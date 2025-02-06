"""A module housing the Sniffer tool for determining the dialect and structure
of a csv file that may contain metadata, header and data sections."""

from collections import Counter
from dataclasses import dataclass
from types import SimpleNamespace
from typing import IO, List, Optional, Tuple
import warnings

import clevercsv
from clevercsv.dialect import SimpleDialect

from tabbed.utils.celltyping import convert
from tabbed.utils.celltyping import is_numeric
from tabbed.utils.mixins import ReprMixin


@dataclass(frozen=True)
class Header:
    """An immutable dataclass representing a text file's header.

    Attributes:
        line:
            The line number of the file this header represents. It may be None
            indicating the header was not derived from the file.
        names:
            The string names of each of the columns comprising the header.
        string:
            The original line string from infile that was split to create names.
            It may be None to indicate the names were not derived from the file.
    """

    line: int | None
    names: List[str]
    string: str | None

    def __post_init__(self) -> None:
        """Replace any ' ' characters in names with underscores."""

        # replace any blank chars with underscores
        names = [name.replace(' ', '_') for name in self.names]
        super().__setattr__('names', names)


@dataclass(frozen=True)
class MetaData:
    """An immutable dataclass representing a text file's metadata section.

    Attributes:
        lines:
            A start, stop tuple of the metadata section from a file instance.
            The start is always 0. May be None to indicate the file does not
            contain a metadata section.
        string:
            The string of metadata with no conversion read from file instance.
            The last element may be None to indicate the file does not contain
            a metadata section.
    """

    lines: Tuple[int, int | None]
    string: str | None


class Sniffer(ReprMixin):
    r"""A tool for inferring the dialect and structure of a CSV file.

    The formatting of CSV files can vary widely. Python's builtin Sniffer is
    capable of handling different dialects (separators, line terminators, quotes
    etc) but assumes the first line within the file is a header or a row of
    unheaded data. In practice, many CSV files contain metadata prior to the
    header or data section. While these files are not compliant with CSV
    standards (https://datatracker.ietf.org/doc/html/rfc4180.html), their broad
    use necessitates file sniffing that infers both dialect and structure. To
    date, some csv readers such as Pandas read_csv allow metadata rows to be
    skipped but no formal mechanism for sniffing dialect, metadata and header
    information exist. This Sniffer supports these operations.

    Attributes:
        infile:
            An open file, and instance of IO.
        line_count:
            The number of lines in infile.
        start:
            The start line of infile for collecting a sample of 'amount' number
            of lines.
        amount:
            The number of infile lines to sample for dialect detection and
            locating header and metadata positions. The initial value defaults
            to the smaller of line_count or 100 lines.
        skips:
            Line numbers to ignore during sample collection.

    Example:
        >>> import tempfile
        >>> delimiter = ';'
        >>> # make a metadata and add to text that will be written to tempfile
        >>> metadata = {'exp': '3', 'name': 'Paul Dirac', 'date': '11/09/1942'}
        >>> text = [delimiter.join([key, val]) for key, val in metadata.items()]
        >>> # make a header and row to skip and add to text
        >>> header = delimiter.join('group count color'.split())
        >>> to_skip = delimiter.join('please ignore this line'.split())
        >>> text.extend([header, to_skip])
        >>> # make some data rows and add to text
        >>> group = 'a c b b c a c b c a a c'.split()
        >>> count = '22 2 13 15 4 19 4 21 5 24 18 1'.split()
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> data = [delimiter.join(row) for row in zip(group, count, color)]
        >>> text.extend(data)
        >>> # create a temp file and dump our text
        >>> outfile = tempfile.TemporaryFile(mode='w+')
        >>> _ = outfile.write('\r\n'.join(text))
        >>> # create a sniffer
        >>> sniffer = Sniffer(outfile)
        >>> # ask sniffer to report number of lines
        >>> sniffer.line_count
        17
        >>> len(text)
        17
        >>> # change the sample amount to 5 lines and skip line 4
        >>> # you would know to do this by inspecting the sample property
        >>> # and seeing the problematic line 4
        >>> sniffer.amount = 5
        >>> sniffer.skips = [4]
        >>> dialect = sniffer.sniff()
        >>> print(dialect)
        SimpleDialect(';', '', '')
        >>> # ask the sniffer to return a Header
        >>> header = sniffer.header()
        >>> print(header)
        ... #doctest: +NORMALIZE_WHITESPACE
        Header(line=3,
        names=['group', 'count', 'color'],
        string='group;count;color')
        >>> # ask sniffer for the metadata given the header
        >>> sniffer.metadata(header)
        ... #doctest: +NORMALIZE_WHITESPACE
        MetaData(lines=(0, 3),
        string='exp;3\nname;Paul Dirac\ndate;11/09/1942')
        >>> # ask for the column types
        >>> sniffer.types()
        [<class 'str'>, <class 'int'>, <class 'str'>]
        >>> # close the temp outfile resource
        >>> outfile.close()
    """

    def __init__(
        self,
        infile: IO[str],
        start: int = 0,
        amount: int = 100,
        skips: Optional[List[int]] = None,
    ) -> None:
        """Initialize this sniffer.

        Args:
            infile:
                A I/O stream instance such as returned by open.
            start:
                The start line of infile for collecting a sample of lines.
            amount:
                The number of infile lines to sample for dialect detection and
                locating header and metadata positions. The initial value defaults
                to the smaller of the infiles length or 100 lines.
            skips:
                Line numbers to ignore during sample collection.

        Notes:
            Sniffer deviates from Python's Sniffer in that infile is strictly an
            IO stream, not a list because detecting the metadata and header
            structures requires movement within the file via 'seek'.
        """

        self.infile = infile
        self._start = min(start, self.line_count - 1)
        self._amount = min(self.line_count - self._start, amount)
        self._skips = skips if skips else []
        self._sample = self._resample()
        # perform initial sniff from initialized sample
        self.dialect = self.sniff()

    @property
    def line_count(self) -> int:
        """Returns the number of lines in this Sniffer's infile."""

        self._move(0)
        result = sum(1 for line in self.infile)
        self._move(0)

        return result

    @property
    def start(self) -> int:
        """Returns the start line of this Sniffer's sample string."""

        return self._start

    @start.setter
    def start(self, value: int) -> None:
        """Sets a start line and updates this Sniffer's sample string.

        Args:
            value:
                A new sample start line.
        """

        self._start = min(self.line_count - 1, value)
        self._sample = self._resample()

    @property
    def amount(self) -> int:
        """Returns the number of joined lines in Sniffer's sample string."""

        return self._amount

    @amount.setter
    def amount(self, value: int) -> None:
        """Sets the number of lines & updates this Sniffer's sample string.

        Args:
            value:
                The new number of lines to join to build the sample string.
        """

        self._amount = min(self.line_count, value)
        self._sample = self._resample()

    @property
    def skips(self) -> List[int]:
        """Returns the skipped lines excluded from this Sniffer's sample string."""

        return self._skips

    @skips.setter
    def skips(self, other: List[int]) -> None:
        """Sets the lines to exclude from this Sniffer's sample string."""

        self._skips = other
        self._sample = self._resample()

    @property
    def sample(self) -> Tuple[str, List[int]]:
        """Returns a sample string and respective line numbers from infile."""

        return self._sample

    def _resample(self) -> Tuple[str, List[int]]:
        """Sample from the infile using the start, amount and skip properties.

        Returns:
            A tuple with the sample string and line numbers of the sample.
        """

        self._move(self.start)
        result = SimpleNamespace(loc=self.start, n=0, lines=[], line_nums=[])
        while result.n < self.amount:

            line = self.infile.readline()
            if result.loc not in self.skips:
                result.lines.append(line)
                result.line_nums.append(result.loc)
                result.n += 1
            result.loc += 1

        # move line pointer back to start of the file
        self._move(0)
        sampled = ''.join(result.lines)
        return sampled, result.line_nums

    def _move(self, line: int) -> None:
        """Moves the line pointer in this file to line number.

        Args:
            line:
                A line number to move to within this Sniffer's infile.

        Returns:
            None but advances the line pointer to line.
        """

        self.infile.seek(0)
        for _ in range(line):
            next(self.infile)

    def sniff(self, delimiters: Optional[str] = None) -> SimpleDialect | None:
        """Returns a clevercsv SimpleDialect from this instances sample.

        Dialect is detected using clevercsv's sniffer as it has shown improved
        dialect detection accuracy over Python's csv sniffer built-in.

        Args:
            delimiters:
                A string of possibly valid delimiters see csv.Sniffer.sniff.

        Returns:
            A SimpleDialect instance (see clevercsv.dialect) or None if sniffing
            is inconclusive.

        References:
            van den Burg, G.J.J., Nazábal, A. & Sutton, C. Wrangling messy CSV
            files by detecting row and type patterns. Data Min Knowl Disc 33,
            1799–1820 (2019). https://doi.org/10.1007/s10618-019-00646-y
        """

        sample_str = self.sample[0]
        result = clevercsv.Sniffer().sniff(sample_str, delimiters=delimiters)
        if not result:
            msg = "Dialect could not be determined from Sniffer's sample"
            warnings.warn(msg)

        # python 3.11 deprecated '' escapechars that clever csv defaults to
        escapechar = result.escapechar
        result.escapechar = None if escapechar == '' else escapechar

        return result

    def rows(self, delimiter: Optional[str] = None) -> List[List[str]]:
        """Transforms a sample string into rows containing string cells.

        This protected method converts the sample string into a list of rows of
        individual string items. As a protected method it is not intended for
        external call and may change in the future.

        Args:
            delimiter:
                An optional delimiter to split each line in sample string. If
                None, the delimiter of the detected dialect will be used.

        Returns:
            A list of list representing each line in sample.

        """

        sample_str, _ = self.sample

        if delimiter is None and self.dialect is None:
            msg = "A delimiter str type must be given if dialect is None."
            raise TypeError(msg)
        # mypy fails to detect that one of these two is not None now
        sep = delimiter if delimiter else self.dialect.delimiter  # type: ignore

        rows = []
        # split sample_str on terminators, strip & split each line on delimiter
        for line in sample_str.splitlines():
            # lines may end in delimiter leading to empty trailing cells
            stripped = line.rstrip(sep)
            row = stripped.split(sep)
            # remove any double quotes
            row = [astring.replace('"', '') for astring in row]
            rows.append(row)

        return rows

    def _nonnumeric(
        self,
        rows: List[List[str]],
        line_nums: List[int],
    ) -> int | None:
        """Locates the largest indexed row containing no numeric strings, no
        empty strings and whose length matches the last row.

        A row containing only strings sitting above rows with numerical types
        is likely a header row. This function finds that row assuming the row is
        full (no empty strings) and is complete (length matches last row).

        Args:
            rows:
                A list of list of representing each file in sample.
            line_nums:
                The line numbers of each list in sample accounting for skip rows.

        Returns:
            An integer line number or None.
        """

        # search rows from bottom to top to get largest indexed row
        for num, row in reversed(list(zip(line_nums, rows))):
            numeric = any(is_numeric(astring) for astring in row)
            full = all(bool(el) for el in row)
            complete = len(row) == len(rows[-1])
            if not numeric and full and complete:
                return num

        return None

    def _disjointed(
        self,
        rows: List[List[str]],
        line_nums: List[int],
    ) -> int | None:
        """Locates the largest indexed row that shares nothing in common with
        all the rows below it.

        Metadata and Header rows likely share no string values in common with
        data rows. This function finds a largest indexed row that is disjoint
        with all the rows below it.

        Args:
            rows:
                A list of list of representing each file in sample.
            line_nums:
                The line numbers of each list in sample accounting for skip rows.

        Returns:
            An integer line number or None.

        """

        reversal = reversed(list(zip(line_nums, rows)))
        # advance iterator to line above last row
        _, last = next(reversal)
        seen = [last]
        for num, row in reversal:
            if all(set(row).isdisjoint(others) for others in seen):
                return num

            seen.append(row)

        return None

    def _mislengthed(
        self,
        rows: List[List[str]],
        line_nums: List[int],
    ) -> int | None:
        """Finds the largest indexed row whose length does not match the length
        of the last row.

        Metadata rows are not required to be the same length as data rows. The
        first row above a data section in the absence of a header whose length
        does not match the last row is likely a metadata row.

        Args:
            rows:
                A list of list of representing each file in sample.
            line_nums:
                The line numbers of each list in sample accounting for skip rows.

        Returns:
            An integer line number or None.
        """

        # search rows from bottom to top to get largest indexed row
        for num, row in reversed(list(zip(line_nums, rows))):
            if len(row) != len(rows[-1]):
                return num

        return None

    def header(self, delimiter: Optional[str] = None) -> Header:
        """Detects the header row (if any) in this Sniffer's sample.

        If no header is detected this method constructs a header. The names in
        this header are of the form; 'Column_1', ... 'Column_n' where n is the
        expected number of columns from the last row if the sample.

        Args:
            delimiter:
                An optional delimiter to split each line in sample string. If
                None, the delimiter of the detected dialect will be used.


        Two methods are used to determine if the rows contain a header.
        1. If the last line of rows (assumed to be a data section row) contains
           a substring representing a numeric, then the first row from the end
           of rows with no numeric string, having no empty strings, and a length
           matching the last row will be taken as the header.
        2. If the last line of rows contains only strings. We look for the
           first row from the end of the rows with no empty strings and
           contains no items in common with all the rows below it.

        Notes:
            Just like all other file sniffers, this heuristic will make
            mistakes.  A judicious sample choice that ignores problematic rows
            via the skip parameter may aide detection.

        Returns:
            A Header dataclass instance.
        """

        sample, line_nums = self.sample

        if delimiter is None and self.dialect is None:
            msg = "A delimiter str type must be given if dialect is None."
            raise TypeError(msg)
        # mypy fails to detect that one of these two is not None now
        sep = delimiter if delimiter else self.dialect.delimiter  # type: ignore

        rows = self.rows(sep)
        if any(is_numeric(astring) for astring in rows[-1]):
            # locate by non-numeric method
            num = self._nonnumeric(rows, line_nums)
        else:
            # locate by disjoint method & assert len to match last row
            num = self._disjointed(rows, line_nums)
            idx = line_nums.index(num) if num else None
            if idx and len(rows[idx]) != len(rows[-1]):
                num = None

        if num is None:
            ncols = len(self.rows()[-1])
            names = [f'Column_{i}' for i in range(ncols)]
            return Header(line=None, names=names, string=None)

        # locate this idx and get corresponding row
        row = rows[line_nums.index(num)]

        # get the original string & return Header
        s = sample.splitlines()[line_nums.index(num)]

        return Header(line=num, names=row, string=s)

    def metadata(
        self,
        header: Header | None,
        delimiter: Optional[str] = None,
    ) -> MetaData:
        """Detects the metadata section (if any) in this Sniffer's sample.

        Args:
            header:
                A Header dataclass instance.
            delimiter:
                An optional delimiter to split each line in sample string. If
                None, the delimiter of the detected dialect will be used.

        Notes:
            The detection of the metadata section when no header is present
            follows this heuristic:
            1. If last sample row strings all represent numerics, locate the row
               closest to the last row that has non numeric strings or
               a different length whichever occurs closest to last row.
            2. If the last row contains at least one string representing
               a numeric, look for the row closest to the last row that has
               a different length, is disjointed or non-numeric taking the
               closest to the last row if these rows differ.
            3. If the last sample contains no strings representing numerics,
               take the row closest to the last row that is disjointed with all
               rows below or has a different from last row. If these differ take
               the one closest to last row.

            This heuristic will make mistakes, A judicious choice for the sample
            and skips may improve detection.

        Returns:
            A MetaData dataclass instance or None.
        """

        sample, line_nums = self.sample

        if delimiter is None and self.dialect is None:
            msg = "A delimiter str type must be given if dialect is None."
            raise TypeError(msg)
        # mypy fails to detect that one of these two is not None now
        sep = delimiter if delimiter else self.dialect.delimiter  # type: ignore

        # get rows upto header line if given
        rows = self.rows(sep)
        if header and header.line:
            idx = line_nums.index(header.line)
            s = '\n'.join(sample.splitlines()[0:idx])
            return MetaData((0, header.line), s)

        mislengthed = self._mislengthed(rows, line_nums)
        disjointed = self._disjointed(rows, line_nums)
        nonnumeric = self._nonnumeric(rows, line_nums)

        line_num = None
        if all(is_numeric(astring) for astring in rows[-1]):

            # if all data is numeric find lowest of nonnumeric and mislengthed
            nums = [x for x in [mislengthed, nonnumeric] if x]
            line_num = max(nums) if nums else None

        if any(is_numeric(astring) for astring in rows[-1]):

            # if any but not all numeric in data find lowest for all rows
            nums = [x for x in (mislengthed, disjointed, nonnumeric) if x]
            line_num = max(nums) if nums else None

        else:
            # all strings- look for lowest row that's disjoint or mislen
            nums = [x for x in (mislengthed, disjointed) if x]
            line_num = max(nums) if nums else None

        if line_num is None:
            return MetaData((0, None), None)

        # get index, original string & return Header
        idx = line_nums.index(line_num)
        s = sample.splitlines()[idx + 1]

        return MetaData((0, line_num), s)

    def types(
        self,
        count: int = 5,
        delimiter: Optional[str] = None,
    ) -> List[str]:
        """Infer the column types from the last rows of sniffed sample.

        Args:
            count:
                The number of lines at the end of sniffed sample to poll for
                type. Defaults to the last 5 rows of sample.
            delimiter:
                An optional delimiter to override the sniffed dialect delimiter.

        Returns:
            A list of type names. The length of the list matches the length of
            the last row in the sample.
        """

        sep = delimiter if delimiter else self.dialect.delimiter  # type: ignore
        rows = self.rows(sep)[-count:]
        counters: List[Counter] = [Counter() for astring in rows[-1]]
        for row in rows:
            for counter, astring in zip(counters, row):
                counter.update([type(convert(astring))])

        common = [counter.most_common(1)[0] for counter in counters]
        return [typed for typed, cnt in common]


if __name__ == '__main__':

    import doctest

    doctest.testmod()
