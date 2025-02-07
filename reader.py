"""

"""

import csv
import re
from itertools import zip_longest
from collections import abc, namedtuple, deque
from types import SimpleNamespace
from typing import Callable, Dict, List, Optional, Sequence

from tabbed import tabs
from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.utils.celltyping import CellType, convert
from tabbed.utils.mixins import ReprMixin

# Planning
#
# 8. Reader is the main type in Tabbed and should be available at package level
#    with no imports
# 9. Reader should have a sample method to show lines and indices to aid setting
#    specific numbers like count etc. Could call the method 'lines'
#

# FIXME declare in docs the supported celltypes
class Reader(ReprMixin):
    """A reader of delimited text files supporting iterative reading of specific
    rows and columns from files that possibly contain metadata and header
    components.

    Most CSV files do not adhere to the RFC-4180 CSV standard. In particular,
    many delimited files contain a metadata section in addition to a header line
    naming the columns of the data. Python's file sniffer can detect dialects
    but it's heuristic rules for detecting the header are limited and exclude
    the possibility of metadata. This reader uses an embedded sniffer to detect
    header and metadata sections. Additionally, all delimited text readers to
    date are unable to filter the data by value during reading. This reader can
    selectively read rows of the data using equality, membership, logical
    comparisons, regular expression matching and callable filters. These filters
    can be created using kwargs passed to the tab method.

    Attributes:
        infile:
            An I/O stream instance returned by open.
        sniffer:
            A tabbed Sniffer instance for dialect & file structure inference.
        dialect:
            The current dialect used by Sniffer. If problems are encountered
            during sniffing, this property may be changed to improve
            detection of header, metadata, and casting types of the Sniffer.
        header:
            A Header dataclass containing the header line number, the header
            column names, and the row string used to build the column names. If
            the header is not determnined by infile, the line number and row
            string are None type (see tabbed.sniffing module)
        metadata:
            A frozen dataclass containing the line numbers and metadata string
            from the infile. If not determined from infile the line number is
            None type.
        tabulator:
            An callable container that tracks the tabs to apply to each row and
            the columns to filter each row with.
        errors:

    Example:
        >>
    """

    def __init__(self, infile, **kwargs) -> None:
        """Initialize Reader with infile & any valid sniffer arguments."""

        self.infile = infile
        self.sniffer = Sniffer(self.infile, **kwargs)
        self._header = self.sniffer.header
        self._set_sniff()
        self.tabulator = tabs.Tabulator(self.header, rows=None, columns=None)
        self._error = namedtuple('error', 'line messages')
        self.errors = SimpleNamespace(casting=[], ragged=[])

    def _set_sniff(self) -> None:
        """On update of a Sniffer attribute, update this readers header.

        Monkey patches Sniffer's __setattr__ method in order to update this
        Reader's header whenever the embedded sniffer instance changes. This
        protected method should not be externally called.
        """

        def on_change(sniffer, name, value):
            """A replacement for Sniffer's __setattr__."""

            super(Sniffer, sniffer).__setattr__(name, value)
            self._header = sniffer.header

        Sniffer.__setattr__ = on_change

    @property
    def dialect(self):
        """Returns the Sniffer's current simplecsv dialect."""

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
                specification.
        """

        self.sniffer.dialect.__dict__.update(fmt_params)

    @property
    def header(self) -> Header | None:
        """Returns this Reader's header instance.

        This header may come from the sniffer or a previously set header.

        Returns:
            An instance of the Header dataclass (see sniffing module).
        """

        item = self._header
        # if header is a sniffer method call it
        return item() if isinstance(item, abc.Callable) else item

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

        num_columns = len(self.sniffer.rows()[-1])
        if isinstance(value, int):

            # sniff single line at index value, get str & make header
            sniffer = Sniffer(self.infile, start=value, amount=1)
            string = sniffer.sample[0]
            self._header = Header(value, sniffer.rows()[0], string)

        elif isinstance(value, List):

            if len(value) != column_count:
                msg = (f'Column count = {len(value)} does not match'
                      f'last sniffed row column count = {column_count}')
                raise ValueError(msg)

            # set index and string to none
            self._header = Header(line=None, names=value, string=None)

        elif isinstance(value, type(None)):

            # if None given as for sniffer's header
            self._header = self.sniffer.header()

        else:

            msg = f"Names must be type int, List[str], or None not {type(value)}"
            raise TypeError(msg)

        # on header change reset tabulator
        self.tabulator = tabs.Tabulator(self.header, rows=None, columns=None)

    @property
    def typecasts(self):
        """Returns the Sniffers type castings from the last 5 sample lines."""

        types = self.sniffer.types()
        if len(types) < len(self.header.names):
            msg = ('Casting count = {len(types)} does not match the number'
                   ' of header columns = {len(self.header.names}. Some columns will'
                   ' not be type casted'
                   )
            print(msg)

        return dict(zip_longest(self.header.names, types, fillvalue=str))

    def tab(
        self,
        columns: Optional[List[str | int] | re.Pattern] = None,
        **rows: dict[str, CellType | Sequence[CellType] | re.Pattern | Callable],
    ) -> None:
        """Set the Tabulator instance that will filter infiles rows & columns.

        Args:
            columns:
                Column names to be returned during reading. These may be
                provided as a list of string names, a list of column indices or
                a compiled regular expression pattern to match against header
                names. If None, all the columns in the header will be read
                during a read call.
            rows:
                name = value keyword argument pairs where name is a valid header
                column name and value may be of type string, CellType, reg.
                expression pattern or a callable. If a string type with rich
                comparison(s) is provided, a comparison tab is constructed. If
                a string, int, float, complex value or datetime is provided, an
                equality tab is constructed. If a sequence is provided,
                a membership tab is constructed. If a compiled re pattern
                a Regex tab is constructed. See class docs for example.

        Returns:
            None
        """

        self.tabulator = tabs.Tabulator.from_keywords(self.header, columns, **rows)

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
        elif self.sniffer.metadata.string:
            start = self.sniffer.metadata.lines[1] + 1

        return start

    def _ragged(self, line: int, row: dict[str, str], raise_error: bool) -> bool:
        """ """

        error_msg = None
        # a non-empty restkey or a None value indicates raggedness
        if row[None][0] or None in row.values():
            msg = f'Unexpected line length on row {line}'
            if raise_error:
                raise csv.Error(msg)
            else:
                self.errors.ragged.append(msg)

        row.pop(None, None)
        return row

    def _recast(
        self,
        line: int,
        row: dict[str, str],
        castings: dict[str, type],
        raise_error: bool,
    ) -> Dict[str, CellType]:
        """Applies named castings to a dictionary row.

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
        """

        error_msgs = []
        result = {}
        for name, value in row.items():
            try:
                result[name] = castings[name](value)
            except Exception as e:
                msg = "Casting error occurred on line = {}, column = '{}'"
                msg = msg.format(line, name)
                if raise_error:
                    # any other triggers an exception to be raised
                    print(msg)
                    raise e
                else:
                    result[name] = value
                    error_msgs.append(msg)

        if error_msgs:
            #self.errors.casting.append(self._error(line, error_msgs))
            self.errors.casting.extend(error_msgs)

        return result

    #TODO Finish docs
    def read(
        self,
        start: Optional[int] = None,
        skips: Optional[Sequence[int]] = None,
        indices: Optional[Sequence] = None,
        chunksize: int = int(1e6),
        skip_blanks: bool = True,
        castings: Optional[Dict[str, Callable[[str], CellType]]] = {},
        raise_cast: bool = False,
        raise_ragged: bool = False,
    ) -> List[Dict[str, CellType]]:
        """Read dictionary rows from an text delimited infile.

        Args:
            start:
                An integer line number to begin reading data. If None and
                Header has a line number, the line following the header line is the start.
                If None and header line number is None, the line following the metadata
                section is the start. If None and no header line or metadata
                lines are present, the start line will be 0.
            skips:
                A Sequence of integer line numbers to skip during reading.
        """

        # init None args and reset errors to fresh empty for this read
        start = self._autostart() if not start else start
        skips = [] if not skips else skips
        indices = range(0, len(self)) if not indices else indices
        self.errors = SimpleNamespace(casting=[], ragged=[])
        # update typecasts with castings
        typecasts = self.typecasts
        typecasts.update(castings)

        # advance to data section, build row iterator and fifo
        [next(self.infile) for _ in range(start)]
        riter = csv.DictReader(infile, self.header.names, dialect=self.dialect)
        fifo = deque()
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

        yield [row for row in fifo]


    def preview(self):
        """ """

        pass

    def close(self):
        """Closes the infile resource."""

        self.infile.close()

    def __len__(self):
        """Returns the number of lines in the infile."""

        return self.sniffer.line_count


if __name__ == '__main__':

    import time

    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)
    #reader = Reader(infile)
    print(reader.header)

    reader.tab(columns=['Trial_time', 'X_center', 'Y_center', 'Area'],
            Area='>0.01')

    x = reader.read(start=None, skips=[35], indices=None, chunksize=200000)

    t0 = time.perf_counter()
    result = []
    for idx, chunk in enumerate(x):
        print(idx)
        result.extend(chunk)

    print(f'elapsed time: {time.perf_counter() - t0}')
