"""

"""

import csv
import re
from itertools import islice
from collections import abc, namedtuple
from typing import Callable, Dict, List, Optional, Sequence

from tabbed import tabs
from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.utils.queues import ListFIFO
from tabbed.utils.celltyping import CellType, convert
from tabbed.utils.mixins import ReprMixin

# Planning
#
# 3. reader should have an index method which will add a client named index to
#    the rows prior to filters to allow for row index filtering
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
            A list to store casting errors. Each error is a namedtuple containing a line
            number and the error messages that occured during casting of values
            on that line. These errors are only stored if the read methods
            'raised' argument is False.

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
        self.errors = []

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

    def _recast(
        self,
        line: int,
        row: dict[str, str],
        castings: dict[str, type],
        raise_error: bool,
    ) -> Dict[str, CellType]:
        """Applies named castings to dictionary row at line.

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
                if raise_error:
                    msg = "Casting error occurred on line = {}, column = '{}'"
                    # any other triggers an exception to be raised
                    msg = msg.format(line, name)
                    print(msg)
                    raise e
                else:
                    result[name] = value
                    error_msgs.append(str(e))

        if error_msgs:
            self.errors.append(self._error(line, set(error_msgs)))


        return result


    def read(
        self,
        start: Optional[int],
        skips: Optional[List[int]],
        indices: Optional[Sequence] = None,
        chunksize: int = int(1e6),
        raise_error: bool = False,
        castings: Optional[Dict[str, Callable[[str], CellType]]] = None,
        **fmt_params,
    ) -> List[Dict[str, CellType]]:
        """ """

        if start is None:
            start = self.header.line + 1 if self.header.line else 0
        skips = [] if not skips else skips
        indices = range(0, len(self)) if not indices else indices
        chunksize = min(len(self), len(indices), chunksize)
        casts = {} if not castings else castings
        # reset errors
        self.errors = []

        # FIXME point of failure that needs docs
        # ask sniffer for castings and update with client casts
        delimiter = fmt_params.get('delimiter', None)
        castings = dict(
                zip(
                    self.header.names,
                    self.sniffer.types(delimiter=delimiter,
                    )
                    )
                )
        castings.update(casts)
        chunk = 0
        # advance to the data section
        [next(self.infile) for _ in range(start)]
        # build reader and FIFO for chunksize dequeing
        dreader = csv.DictReader(
                infile,
                self.header.names,
                restkey=None,
                restval='',
                dialect = self.sniffer.dialect,
                **fmt_params,
                )
        fifo = ListFIFO(chunksize)
        for line, dic in enumerate(dreader, start):

            if line in skips:
                continue

            if not any(dic.values()):
                continue

            if line not in indices:
                continue

            # remove any values under the None restkey and recast
            # TODO decide if ever needed...
            dic.pop(None)
            row = self._recast(line, dic, castings, raise_error)

            row = self.tabulator(row)
            if row:
                fifo.put(row)

            if fifo.full():
                print(f'yielding chunk {chunk}')
                chunk += 1
                yield fifo.get()

        yield fifo.get()


    def preview(self):
        """ """

        pass

    def close(self):
        """ """

        self.infile.close()

    def __len__(self):
        """ """

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

    x = reader.read(start=None, skips=[35], indices=range(34, 10000), chunksize=200000)

    t0 = time.perf_counter()
    result = []
    [result.extend(rows) for rows in x]
    print(f'elapsed time: {time.perf_counter() - t0}')
