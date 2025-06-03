"""

"""
from __future__ import annotations
import csv
import datetime
from functools import partial
from types import SimpleNamespace
from typing import Dict, Deque, IO, List, Optional, Sequence
import warnings
import itertools
from collections import deque
import copy


from tabbed.sniffing import Header, Sniffer
from tabbed.tabbing import Tabulator
from tabbed.utils.mixins import ReprMixin
from tabbed.utils import parsing
from tabbed import tabbing


class Reader(ReprMixin):
    r"""An iterative reader of structurally variable text files supporting
    conditional reading of selective rows and columns.

    A lack of formal specifications for a CSV format has led to many
    structurally variant implementations. Many variants of the RFC-4180 standard
    include metadata prior to a possible header and data section. This reader
    sniffs files for these sections advancing to the most-likely start
    position of the data section. This reader uses type inference to
    automatically convert cells in the data section to strings, integers,
    floats, complex, time, date or datetime instances. Finally, this reader
    supports selective reading of rows based equality, membership, comparison, and
    regular expression value based conditions via Tab callables that may be
    supplied as keyword arguments to the 'tab' method.

    Attributes:
        infile:
            An I/O stream instance returned by open.
    """

    def __init__(self, infile:IO[str], **sniffing_kwargs) -> None:
        """Initialize this Reader."""

        self.infile = infile
        self._sniffer = Sniffer(infile, **sniffing_kwargs)
        self._header = self._sniffer.header()
        self.tabulator = Tabulator(self.header, columns=None, tabs=None)
        self.errors = SimpleNamespace(casting=[], ragged=[])

    @property
    def sniffer(self) -> Sniffer:
        """Returns this Reader's sniffer.

        If this Reader's header has been determined by sniffing the infile, then
        accessing the sniffer will remeasure the header and reset the Tabulator.
        For example, if the start attribute of the sniffer is changed and the
        header was previously determined by the sniffer, then the header will
        be remeasured and the Tabulator reset.
        """

        if self._header.line is not None:
            print('Resniffing Header and resetting Tabulator')
            self._header = self._sniffer.header()
            self.tabulator = Tabulator(self.header, columns=None, tabs=None)

        return self._sniffer

    @property
    def header(self) -> Header:
        """Fetches this Reader's current header."""

        return self._header

    @header.setter
    def header(self, value: int | List[str] | Dict[str, int]) -> None:
        """Sets this Reader's header and resets the Tabulator.

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

        if not isinstance(value, (int, list, dict)):
            msg = (
                    "A header may be set by integer line number, list of "
                    "header names or a dict of kwargs for sniffer's header "
                    f"method but not type {type(value)}."
                    )
            raise ValueError(msg)

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

        if isinstance(value, list):
            if len(value) != expected:
                msg = (
                    f'Length of provided header names = {len(value)} does '
                    f'not match length of last sample row = {expected}'
                )
                raise ValueError(msg)
            result = Header(None, value, None)

        if isinstance(value, dict):
            result = self._sniffer.header(**value)

        # set header
        self._header = result
        # determine if reader has previously set tabulator and warn
        previous  = self.tabulator
        tblr = Tabulator(self.header, tabs=None, columns=None)
        if tblr.columns != previous.columns or tblr.tabs != previous.tabs:
            msg = ("Previously set tabs have been reset. Please call 'tab' "
                   "method again before reading.")
            print(msg)

        self.tabulator = tblr

    def tab(
        self,
        columns: Optional[List[str | int] | re.Pattern] = None,
        **tabs: dict[
            str, CellType | Sequence[CellType] | re.Pattern | Callable
        ],
    ) -> None:
        """Set the Tabulator instance that will filter infile's rows & columns.

        A tabulator is a container of tab instances that when called on a row,
        sequentially applies each tab to that row. Additionally after applying
        the row tabs it filters the result by columns. Implementation details
        may be found in the tabbed.tabs module.

        Args:
            columns:
                Names of the columns in each row to return during reading. These
                may be provided as a list of string names, a list of column
                indices or a compiled regular expression pattern to match
                against header names. If None, all the columns in the header
                will be read during a read call.
            tabs:
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
        ) -> csv.DictReader:
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
                An optional Sequence of line numbers to read rows from. If None,
                all rows from start not in skips will be read. If reading
                a slice of the file, a range instance will have improved
                performance over list or tuple sequence types.

        Returns:
            A DictReader row iterator & row index the iterator starts from.

        Raises:
            A ValueError is issued if start or start index is less than the data
            section start row.
        """

        # locate the start of the datasection
        autostart = 0
        if self.header.line is not None:
            autostart = self.header.line + 1
        else:
            metalines = self._sniffer.metadata(line).lines
            auotstart = metalines[1] + 1 if metalines[1] else metalines[0]

        start = start if start else autostart
        stop = None
        step = None

        # indices if provided override start, stop and step
        if indices:

            if isinstance(indices, range):
                start, stop, step = indices.start, indices.stop, indices.step

            elif isinstance(indices, Sequence):
                start, stop = indices[0], indices[-1]

            else:
                msg = f'indices must be a Sequence type not {type(indices)}.'
                raise TypeError(msg)

        # validate our start is in the data section
        if start < autostart:
            msg = f'Start must be > data section start row = {autostart}'
            raise ValueError(msg)

        # advance reader's infile to account for blank metalines
        [next(self.infile) for _ in range(start)]
        row_iter = csv.DictReader(
                    self.infile,
                    self.header.names,
                    dialect=self._sniffer.dialect,
                    )

        return itertools.islice(row_iter, 0, stop, step), start

    def read(
        self,
        start: Optional[int] = None,
        skips: Optional[Sequence[int]] = None,
        indices: Optional[Sequence] = None,
        chunksize: int = int(2e5),
        skip_empty: bool = True,
        poll: int = 5,
        raise_ragged: bool = False,
    ) -> Iterator[List[Dict[str, CellType]]]:
        """ """

        skips = [] if not skips else skips

        # poll types & formats, inconsistencies will trigger casting error log
        types, _ = self._sniffer.types(poll)
        formats, _ = self._sniffer.datetime_formats(poll)
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
            row = {}
            for name, astr in dic.items():

                casting, fmt = castings[name]
                try:
                    row[name] = parsing.convert(astr, casting, fmt)
                except Exception as e:
                    # on exception leave astr unconverted & log casting error
                    msg = f"line = {line}, column = '{name}'"
                    self.errors.casting.append(msg)
                    row[name] = astr

            # apply tabs to filter row
            row = self.tabulator(row)

            if row:
                fifo.append(row)

            if len(fifo) >= chunksize:
                yield [fifo.popleft() for _ in range(chunksize)]

        yield list(fifo)
        self.infile.seek(0)



if __name__ == '__main__':

    import time
    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)
    datagen = reader.read(chunksize=int(1e5), skips=[35],
            indices=range(int(1e5), int(5e5)))

    t0 = time.perf_counter()
    amt = 0
    for chunk in datagen:
        amt += len(chunk)
        print(f'{amt} rows read')

    print(time.perf_counter() - t0)
