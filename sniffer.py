"""A module housing the Sniffer tool for determining the dialect and structure
of a csv file that may contain metadata, header and data sections."""

from types import SimpleNamespace
from typing import IO, List, Optional, Tuple
import warnings

import clevercsv
from clevercsv.dialect import SimpleDialect

from tabbed.utils.celltyping import is_numeric
from tabbed.utils.mixins import ReprMixin


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
        >>> # ask the sniffer to return the header row index
        >>> head_pos = sniffer.has_header()
        >>> head_pos
        3
        >>> # ask sniffer for the inclusive stop row index of metadata
        >>> sniffer.has_meta(head_pos)
        2
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
                The start line of infile for collecting a sample of 'amount' number
                of lines.
            amount:
                The number of infile lines to sample for dialect detection and
                locating header and metadata positions. The initial value defaults
                to the smaller of line_count or 100 lines.
            skips:
                Line numbers to ignore during sample collection.

        Notes:
            Sniffer deviates from Python's Sniffer in that infile is strictly an
            IO stream, not a list. File section detection requires the 'seek'
            method of IO streams.
        """

        self.infile = infile
        self._start = min(start, self.line_count - 1)
        self._amount = min(self.line_count - self._start, amount)
        self._skips = skips if skips else []
        self._sample = self._resample()
        self.dialect = self.sniff()

    @property
    def line_count(self) -> int:
        """Returns the number of lines in this Sniffer's infile."""

        self._move(0)
        result = sum(1 for line in self.infile)

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
        """Returns a sample string, the joining of lines read from infile and
        the indices of the lines that were joined."""

        return self._sample

    def _resample(self) -> Tuple[str, List[int]]:
        """Returns a tuple, a string of lines & their respective
        indices from infile.

        Returns:
            A tuple containing the sample string and the line indices used to
            make the sample.
        """

        self._move(self.start)
        result = SimpleNamespace(loc=self.start, n=0, lines=[], indices=[])
        while result.n < self.amount:

            line = self.infile.readline()
            if result.loc not in self.skips:
                result.lines.append(line)
                result.indices.append(result.loc)
                result.n += 1
            result.loc += 1

        # move line pointer back to start of the file
        self._move(0)
        sampled = ''.join(result.lines)
        return sampled, result.indices

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

        return result

    def _any_numeric(self, row) -> bool:
        """Returns True if any string element in row is numeric.

        This protected method is not intended for external call.

        Args:
            row:
                A list of strings made from splitting a single line in infile on
                the detected delimiter.

        Returns:
            True if row has stringed numeric value and False otherwise.
        """

        for astring in row:
            if is_numeric(astring):
                return True

        return False

    def rows(self, delimiter: Optional[str] = None) -> List[List[str]]:
        """Transforms a sampling into a list of rows containing string cells.

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
            rows.append(stripped.split(sep))

        return rows

    def header(self, delimiter: Optional[str] = None) -> int | None:
        """Determines if this Sniffer's infile contains a header row.

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
            The integer row index of the detected header or None.
        """

        indices = self.sample[1]

        if delimiter is None and self.dialect is None:
            msg = "A delimiter str type must be given if dialect is None."
            raise TypeError(msg)
        # mypy fails to detect that one of these two is not None now
        sep = delimiter if delimiter else self.dialect.delimiter  # type: ignore

        rows = self.rows(sep)
        index = None
        # Method1: numeric data, look for 1st non-numeric, full, & complete
        if self._any_numeric(rows[-1]):
            for idx, row in reversed(list(zip(indices, rows))):

                has_numeric = self._any_numeric(row)
                is_full = all(bool(item) for item in row)
                complete = len(row) == len(rows[-1])

                if not has_numeric and is_full and complete:
                    index = idx
                    break

        else:
            # Method2: non-numeric data, look for 1st disjoint, full & complete
            riterator = reversed(list(enumerate(rows)))
            last = next(riterator)  # start with next to last row
            for idx, row in riterator:

                disjoint = all(set(row).isdisjoint(o) for o in rows[idx + 1 :])
                is_full = all(bool(item) for item in row)
                complete = len(row) == len(last)

                if disjoint and is_full and complete:
                    index = indices[idx]
                    break

        # TODO this should be optional
        if index is not None:
            row = rows[index]
            result = [astring.replace('"','') for astring in row]
        else:
            result = None

        return result, index

    def meta(
        self,
        header: int | None,
        delimiter: Optional[str] = None,
    ) -> int | None:
        """Returns the stop index of the metadata section.

        Args:
            header:
                The index of the header row or None with None signifying the
                infile contains no header row.
            delimiter:
                An optional delimiter to split each line in sample string. If
                None, the delimiter of the detected dialect will be used.

        Notes:
            The metadata section is found similarly to the header section except
            we do not require the first disjoint or non-numeric row to be
            complete.

        Returns:
            The stop index (inclusive) of the metadata section or None.
        """


        indices = self.sample[1]

        if delimiter is None and self.dialect is None:
            msg = "A delimiter str type must be given if dialect is None."
            raise TypeError(msg)
        # mypy fails to detect that one of these two is not None now
        sep = delimiter if delimiter else self.dialect.delimiter  # type: ignore

        rows = self.rows(sep)
        if header is not None:
            return rows[:header]

        index = None
        # Method 1: numerical data, look for first non-numerical & full row
        if self._any_numeric(rows[-1]):
            for idx, row in reversed(list(zip(indices, rows))):

                has_numeric = self._any_numeric(row)
                is_full = all(bool(item) for item in row)

                if not has_numeric and is_full:
                    index = idx
                    break

        else:
            # Method 2: non-numerical data, look for first disjoint & full row
            riterator = reversed(list(enumerate(rows)))
            next(riterator)  # start with next to last row
            for idx, row in riterator:

                disjoint = all(set(row).isdisjoint(o) for o in rows[idx + 1 :])
                is_full = all(bool(item) for item in row)

                if disjoint and is_full:
                    index = indices[max(idx, 0)]
                    break

        if index:
            result = rows[:index], (0, index)
        else:
            result = None, None
        return result


if __name__ == '__main__':

    """
    import doctest

    doctest.testmod()
    """

    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'
    with open(fp, 'r') as infile:
        sniffer = Sniffer(infile)
        sniffer.start=0
        sniffer.skips = []
        header0 = sniffer.header()
        sniffer.skips = [35]
        header1 = sniffer.header()
        meta1 = sniffer.meta(header1[1])
