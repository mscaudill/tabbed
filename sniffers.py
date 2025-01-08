""" """

import itertools
from collections import Counter
from types import SimpleNamespace
from typing import IO, List, Tuple

import clevercsv
from clevercsv.dialect import SimpleDialect


class MetaSniffer:
    """A tool for inferring the format and structure of a CSV file.

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

    """

    def __init__(self, infile: IO[str]) -> None:
        """Initialize this sniffer.

        Args:
            infile:
                A file-like I/O stream instance such as returned by open.
        """

        self.infile = infile


    @property
    def count(self) -> int:
        """Returns the numer of lines in this Sniffer's infile."""

        result = sum(1 for line in infile)
        self._move(0)

        return result


    def _move(self, line: int) -> None:
        """Moves the line pointer in this file to line number.

        Args:
            line:
                A line number to move to within this Sniffer's infile.
        """

        self.infile.seek(0)
        for _ in range(line):
            next(infile)


    def sample(
        self,
        count: int,
        start: int,
        skips: List[int],
    ) -> Tuple[str, List[int]]:
        """Returns a string of count joint lines & line indices from this
        Sniffer's infile.

        Args:
            count:
                The number of lines used to build the string sample.
            start:
                The start line of the file to begin sample collection.
            skips:
                Line numbers to ignore during sample collection.

        Returns:
            A tuple containing the sample string and the line indices used to
            make the sample. We refer to this tuple as a sampling.
        """

        cnt = min(self.count - start, count)

        self._move(start)
        result = SimpleNamespace(loc=start, n=0, lines=[], indices=[])
        while result.n < cnt:

            line = infile.readline()
            if result.loc not in skips:
                result.lines.append(line)
                result.indices.append(result.loc)
                result.n += 1
            result.loc += 1

        # move line pointer back to start of the file
        self._move(0)
        sample_str = ''.join(result.lines)
        return sample_str, result.indices


    def dialect(self, sample: str, delimiters: str = None) -> SimpleDialect:
        """Returns a clevercsv SimpleDialect from the sniffed sample.

        Args:
            sample:
                A string consisting of joined lines from the file.
            delimiters:
                A string of possibly valid delimiters see csv.Sniffer.sniff.

        Returns:
            A SimpleDialect instance (see clevercsv.dialect)
        """

        return clevercsv.Sniffer().sniff(sample, delimiters=delimiters)


    def has_numeric(self, line) -> bool:
        """Returns True if any item in line is numeric.

        Args:
            line:
                A list of strings representing a single row in Sniffer's infile.

        Returns:
            True if line has stringed numeric value and False otherwise.
        """

        for item in line:
            try:
                complex(item)
                return True
            except (ValueError, OverflowError):
                continue
        else:
            return False


    def header(
        self,
        sampling: (str, List[int]),
        dialect: SimpleDialect,
    ) -> int | None:
        """Determines if this Sniffer's infile contains a header section.

        Args:
            sampling:
                A tuple of joined strings from this infile and the corresponding
                line indices.
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
        Just like all other file sniffers, this heuristic will make mistakes.
        A judicious sample choice that ignores problematic rows via the skip
        parameter may aide detection.

        Returns:
            The integer row index of the header if one exist or None.
        """

        sample, indices = sampling
        # split samples into lines, strip any trailing delimiters and split line
        lines = []
        for line in sample.splitlines():
            stripped = line.rstrip(dialect.delimiter)
            lines.append(stripped.split(dialect.delimiter))

        result = None
        if self.has_numeric(lines[-1]):

            # get first line from end that is all non-numeric and full
            for idx, line in reversed(list(zip(indices, lines))):

                has_numeric = self.has_numeric(line)
                is_full = all([True if item else False for item in line])

                if not has_numeric and is_full:
                    result = idx
                    break

        else:
            # from next to last find first that is disjoint with all below & full
            riterator = reversed(list(enumerate(lines)))
            next(riterator)
            for idx, line in riterator:

                disjoint = all([set(line).isdisjoint(o) for o in lines[idx+1:]])
                is_full = all([True if item else False for item in line])

                if disjoint and is_full:
                    result = indices[idx]
                    break

        return result


    def metadata(
        self,
        sampling: (str, List[int]),
        header: int | None,
        dialect: SimpleDialect,
    ) -> int | None:
        """Returns the stop index of the metadata section.

        Args:
            sampling:
                A tuple of joined strings from this infile and the corresponding
                line indices.
            header:
                The header index if it exist or None. Method header must
                therefore be called prior to metadata call.
            dialect:
                A clevercsv SimpleDialect instance.

        Returns:
            The stop index (inclusive) of the metadata section or None.
        """

        metadata = None
        if header is not None:
            return header - 1

        sample, indices = sampling
        # split samples into lines, strip any trailing delimiters and split line
        lines = []
        for line in sample.splitlines():
            stripped = line.rstrip(dialect.delimiter)
            lines.append(stripped.split(dialect.delimiter))

        # from next to last find first that is disjoint with all below & full
        riterator = reversed(list(enumerate(lines)))
        next(riterator)
        for idx, line in riterator:

            disjoint = all([set(line).isdisjoint(o) for o in lines[idx+1:]])
            is_full = all([True if item else False for item in line])

            if disjoint and is_full:
                metadata = indices[max(idx-1, 0)]
                break

        return metadata






if __name__ == '__main__':

    fp1 = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'
    with open(fp1, 'r') as infile:
        sniffer1 = MetaSniffer(infile)
        sample1, indices1 = sniffer1.sample(count=100, start=0, skips=[35])
        cleverdialect1 = clevercsv.Sniffer().sniff(sample1)
        header1 = sniffer1.header((sample1, indices1), cleverdialect1)
        meta1 = sniffer1.metadata((sample1, indices1), header1, cleverdialect1)


    fp2 = '/home/matt/python/nri/tabbed/__data__/mouse_annotations.txt'
    with open(fp2, 'r') as infile:
        sniffer2 = MetaSniffer(infile)
        sample2, indices2 = sniffer2.sample(count=100, start=0, skips=[])
        cleverdialect2 = clevercsv.Sniffer().sniff(sample2)
        header2 = sniffer2.header((sample2, indices2), cleverdialect2)
        meta2 = sniffer1.metadata((sample2, indices2), None, cleverdialect2)

    fp3 = '/home/matt/python/nri/tabbed/__data__/mouse_behavior.txt'
    with open(fp3, 'r') as infile:
        sniffer3 = MetaSniffer(infile)
        sample3, indices3 = sniffer3.sample(count=100, start=0, skips=[])
        cleverdialect3 = clevercsv.Sniffer().sniff(sample3)
        header3 = sniffer3.header((sample3, indices3), cleverdialect3)
        meta3 = sniffer3.metadata((sample3, indices3), None, cleverdialect3)

