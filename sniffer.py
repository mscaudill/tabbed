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
        count:
            The number of lines in infile.

    Example:
        >>> import tempfile
        >>> delimiter = ';'
        >>> # make a metadata and add to text that will be written to tempfile
        >>> metadata = {'exp': '3', 'name': 'Paul Dirac', 'date': '11/09/1942'}
        >>> text = [delimiter.join([key, val]) for key, val in metadata.items()]
        >>> # make a header and row to skip and add to text
        >>> header = delimiter.join('group count color temp'.split())
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
        >>> sniffer.count
        17
        >>> len(text)
        17
        >>> # make a sample and ask sniffer for the dialect
        >>> # note the skip over the to_skip line
        >>> sampling = sniffer.sample(count=5, start=0, skips=[4])
        >>> dialect = sniffer.sniff(sampling)
        >>> print(dialect)
        SimpleDialect(';', '', '')
        >>> # ask the sniffer to return the header row index
        >>> heading = sniffer.has_header(sampling, dialect)
        >>> heading
        3
        >>> # ask sniffer for the inclusive stop row index of metadata
        >>> sniffer.has_meta(sampling, heading, dialect)
        2
        >>> # close the temp outfile resource
        >>> outfile.close()
    """

    def __init__(self, infile: IO[str]) -> None:
        """Initialize this sniffer.

        Args:
             infile:
                A I/O stream instance such as returned by open.

        Notes:
            Sniffer deviates from Python's Sniffer in that infile is strictly an
            IO stream, not a list. File section detection requires the 'seek'
            method of IO streams.
        """

        self.infile = infile

    @property
    def count(self) -> int:
        """Returns the number of lines in this Sniffer's infile."""

        self._move(0)
        result = sum(1 for line in self.infile)

        return result

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

    def sample(
        self,
        count: int,
        start: int,
        skips: List[int],
    ) -> Tuple[str, List[int]]:
        """Returns a sampling tuple, a string of lines & their respective
        indices from infile.

        Args:
            count:
                The number of lines used to build the string sample.
            start:
                The start line of the file to begin sample collection.
            skips:
                Line numbers to ignore during sample collection.

        Returns:
            A tuple containing the sample string and the line indices used to
            make the sample.
        """

        cnt = min(self.count - start, count)

        self._move(start)
        result = SimpleNamespace(loc=start, n=0, lines=[], indices=[])
        while result.n < cnt:

            line = self.infile.readline()
            if result.loc not in skips:
                result.lines.append(line)
                result.indices.append(result.loc)
                result.n += 1
            result.loc += 1

        # move line pointer back to start of the file
        self._move(0)
        sampled = ''.join(result.lines)
        return sampled, result.indices

    def sniff(
        self,
        sampling: Tuple[str, List[int]],
        delimiters: Optional[str] = None,
    ) -> SimpleDialect | None:
        """Returns a clevercsv SimpleDialect from a sample of lines.

        Dialect is detected using clevercsv's sniffer as it has shown improved
        dialect detection accuracy over Python's csv sniffer built-in.

        Args:
            sampling:
                A 2-tuple, a string of lines and their indices returned by this
                instances sample method.
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

        result = clevercsv.Sniffer().sniff(sampling[0], delimiters=delimiters)
        if not result:
            msg = 'Dialect could not be determined from sample'
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

    def _as_rows(
        self,
        sampling: Tuple[str, List[int]],
        dialect: SimpleDialect,
    ) -> List[List[str]]:
        """Transforms a sampling into a list of rows containing string cells.

        A sample consist of count lines of data as a single string. This
        protected method converts the sample into a list of rows of individual
        string items. As a protected method it is not intended for external call
        and may change in the future.

        Args:
           sampling:
                A 2-tuple, a string of lines and their indices returned by this
                instance's sample method.
            dialect:
                A clevercsv SimpleDialect instance.

        Returns:
            A list of rows, a list representation of each line in sampling.
        """

        sample, _ = sampling
        rows = []
        # split sample on terminators, strip then split each line on delimiter
        for line in sample.splitlines():
            # lines may end in delimiter leading to empty trailing cells
            stripped = line.rstrip(dialect.delimiter)
            rows.append(stripped.split(dialect.delimiter))

        return rows

    def has_header(
        self,
        sampling: Tuple[str, List[int]],
        dialect: SimpleDialect,
    ) -> int | None:
        """Determines if this Sniffer's infile contains a header row.

        Args:
            sampling:
                A 2-tuple, a string of lines and their indices returned by this
                instance's sample method.
            dialect:
                A clevercsv SimpleDialect instance.

        Two methods are used to determine if the sample contains a header:
        1. If the last line of the sample (assumed to be a data section row)
           contains a string representing a numeric, then the first row from
           the end of the sample that does not have a string representing
           a numeric and has no empty strings is taken as the header.
        2. If the last line of the sample contains only strings. We look for
           the first row from the end of the sample with no empty strings
           and contains no items in common with all the rows below it.

        Notes:
            Just like all other file sniffers, this heuristic will make
            mistakes.  A judicious sample choice that ignores problematic rows
            via the skip parameter may aide detection.

        Returns:
            The integer row index of the detected header or None.
        """

        indices = sampling[1]
        rows = self._as_rows(sampling, dialect)

        result = None
        # Method 1: numerical data, look for first non-numerical & full row
        if self._any_numeric(rows[-1]):

            for idx, row in reversed(list(zip(indices, rows))):

                has_numeric = self._any_numeric(row)
                is_full = all(bool(item) for item in row)

                if not has_numeric and is_full:
                    result = idx
                    break

        else:
            # Method 2: non-numerical data, look for first disjoint & full row
            riterator = reversed(list(enumerate(rows)))
            next(riterator)  # start with next to last row
            for idx, row in riterator:

                disjoint = all(set(row).isdisjoint(o) for o in rows[idx + 1 :])
                is_full = all(bool(item) for item in row)

                if disjoint and is_full:
                    result = indices[idx]
                    break

        return result

    def has_meta(
        self,
        sampling: Tuple[str, List[int]],
        header: int | None,
        dialect: SimpleDialect,
    ) -> int | None:
        """Returns the stop index of the metadata section.

        Args:
            sampling:
                A 2-tuple, a string of lines and their indices returned by this
                instance's sample method.
            header:
                The index of the header row or None with None signifying the
                infile contains no header row.
            dialect:
                A clevercsv SimpleDialect instance.

        Returns:
            The stop index (inclusive) of the metadata section or None.
        """

        metadata = None
        if header is not None:
            return header - 1 if header > 0 else None

        indices = sampling[1]
        rows = self._as_rows(sampling, dialect)

        # look for 1st disjoint & full row starting from next to last row
        riterator = reversed(list(enumerate(rows)))
        next(riterator)
        for idx, row in riterator:

            disjoint = all(set(row).isdisjoint(o) for o in rows[idx + 1 :])
            is_full = all(bool(item) for item in row)

            if disjoint and is_full:
                metadata = indices[max(idx - 1, 0)]
                break

        return metadata


if __name__ == '__main__':

    import doctest

    doctest.testmod()
