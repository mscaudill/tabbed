"""A reader of text delimited files that supports the following features:

- Identification of metadata & header file sections.
- Automated type conversion to ints, floats, complex numbers,
  times, dates and datetime instances.
- Selective reading of rows and columns satisfying equality,
  membership, regular expression, and rich comparison conditions.
- Iterative reading of rows from the input file.
"""

import csv
import itertools
import re
import warnings
from collections import deque
from types import SimpleNamespace
from typing import (
    IO,
    Callable,
    Deque,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
)

from clevercsv.dialect import SimpleDialect

from tabbed import tabbing
from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.tabbing import Tabulator
from tabbed.utils import parsing
from tabbed.utils.mixins import ReprMixin
from tabbed.utils.parsing import CellType


class Reader(ReprMixin):
    r"""An iterative reader of irregular text files supporting selective
    value-based reading of rows and columns.

    A common variant to the RFC-4180 CSV standard includes metadata prior to
    a possible header and data section. This reader sniffs files for these
    sections advancing to the most-likely start position of the data.
    Additionally, it uses type inference to automatically convert data cells
    into strings, integers, floats, complex, time, date or datetime instances.
    Finally, this reader supports selective reading of rows using equality,
    membership, comparison, & regular expression value-based conditions supplied
    as keyword arguments to the 'tab' method.

    Attributes:
        infile:
            An I/O stream instance returned by open.
        tabulator:
            A callable container of Tab instances; callables that will filter
            rows based on equality, membership, rich comparison and regular
            expression conditions.
        errors:
            A container of casting and ragged length errors detected during
            reading.

    Examples:
        >>> # Create a temporary file for reading
        >>> import os
        >>> import tempfile
        >>> import random
        >>> from datetime import datetime, timedelta
        >>> # make metadata that spans several lines
        >>> metadata_string = ('Experiment, 3\n'
        ... 'Name, Ernst Rutherford\n'
        ... 'location, Cavendish Labs\n'
        ... 'Time, 11:03:29.092\n'
        ... 'Date, 8/23/1917\n'
        ... '\n')
        >>> # make a header of 5 columns
        >>> header = ['group', 'count', 'color', 'time', 'area']
        >>> header_string = ','.join(header) + '\n'
        >>> # make a reproducible data section with 20 rows
        >>> random.seed(0)
        >>> groups = random.choices(['a', 'b', 'c'], k=20)
        >>> counts = [str(random.randint(0, 10)) for _ in range(20)]
        >>> colors = random.choices(['red', 'green', 'blue'], k=20)
        >>> start = datetime(1917, 8, 23, 11, 3, 29, 9209)
        >>> times = [str(start + timedelta(seconds=10*i)) for i in range(20)]
        >>> areas = [str(random.uniform(0, 10)) for _ in range(20)]
        >>> x = [','.join(row) for row in zip(
        ...    groups, counts, colors, times, areas)]
        >>> data_string = '\r\n'.join(x)
        >>> # write the metadata, header and data strings
        >>> fp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        >>> _ = fp.write(metadata_string)
        >>> _ = fp.write(header_string)
        >>> _ = fp.write(data_string)
        >>> fp.close()
        >>> # open the file for reading
        >>> infile = open(fp.name, mode='r')
        >>> reader = Reader(infile)
        >>> # ask the reader for the header
        >>> reader.header
        ... # doctest: +NORMALIZE_WHITESPACE
        Header(line=6,
        names=['group', 'count', 'color', 'time', 'area'],
        string='group,count,color,time,area')
        >>> # read group, count & area columns where group is a or c & 0 < area <=4
        >>> # by passing keyword args to this reader's 'tab' method
        >>> reader.tab(columns=['group', 'count', 'area'],
        ... group=['a', 'c'],
        ... area='> 0 and <= 4')
        >>> # read the data with a chunksize of 3 rows
        >>> rows = reader.read(chunksize=3)
        >>> type(rows) # rows are of type generator yielding 3 rows at a time
        <class 'generator'>
        >>> for idx, chunk in enumerate(rows):
        ...     print(f'Index = {idx}\n{chunk}')
        ...     # doctest: +NORMALIZE_WHITESPACE
        Index = 0
        [{'group': 'c', 'count': 4, 'area': 3.2005460467254574},
        {'group': 'a', 'count': 10, 'area': 1.0905784593110368},
        {'group': 'c', 'count': 7, 'area': 2.90329502402758}]
        Index = 1
        [{'group': 'c', 'count': 8, 'area': 1.8939132855435614},
        {'group': 'c', 'count': 4, 'area': 1.867295282555551}]
        >>> # close reader since it was not opened with context manager
        >>> reader.close()
        >>> os.remove(fp.name) # explicitly remove the tempfile
    """

    # no mutation of exclude parameter
    # pylint: disable-next=dangerous-default-value
    def __init__(
        self,
        infile: IO[str],
        poll: int = 20,
        exclude: List[str] = ['', ' ', '-', 'nan', 'NaN', 'NAN'],
        **sniffing_kwargs,
    ) -> None:
        """Initialize this Reader.

        Args:
            infile:
                An IO stream instance returned by open builtin.
            poll:
                The number of last sample rows to use for the Sniffer to detect
                header, metadata and data types.
            exclude:
               A sequence of characters indicating missing values in the file.
               Rows containing these values will be disqualified from use for
               header, metadata and data type detection. However, this Reader's
               read method will still read and return rows with this exclusion
               values.
            sniffing_kwargs:
                Any valid kwarg for a tabbed Sniffer instance including: start,
                amount, skips and delimiters. Please see Sniffer initializer.

        Notes:
            During initialization, this reader will use the poll and exclude
            arguments to make an initial guess of the header. If this guess is
            wrong, the header may be explicitly set via the 'header' setter
            property.
        """

        self.infile = infile
        self._sniffer = Sniffer(infile, **sniffing_kwargs)
        self.poll = poll
        self.exclude = exclude
        self._header = self._sniffer.header(self.poll, self.exclude)
        self.tabulator = Tabulator(self.header, columns=None, tabs=None)
        self.errors = SimpleNamespace(casting=[], ragged=[])

    @property
    def sniffer(self) -> Sniffer:
        """Returns this Reader's sniffer instance.

        Any time the sniffer is accessed we reset this reader's header and
        tabulator if the header is built by the sniffer.
        """

        if self._header.line is not None:
            # print('Resniffing Header and resetting metadata and Tabulator')
            self._header = self._sniffer.header(self.poll, self.exclude)
            self.tabulator = Tabulator(self.header, columns=None, tabs=None)

        return self._sniffer

    @property
    def header(self) -> Header:
        """Fetches this Reader's current header."""

        return self._header

    @header.setter
    def header(self, value: int | List[str] | Dict) -> None:
        """Sets this Reader's header and resets the metadata and Tabulator.

        Args:
            value:
                An infile line number, list of string names, or dict of keyword
                arguments for sniffer's header method. If value is type int, the
                header will be set to the split string values of the value row
                of infile. If value is type List, the header will be set to the
                string names in value. If value is type dict, the header will be
                resniffed by sniffer's header method using value keyword args.
                Valid keyword arguments are: 'poll', and 'exclude'. Please type
                help(reader.sniffer.header) for more argument details.

        Returns:
            None

        Raises:
            A ValueError is issued if value is int or List type and the length
            of the proposed header names does not match the length of the last
            sample row in the sniffer.
        """

        # get the expected length of the header from the last sample row.
        expected = len(self._sniffer.rows[-1])

        if isinstance(value, int):
            sniff = Sniffer(self.infile, start=value, amount=1)
            if len(sniff.rows[0]) != expected:
                msg = (
                    f'Length of row at index = {value} does not match'
                    f'length of last sample row = {expected}'
                )
                raise ValueError(msg)
            result = Header(value, sniff.rows[0], sniff.sample)

        elif isinstance(value, list):
            if len(value) != expected:
                msg = (
                    f'Length of provided header names = {len(value)} does '
                    f'not match length of last sample row = {expected}'
                )
                raise ValueError(msg)
            result = Header(None, value, None)

        elif isinstance(value, dict):
            result = self._sniffer.header(**value)

        else:
            msg = (
                "A header may be set by integer line number, list of "
                "header names or a dict of kwargs for sniffer's header "
                f"method but not type {type(value)}."
            )
            raise ValueError(msg)

        # set header
        self._header = result
        # determine if reader has previously set tabulator and warn
        previous = self.tabulator
        tblr = Tabulator(self.header, tabs=None, columns=None)
        if tblr.columns != previous.columns or tblr.tabs != previous.tabs:
            msg = (
                "Previously set tabs have been reset. Please call 'tab' "
                "method again before reading."
            )
            print(msg)

        self.tabulator = tblr

    def metadata(self) -> MetaData:
        """Returns this Reader's current metadata.

        Returns:
            A sniffed metadata instance.
        """

        return self._sniffer.metadata(self.header, self.poll, self.exclude)

    def tab(
        self,
        columns: Optional[List[str] | List[int] | re.Pattern] = None,
        **tabs: (
            CellType
            | Sequence[CellType]
            | re.Pattern
            | Callable[[Dict[str, CellType], str], bool]
        ),
    ) -> None:
        """Set the Tabulator instance that will filter infile's rows & columns.

        A tabulator is a container of tab instances that when called on a row,
        sequentially applies each tab to that row. Additionally after applying
        the row tabs it filters the result by columns. Implementation details
        may be found in the tabbed.tabs module.

        Args:
            columns:
                Columns in each row to return during reading as a list of string
                names, a list of column indices or a compiled regular expression
                pattern to match against header names. If None, all the columns
                in the header will be read during a read call.
            tabs:
                name = value keyword argument pairs where name is a valid header
                column name and value may be of type string, int, float,
                complex, time, date, datetime, regular expression or callable.

                - If a string type with rich comparison(s) is provided,
                  a comparison tab is constructed.
                - If a string, int, float, complex, time, date  or datetime is
                  provided, an equality tab is constructed.
                - If a sequence is provided, a membership tab is constructed.
                - If a compiled re pattern, a Regex tab is constructed. See
                  class docs for example.

        Returns:
            None
        """

        self.tabulator = tabbing.Tabulator.from_keywords(
            self.header, columns, **tabs
        )

    def _log_ragged(self, line, row, raise_error):
        """Error logs rows whose length is unexpected.

        When python's csv DictReader encounters a row with more cells than
        header columns, it stores the additional cells to a list under the None
        key.  When the csv DictReader encounters a row that with fewer cells
        than header columns it inserts None values into the missing cells. This
        function detects rows with None keys or None values and logs the row
        number to the error log.

        Args:
            line:
                The line number of the row being tested.
            row:
                A row dictionary of header names and casted values.
            raise_error:
                A boolean indicating if ragged should raise an error and stop
                the reading of the file if a ragged row is encountered.

        Returns:
            The row with None restkey popped
        """

        remainder = row.pop(None, None)
        none_vals = None in row.values()

        if remainder is not None or none_vals:
            msg = f'Unexpected line length on row {line}'
            if raise_error:
                raise csv.Error(msg)
            self.errors.ragged.append(msg)

        return row

    def _prime(
        self,
        start: Optional[int] = None,
        indices: Optional[Sequence] = None,
    ) -> Tuple[Iterator, int]:
        """Prime this Reader for reading by constructing a row iterator.

        Args:
            start:
                An integer line number from the start of the file to begin
                reading data. If None and this reader's header has a line
                number, the line following the header line is the start. If None
                and the header line is None, the line following the metadata
                section is the start. If None and the file has no header or
                metadata, start is 0. If indices are provided, this argument is
                ignored.
            indices:
                An optional Sequence of line numbers to read rows relative to
                the start of the file. If None, all rows from start not in skips
                will be read. If reading a slice of the file, a range instance
                will have improved performance over list or tuple sequence
                types.

        Notes:
            A warning is issued if the start or index start is less than the
            detected start of the datasection.

        Returns:
            A row iterator & row index the iterator starts from.
        """

        # locate the start of the datasection
        autostart = 0
        if self.header.line is not None:
            autostart = self.header.line + 1
        else:
            metalines = self._sniffer.metadata(
                None, self.poll, self.exclude
            ).lines
            autostart = metalines[1] + 1 if metalines[1] else metalines[0]

        astart = start if start is not None else autostart
        stop = None
        step = None

        # indices if provided override start, stop and step
        if indices:

            if isinstance(indices, range):
                astart, stop, step = indices.start, indices.stop, indices.step

            elif isinstance(indices, Sequence):
                astart, stop = indices[0], indices[-1]

            else:
                msg = f'indices must be a Sequence type not {type(indices)}.'
                raise TypeError(msg)

        # warn if start is < computed autostart
        if astart < autostart:
            msg = f'start = {start} is < than detected data start = {autostart}'
            warnings.warn(msg)

        # advance reader's infile to account for blank metalines & get dialect
        self.infile.seek(0)

        # check that we have a valid simple dialect & convert it
        if not self._sniffer.dialect:
            msg = (
                "Sniffer failed to detect dialect. Please set sniffer's"
                "dialect attribute before calling read"
            )
            raise csv.Error(msg)
        assert isinstance(self._sniffer.dialect, SimpleDialect)
        dialect = self._sniffer.dialect.to_csv_dialect()

        # pylint: disable-next=expression-not-assigned
        [next(self.infile) for _ in range(astart)]
        row_iter = csv.DictReader(
            self.infile,
            self.header.names,
            dialect=dialect,
        )

        stop = stop - astart if stop else None
        return itertools.islice(row_iter, 0, stop, step), astart

    # read method needs provide reasonable options for args
    # pylint: disable-next=too-many-positional-arguments
    def read(
        self,
        start: Optional[int] = None,
        skips: Optional[Sequence[int]] = None,
        indices: Optional[Sequence] = None,
        chunksize: int = int(2e5),
        skip_empty: bool = True,
        raise_ragged: bool = False,
    ) -> Iterator[List[Dict[str, CellType]]]:
        """Iteratively read dictionary rows that satisfy this Reader's tabs.

        Args:
            start:
                A line number from the start of the file to begin reading data
                from. If None and this reader's header has a line number, the
                line following the header is the start. If None and the header
                line number is None, the line following the last line in the
                metadata is the start. If None and there is no header or
                metadata, the start line is 0.
            skips:
                A sequence of line numbers to skip during reading.
            indices:
                A sequence of line numbers to read rows from. If None. all rows
                from start not in skips will be read. If attempting to read
                a slice of a file a range instance may be provided and will have
                improved performance over other sequence types like lists.
            chunksize:
                The number of data lines to read for each yield. Lower values
                consume less memory. The default is 200,000 rows.
            skip_empty:
                A boolean indicating if rows with no values between the
                delimiters should be skipped. Default is True.
            raise_ragged:
                Boolean indicating if a row with more or fewer columns than
                expected should raise an error and stop reading. The default is
                False. Rows with fewer columns than the header will have None
                as  the fill value. Rows with more columns than the header will
                have None keys.

        Yields:
            Chunksize number of dictionary rows with header names as keys.

        Raises:
            csv.Error:
                A csv.Error is issued if a ragged row is encountered and
                raise_ragged is True. Casting problems do not raise errors but
                gracefully return strings when encountered.
        """

        skips = [] if not skips else skips

        # poll types & formats, inconsistencies will trigger casting error log
        types, _ = self._sniffer.types(self.poll, self.exclude)
        formats, _ = self._sniffer.datetime_formats(self.poll, self.exclude)
        castings = dict(zip(self.header.names, zip(types, formats)))

        # initialize casting and ragged row errors
        self.errors.casting = []
        self.errors.ragged = []

        # construct a row iterator
        row_iter, row_start = self._prime(start, indices)

        fifo: Deque[Dict[str, CellType]] = deque()
        for line, dic in enumerate(row_iter, row_start):

            if line in skips:
                continue

            if indices and line not in indices:
                continue

            if not any(dic.values()) and skip_empty:
                continue

            # chk & log raggedness
            dic = self._log_ragged(line, dic, raise_ragged)

            # perform casts, log errors & filter with tabulator
            arow = {}
            for name, astr in dic.items():

                casting, fmt = castings[name]
                try:
                    arow[name] = parsing.convert(astr, casting, fmt)
                except (ValueError, OverflowError, TypeError):
                    # on exception leave astr unconverted & log casting error
                    msg = f"line = {line}, column = '{name}'"
                    self.errors.casting.append(msg)
                    arow[name] = astr

            # apply tabs to filter row
            row = self.tabulator(arow)

            if row:
                fifo.append(row)

            if len(fifo) >= chunksize:
                yield [fifo.popleft() for _ in range(chunksize)]

        yield list(fifo)
        self.infile.seek(0)

    def peek(self, count: int = 10) -> None:
        """Prints count number of lines from the first line of the file.

        This method can be used to ensure this Reader identifies the correct
        metadata, header and data start locations.

        Args:
            count:
                The number of lines to print.

        Returns:
            None
        """

        cnt = 0
        while cnt < count:
            CRED = '\033[91m'
            CEND = '\033[0m'
            print(CRED + f'{cnt}' + CEND, next(self.infile).rstrip())
            cnt += 1

        self.infile.seek(0)

    def close(self):
        """Closes this Reader's infile resource."""

        self.infile.close()


if __name__ == '__main__':

    import doctest

    doctest.testmod()
