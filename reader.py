"""A reader of text delimited files that supports the following features.
    - Automatic identification of metadata & header file sections.
    - Automatic type conversion to ints, floats, complex numbers,
      times, dates and datetime instances.
    - Selective reading of rows and columns satisfying equality,
      membership, regular expression, and rich comparison conditions.
    - Iterative reading of rows from the input file.
"""

from collections import abc
from collections import deque
import csv
import re
from types import SimpleNamespace
from typing import Callable, Deque, Dict, Iterator, List, Optional, Sequence

from tabulate import tabulate

from tabbed import tabs
from tabbed.sniffing import Header
from tabbed.sniffing import MetaData
from tabbed.sniffing import Sniffer
from tabbed.utils.celltyping import CellType
from tabbed.utils.mixins import ReprMixin


class Reader(ReprMixin):
    r"""A reader of delimited text files supporting iterative reading of
    specific rows and columns from files that possibly contain metadata and
    header components.

    Most CSV files do not adhere to the RFC-4180 CSV standard. In particular,
    many delimited files contain a metadata section in addition to a header line
    naming the columns of the data. Python's file sniffer can detect dialects
    but it's heuristic rules for detecting the header are limited and exclude
    the possibility of metadata. This reader uses a structural sniffer to detect
    header and metadata sections. Additionally, all delimited text readers to
    date are unable to filter the data by value during reading. This reader can
    selectively read rows of the data using equality, membership, logical
    comparisons, regular expression matching and callable filters. These filters
    can be created using kwargs passed to the tab method. This reader supports
    automatic type conversion to ints, floats, complex numbers, times, dates and
    datetime types. Type conversions errors are gracefully handled by returning
    strings and logging casting errors for review.

    Attributes:
        infile:
            An I/O stream instance returned by open.
        sniffer:
            A tabbed Sniffer instance for dialect & file structure inference.
        dialect:
            The current dialect used by Sniffer. If problems are encountered
            during sniffing, this property may be changed to improve
            detection of header, metadata, and casting types of the Sniffer. The
            dialect parameters that may be changed are; delimiter, escapechar
            and quotechar. Please see the dialect property for a description of
            these parameters.
        header:
            A Header dataclass containing the header line number, the header
            column names, and the row string used to build the column names. If
            the header is not determnined by infile, the line number and row
            string are None type (see tabbed.sniffing module). Attribute changes
            on the embedded sniffer are dynamically reflected in changes to this
            header attribute.
        metadata:
            A frozen dataclass containing the line numbers and metadata string
            from the infile. If not determined from infile the line number is
            None type. Attribute changes on the embedded sniffer are dynamically
            reflected in changes to this metadata attribute.
        typecasts:
            A dictionary of column names and sniffed data types used to convert
            string values from the input file. These types may be overridden in
            the 'read' method for custom type casting.
        tabulator:
            An callable container of tab instances that sequentially applies the
            tabs supplied to the 'tab' method to filter rows and columns of the
            infile during reading. Please type help on the 'tab' method for
            details on how to create tabs using keyword arguments.
        errors:
            A SimpleNamespace instance containing two lists called casting and
            ragged. The casting list is a list of strings indicating the line
            and columns on which casting failed. The ragged list is a list of
            strings indicating the line numbers which have too many or too few
            fields.

    Example:
        >>> # This example creates a temp file with both a header and metadata
        >>> import os
        >>> import tempfile
        >>> import random
        >>> import datetime
        >>> random.seed(0) # make a reproducible random number generator
        >>> # make a metadata string that spans several lines
        >>> metadata_string = ('Experiment, 3\n'
        ... 'Name, Ernst Rutherford\n'
        ... 'location, Cavendish Labs\n'
        ... 'Time, 11:03:29.092\n'
        ... 'Date, 8/23/1917\n')
        >>> # make a header string of 5 columns
        >>> header = ['group', 'count', 'color', 'time', 'area']
        >>> header_string = ','.join(header) + '\n'
        >>> # make 20 data rows of random data
        >>> groups = random.choices(['a', 'b', 'c'], k=20)
        >>> counts = [str(random.randint(0, 10)) for _ in range(20)]
        >>> colors = random.choices(['red', 'green', 'blue'], k=20)
        >>> start = datetime.datetime(1917, 8, 23, 11, 3, 29, 9209)
        >>> times = [str(start + datetime.timedelta(seconds=10*i)) for i in range(20)]
        >>> areas = [str(random.uniform(0, 10)) for _ in range(20)]
        >>> # make a data string
        >>> x = [','.join(row) for row in zip(groups, counts, colors, times, areas)]
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
        Header(line=5,
        names=['group', 'count', 'color', 'time', 'area'],
        string='group,count,color,time,area')
        >>> # peek at the first 10 lines of the data section
        >>> reader.peek(range(10))
        ... # doctest: +SKIP
        >>> # read group, count & area columns where group is a or c & 0 < area <=4
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

    def __init__(self, infile, **kwargs) -> None:
        """Initialize Reader with infile and sniffer keyword arguments."""

        self.infile = infile
        self.sniffer = Sniffer(self.infile, **kwargs)
        self._header = self.sniffer.header
        self._set_sniff()  # on sniffer attr change update header
        self.tabulator = tabs.Tabulator(self.header, rows=None, columns=None)
        self.errors = SimpleNamespace(casting=[], ragged=[])

    def _set_sniff(self) -> None:
        """On update of a Sniffer attribute, update this readers header.

        Monkey patches Sniffer's __setattr__ method in order to update this
        Reader's header whenever the embedded sniffer instance changes. This
        protected method should not be externally called.
        """

        def on_change(sniffer, name, value):
            """A replacement for Sniffer's __setattr__."""

            # access a setattr method of non-direct parent
            # pylint: disable-next = bad-super-call
            super(Sniffer, sniffer).__setattr__(name, value)
            self._header = sniffer.header

        Sniffer.__setattr__ = on_change

    @property
    def dialect(self):
        """Returns the Sniffer's current Simplecsv dialect."""

        return self.sniffer.dialect

    @dialect.setter
    def dialect(self, **fmt_params: Dict[str, str | bool | None]) -> None:
        """Sets Sniffer's current simplecsv dialect.

        Args:
            fmt_params:
                A dictionary of formatting params to update. Valid names are
                'delimiter', 'quotechar', 'escapechar' and 'strict'. Delimiter
                refers to the character used to separate columns. Quotechar is
                the character used to quote strings, escapechar is used for
                writers and is not relevant and strict refers to error handling
                if a bad csv is encountered. Please see Python csv dialect
                specification for further details.
        """

        self.sniffer.dialect.__dict__.update(fmt_params)

    @property
    def header(self) -> Header:
        """Returns this Reader's header data class instance.

        This header may come from the sniffer or a previously set header.

        Returns:
            An instance of the Header dataclass (see sniffing module).
        """

        item = self._header
        # if header is a sniffer method call it
        return item() if callable(item) else item

    @header.setter
    def header(self, value: int | List[str] | None) -> None:
        """Set this Reader's header.

        Args:
            value:
                An integer, list of strings or None. If int type, the row in
                infile at value line number will be used as the header.  If
                a list of string types, the header will be built from the list.
                If None, the sniffer's header will returned. If the sniffer
                fails to find the header, a generic header is returned with
                names = ['Column_0', 'Column_1', ...].

        Returns:
            None

        Raises:
            A TypeError is raise if value is not a valid type.
        """

        column_count = len(self.sniffer.rows()[-1])
        if isinstance(value, int):

            # sniff single line at index value, get str & make header
            sniffer = Sniffer(self.infile, start=value, amount=1)
            string = sniffer.sample[0]
            self._header = Header(value, sniffer.rows()[0], string)

        elif isinstance(value, List):

            if len(value) != column_count:
                msg = (
                    f'Column count = {len(value)} does not match'
                    f'last sniffed row column count = {column_count}'
                )
                raise ValueError(msg)

            # set index and string to none
            self._header = Header(line=None, names=value, string=None)

        elif isinstance(value, type(None)):

            # if None given as for sniffer's header
            self._header = self.sniffer.header()

        else:

            msg = (
                f"Names must be type int, List[str], or None not {type(value)}"
            )
            raise TypeError(msg)

        # on header change reset tabulator
        self.tabulator = tabs.Tabulator(self.header, rows=None, columns=None)

    @property
    def metadata(self) -> MetaData:
        """Returns this Reader's metadata dataclass from sniffer."""

        return self.sniffer.metadata

    def typecasts(self, count=5) -> Dict[str, Callable[[str], CellType]]:
        """Returns a mapping of column names and column types.

        To quickly perform type conversions, the sniffer polls count number of
        lines in each column of the sniffer's sample to infer types. A single
        type is then used to cast all cells within that column.

        Args:
            count:
                The number of cells within a column to poll for type.

        Returns:
            A mapping of header names and the inferred types.
        """

        types = self.sniffer.types(count)

        return dict(zip(self.header.names, types))

    def tab(
        self,
        columns: Optional[List[str | int] | re.Pattern] = None,
        **rows: dict[
            str, CellType | Sequence[CellType] | re.Pattern | Callable
        ],
    ) -> None:
        """Set the Tabulator instance that will filter infiles rows & columns.

        A tabulator is a container of tab instances that when called on a row,
        sequentially applies each tab to that row. Additionally after applying
        the row tabs it filters the result by columns. Implementation details
        may be found in the tabbed.tabs module.

        Args:
            columns:
                Column names to be returned during reading. These may be
                provided as a list of string names, a list of column indices or
                a compiled regular expression pattern to match against header
                names. If None, all the columns in the header will be read
                during a read call.
            rows:
                name = value keyword argument pairs where name is a valid header
                column name and value may be of type string, int, float,
                complex, time, date, datetime, regular expression or callable.
                If a string type with rich comparison(s) is provided,
                a comparison tab is constructed. If a string, int, float,
                complex, time, date  or datetime is provided, an equality tab is
                constructed. If a sequence is provided, a membership tab is
                constructed. If a compiled re patterni, a Regex tab is
                constructed. See class docs for example.

        Returns:
            None
        """

        self.tabulator = tabs.Tabulator.from_keywords(
            self.header, columns, **rows
        )

    def _autostart(self):
        """Locates the start line of the data section.

        Infers start of the data section of infile by looking at whether the
        Header instance has a line number in the infile or if not, examining if
        the metadata section exist and fetching its line numbers.

        This protected method is subject to change and should not be called
        externally.

        Returns:
            An integer line number that begins the data section.
        """

        start = 0
        if self.header.line:
            start = self.header.line + 1
        elif self.sniffer.metadata(None).string:
            start = self.sniffer.metadata(None).lines[1] + 1

        return start

    # ignore typing here for speed
    def _ragged(self, line, row, raise_error):
        """Error logs rows that are shorter or longer than expected.

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
                A row dictionary of header names and string values.
            raise_error:
                A boolean indicating if ragged should raise an error and stop
                the reading of the file if a ragged row is encountered.

        Returns:
            The row with None restkey popped
        """

        remainder = row.pop(None, [None])
        none_vals = None in row.values()

        if any(remainder) or none_vals:
            msg = f'Unexpected line length on row {line}'
            if raise_error:
                raise csv.Error(msg)
            self.errors.ragged.append(msg)

        return row

    def _recast(
        self,
        line: int,
        row: dict[str, str],
        castings: dict[str, type],
        raise_error: bool,
    ) -> Dict[str, CellType]:
        """Applies named castings to a dictionary row.

        Tabbed automatically casts infile cells to int, float, complex, time,
        date, and datetime types. This function allows these castings to occur
        gracefully be defaulting to str type on casting error. Each error is
        logged to the error log.

        Args:
            line:
                The integer line number of row.
            row:
                A dictionary row whose string values will be recast.
            castings:
                A dictionary of casting callables that accept a string &
                return a CellType. The keys must match this reader's header.
            issue:
                A string, one of {'ignore', 'warn', 'raise'} indicating whether
                cast failure on a row should be ignored, a warning issued or an
                exception raised.

        Returns:
            The row with values recast according to castings.

        Raises:
            A ValueError is raised if raise_error and a cell can not be cast
            with the specified casting.
            An Overflow error is raised if raise_error and the cell value
            exceeds the maximum value for that datatype.
        """

        error_msgs = []
        result = {}
        for name, value in row.items():
            try:
                result[name] = castings[name](value)
            # slight speed boost if ignore exception type (Value, Overflow)
            # pylint: disable-next broad-exception-caught
            except Exception as e:
                msg = "Casting error occurred on line = {}, column = '{}'"
                msg = msg.format(line, name)
                if raise_error:
                    # any other triggers an exception to be raised
                    print(msg)
                    raise e

                result[name] = value
                error_msgs.append(msg)

        if error_msgs:
            self.errors.casting.extend(error_msgs)

        return result

    def read(
        self,
        start: Optional[int] = None,
        skips: Optional[Sequence[int]] = None,
        indices: Optional[Sequence] = None,
        chunksize: int = int(200e3),
        skip_blanks: bool = True,
        castings: Optional[Dict[str, Callable[[str], CellType]]] = None,
        raise_cast: bool = False,
        raise_ragged: bool = False,
    ) -> Iterator[List[Dict[str, CellType]]]:
        """Iteratively read dictionary rows that satisfy this Reader's tabs.

        Args:
            start:
                An integer line number from the start of the file to begin
                reading data. If None and Header has a line number, the line
                following the header line is the start.  If None and header line
                number is None, the line following the metadata section is the
                start. If None and no header line or metadata lines are present,
                the start line will be 0.
            skips:
                A Sequence of integer line numbers to skip during reading.
            indices:
                An optional sequence of line numbers to read rows from. If None,
                all rows from start that are not in skips will be read.
            chunksize:
                The number of data lines to read at a time. Changing this
                argument to lower values results in lower memory overhead but
                possibly at the expense of runtime. The default is to read
                200,000 lines at a time.
            skip_blanks:
                A boolean indicating if blank lines should be skipped or
                included.
            castings:
                A mapping of column names and types for casting specific columns
                of the data.
            raise_cast:
                A boolean indicating if casting errors should be raised (i.e.
                stop reading) or ignored but logged. On a casting error, this
                reader will gracefully default to string type.
            raise_ragged:
                A boolean indicating if rows with too many or too few cells, as
                compared with the header, should raise an error (i.e. stop
                reading) or be ignored. On a ragged error, this reader will
                gracefully log the error and drop any cells not associated with
                a header column.

        Yields:
            A list of dictionary rows. The number of dicts in each row will be
            chunksize if the number of lines left to read is greater than
            chunksize and smaller otherwise.
        """

        # init None args and reset errors to fresh empty for this read
        start = self._autostart() if not start else start
        skips = [] if not skips else skips
        indices = range(0, len(self)) if not indices else indices
        self.errors = SimpleNamespace(casting=[], ragged=[])
        # update typecasts with castings
        typecasts = self.typecasts()
        typecasts.update(castings if castings else {})

        # advance to data section, build row iterator and fifo
        _ = [self.infile.readline() for _ in range(start)]
        riter = csv.DictReader(
            self.infile, self.header.names, dialect=self.dialect
        )
        fifo: Deque[Dict[str, CellType]] = deque()
        for line, dic in enumerate(riter, start):

            if line in skips or line not in indices:
                continue

            if not any(dic.values()):
                if skip_blanks:
                    continue

            # log whether the row is ragged and recast
            row = self._ragged(line, dic, raise_ragged)
            row = self._recast(line, dic, typecasts, raise_cast)

            row = self.tabulator(row)
            if row:
                fifo.append(row)

            if len(fifo) >= chunksize:
                yield [fifo.popleft() for _ in range(chunksize)]

        yield list(fifo)
        self.infile.seek(0)

    def peek(self, start: int = 0, count: int = 10, **kwargs) -> str:
        """Prints count number of lines from the start of the data section.

        Args:
            start:
                The first line to peek at relative to the data section start
                line which follows the header line or metadata lines if present.
            count:
                The number of lines to peek at.
            kwargs:
                Any valid keyword argument for this Reader's read method except
                for indices which is determined by start and count.
        """

        # set the start position relative to the datastart using autostart
        a = self._autostart() + start
        b = a + count
        data = []
        rows = self.read(indices=range(a, b), **kwargs)
        [data.extend(chunk) for chunk in rows]
        table: str = tabulate(data, headers='keys', tablefmt='simple_grid')
        print(table)

        return table

    def close(self):
        """Closes the infile resource."""

        self.infile.close()

    def __len__(self):
        """Returns the number of lines in the infile."""

        return self.sniffer.line_count


if __name__ == '__main__':

    # import doctest

    # doctest.testmod()

    import time

    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)
    # reader = Reader(infile)
    print(reader.header)

    reader.tab(
        columns=['Trial_time', 'X_center', 'Y_center', 'Area'], Area='>0.01'
    )
    datagen = reader.read(
        start=None, skips=[35], indices=None, chunksize=200000
    )

    t0 = time.perf_counter()
    result = []
    for idx, chunk in enumerate(datagen):
        print(idx, len(chunk))
        result.extend(chunk)

    print(f'elapsed time: {time.perf_counter() - t0}')
    reader.close()
