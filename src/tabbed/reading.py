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
    """

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

    def castings(
        self,
        poll: int,
    ) -> Dict[str, Callable[[str], CellType]]:
        """Returns a mapping of callables for converting infile's columns.

        To quickly convert strings into Tabbed's supported data types, the last
        poll rows of the sniffer's sample are used to infer both types and
        possible date/time formats. These types and formats are then used to
        convert all of infile's rows from string values to CellTypes.

        Args:
            poll:
                The number of rows to poll to infer the column types and
                possibly the date/time formats.

        Returns:
            A dict of callables with all arguments frozen except for the string
            value to convert.

        Raises:
            None but warnings are issued if the types or formats are not
            consistent across the rows of the sample. Conversion errors will not
            raise errors but leave the string values at a row, column location
            unchanged.
        """

        # warn if there are type or format inconsistencies in sniff sample
        types, type_consistency = self._sniffer.types(poll)
        if not type_consistency:
            msg = ('Sniffer detected inconsistent column types. '
                   'Using most common type for each column.')
            warnings.warn(msg)

        fmts, fmt_consistency = self._sniffer.datetime_formats(poll)
        if not fmt_consistency:
            msg = ('Sniffer detected inconsistent datetime formats. '
                   'Using formats from last row of sniffed sample.')
            warnings.warn(msg)

        # construct mapping of header names and partial functions for casting
        result = dict(zip(self.header.names, types))
        for name, tp, fmt in zip(self.header.names, types, fmts):

            if fmt:
                result[name] = partial(parsing.as_datetime_type, tp=tp, fmt=fmt)

        return result

    def _datastart(self) -> int:
        """Returns the first line number of the data section.

        Returns:
            An integer line number.
        """

        start = 0
        line = self.header.line
        if line is not None:
            start = line + 1
        else:
            metalines = self._sniffer.metadata(line).lines
            start = metalines[1] + 1 if metalines[1] else metalines[0]

        return start

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

    def _log_miscast(self, line, row, expected):
        """Error logs rows that have at least one type mismatch with expected.

        Casting errors do not raise exceptions but are logged since they can be
        handled after reading.

        Args:
            line:
                The line number of the row being tested.
            row:
                A row dictionary of header names and casted values.
            expected:
                A dictionary of header names and expected column types.

        Returns:
            The row.
        """

        types = {name: type(val) for name, val in row.items()}
        miscast = {name for name in types if types[name] != expected[name]}
        if miscast:
            msg = f"line = {line}, column = '{miscast}'"
            self.errors.casting.append(msg)

        return row

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
        castings = self.castings(poll)
        expected = dict(zip(self.header.names, self._sniffer.types(poll)[0]))
        self.errors.casting = []
        self.errors.ragged = []

        # advance infile to data section to handle blank metadata lines
        start = self._datastart() if not start else start
        stop = None
        step = None
        if indices:

            # If indices are provided the start argument is ignored
            if isinstance(indices, range):
                start, stop, step = indices.start, indices.stop, indices.step

            elif isinstance(indices, Sequence):
                start = indices[0]
                stop = indices[-1]

            else:
                msg = f'indices must be a Sequence type not {type(indices)}.'
                raise TypeError(msg)

        if start < self._datastart():
            v = self._datastart()
            msg = f'Start must be > data section start row = {v}'
            raise ValueError(msg)

        # advance to data start to account for possible blank meta lines
        [next(self.infile) for _ in range(self._datastart())]
        row_iter = csv.DictReader(
                    self.infile,
                    self.header.names,
                    dialect=self._sniffer.dialect,
                    )
        # file is advanced to datastart so compute relative start
        relative_start = start - self._datastart()
        row_iter = itertools.islice(row_iter, relative_start, stop, step)

        fifo: Deque[Dict[str, CellType]] = deque()
        for line, dic in enumerate(row_iter, start):

            if line in skips:
                continue

            if indices and line not in indices:
                continue

            if not any(dic.values()) and skip_empty:
                continue

            # perform conversion, log errors & filter with tabulator
            row = {name: castings[name](val) for name, val in dic.items()}
            row = self._log_ragged(line, row, raise_ragged)
            row = self._log_miscast(line, row, expected)
            row = self.tabulator(row)

            if row:
                fifo.append(row)

            if len(fifo) >= chunksize:
                yield [fifo.popleft() for _ in range(chunksize)]

        yield list(fifo)
        self.infile.seek(0)

    def as_list(self, datagen):
        """ """

        return list(*itertools.chain(datagen))

if __name__ == '__main__':

    fp = '/home/matt/python/nri/tabbed/__data__/mouse_annotations.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)
    datagen = reader.read()
