"""

"""

import csv
import re
from itertools import islice #FIXME to be removed
from collections import abc
from typing import Callable, List, Optional, Sequence

from tabbed import tabs
from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.utils.queues import ListFIFO
from tabbed.utils.celltyping import CellType, convert
from tabbed.utils import parsing
from tabbed.utils.mixins import ReprMixin

# Planning
#
# 2. reader should have a 'peek' or show method to show a sample of what will be
#    read in a nice format
# 3. reader should have an index method which will add a client named index to
#    the rows prior to filters to allow for row index filtering
# 7. reader's read method should support chunk interation of rows that yield
#    consistent sizes after filtering FIFO
# 8. Reader is the main type in Tabbed and should be available at package level
#    with no imports
# 9. Reader should have a sample method to show lines and indices to aid setting
#    specific numbers like count etc. Could call the method 'lines'
#
class _Columns(ReprMixin):
    """ """

    def __init__(self, header):
        """ """

        self.header = header
        self._names = header.names

    @property
    def names(self):
        """Returns columns names."""

        return self._names

    @names.setter
    def names(self, other: Sequence[str|int] | re.Pattern) -> None:
        """Validate and set the column names.

        Args:
            other:
                A sequence of string names, header name indices or a compiled
                re pattern to match against header names.

        Raises:
            A ValueError is issued if names contains mixed types.
            An IndexError is issued if a name in names is not in the header.
        """

        if not isinstance(other, (Sequence, re.Pattern)):
            msg = 'Value must be a Sequence[str|int] or re.Pattern type'
            raise TypeError(msg)

        if isinstance(names, re.Pattern):
            pattern = names
            res = [x for x in self.header.names if bool(re.search(pattern, x)]

        elif all(isinstance(name, int) for name in names):
            indices = names
            res = [self.header.names[idx] for idx in indices]

        elif all(isinstance(name, str) for name in names):
            res = names

        else:
            msg = 'Columns types must all be strs, ints or an re.Pattern'
            raise ValueError(msg)

        # validate the elements are a subset of the header names
        if not set(self.header).issuperset(res):
            invalid = set(res).difference(self.header)
            raise IndexError(f'[{invalid}] are not a valid column name(s)')

        self._names = res

    @names.deleter
    def names(self):
        """ """

        self._names = self.header.names



class Reader(ReprMixin):
    """A reader of delimited text files supporting iterative reading of specific
    rows and columns from files that possibly contain metadata and header
    components.

    Most CSV files do not adhere to the RFC-4180 CSV standards. In particular,
    many delimited files contain a metadata section in addition to a header line
    naming the columns of the data. Python's file sniffer can detect dialects
    but it's heuristic rules for detecting the header are limited and exclude
    the possibility of metadata. This reader uses an embedded sniffer to detect
    header and metadata sections. Additionally, all delimited text readers to
    date are unable to filter the data by value during reading. This reader
    can filter both rows and columns of the data using equality, membership,
    comparisons, regular expression matching and callables to select rows during
    reading. These filters are stored to objects called Tabs that can be
    dynamically changed from this Reader instance.

    Attributes:
        infile:
            An I/O stream instance returned by open.
        sniffer:
            A tabbed Sniffer instance fo inferring the dialect and structure of
            infile.
        header:
            A Header named tuple instance from sniffer. This value is
            updated on any change to this Reader's sniffer.
        columns:
            A callable that determines the columns of the data to return during
            read. This callable is set by creating a tab via the tab method
            allowing columns to be selected by regex pattern, membership or index.
        rows:
            A sequence of callables that determines the rows of data to return
            during read. These callables can be set by creating a tab via the
            tab method allowing rows to be filtered by comparison, equality,
            membership, regex or callable.

    Example:
        >>
    """

    def __init__(self, infile, **kwargs) -> None:
        """Initialize Reader with infile & any valid sniffer arguments."""

        self.infile = infile
        self.sniffer = Sniffer(self.infile, **kwargs)
        # set protected attributes accessible by property access only
        self._header = self.sniffer.header
        self._set_sniff()

        self.columns = Columns(self.header)
        self.tabbed = []

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
    def header(self, value: int | List[str] | str) -> None:
        """Sets this Reader's header.

        Args:
            value:
                An integer, list of strings or the string 'generic'. If int
                type, the row in infile at line number = value will be used as
                the header.  If a list of string types, the header will be built
                from the list. If a string matching 'generic', a list of column
                names matching the length of the columns in the last sniffed
                sample row will be created. The form of the column names will be
                [Column_0, Column_1 ...].

        Returns:
            None

        Raises:
            A ValueError is issued if value is string type but does not match
            the string 'generic'. A TypeError is raise if value is not a valid
            type.
        """

        num_columns = len(self.sniffer.rows()[-1])
        if isinstance(value, int):

            sniffer = Sniffer(self.infile, start=value, amount=1)
            self._header = Header(sniffer.rows()[0], value)

        elif isinstance(value, List):

            if len(value) != column_count:
                msg = (f'Column count = {len(value)} does not match'
                      f'last sniffed row column count = {column_count}')
                raise ValueError(msg)

            # set index of header to None
            self._header = Header(value, None)

        elif isinstance(value, str):

            if value.lower() != 'generic':
                msg = f"Only string 'generic' is valid not {value}"
                raise ValueError(msg)

            names = [f'Column_{i}' for i in range(num_columns)]
            self._header = Header(names, None)

        else:

            msg = f"Names must be type int, List[str], or str not {type(value)}"
            raise TypeError(msg)

        # on header change update tabs and columns
        self.tabs = []
        self.columns.names = self.header.names

    def tab(
        self,
        **tabbings: dict[
            str,
            CellType | Sequence[CellType] | re.Pattern | Callable],
        ):
        """ """

        for name, value in tabbings.items():

            if parsing.is_comparison(value):
                tab = tabs.Comparison(name, value)

            if parsing.is_celltype(value):
                tab = tabs.Equality(name, value)

            if parsing.is_regex(value):
                tab = tabs.Regex(name, value)

            if parsing.is_sequence(value):
                tab = tabs.Membership(name, value)

            self.tabbed.append(tab)



    # FIXME clean-up
    def _convert(self, line, row, converters, error):
        """Converts a single row."""

        def safe_convert(arow, converters):
            """ """
            
            result = {}
            for name, astring in arow.items():
                try:
                    result[name] = converters[name](astring)
                except:
                    result[name] = astring

            return result


        try:

            return {name: converters[name](astr) for name, astr in row.items()}

        except Exception as e:

            if error == 'raise':
                print(f'Exception occured on line number {line}')
                raise e

            if error == 'warn':
                print(f'Skipping some conversion(s) on line number {line}')
                print(e)
                return safe_convert(row, converters)

            return safe_convert(row, converters)


    def read(
        self,
        start=None,
        skips=None,
        chunksize=None,
        index_name='index',
        errors='warn',
        **fmtparams,
        ):
        """ """

        # TODO
        # 1. allow dtypes dict to be passed or a single dtype for whole file
        # 3. date format passing default to None for inference


        if start is None:
            start = self.header.line + 1 if self.header.line else 0

        skips = [] if not skips else skips
        chunksize = len(self) if not chunksize else chunksize
        # advance to the data section
        [next(self.infile) for _ in range(start)]
        dictreader = csv.DictReader(
                    infile,
                    self.header.names,
                    restkey=None,
                    restval='',
                    dialect = self.sniffer.dialect, **fmtparams)

        # TODO could update with custom converters if desired
        converters = dict(zip(self.header.names, self.sniffer.types()))
        fifo = ListFIFO(chunksize)

        # testing limit
        #dreader = islice(dictreader, 0, 500000)
        for line, dic in enumerate(dictreader, start):

            if line in skips:
                continue

            if not any(dic.values()) and skip_blank:
                continue

            unnamed = dic.pop(None)

            # FIXME how to do index row filtering fast??
            # Updating the dic and header dramatically slows reading down
            """
            dic.update({index_name: line})
            self.header.names.append(index_name)
            """

            """
            needed = set(self.header.names)
            if self.columns:
                needed = set(self.columns.tabs)
            if self.rows:
                needed.update(set(self.rows.tabs))

            dic = {name: astring for name, astring in dic.items() if name in needed}
            """

            res = self._convert(line, dic, converters, errors)


            # FIXME if a filter is working with a string that was not converted
            # errors occur, the filters need a way to ignore, raise, or warn
            # apply tabs
            if self.rows and self.rows(res):
                res = res
            if self.columns:
                res = self.columns(res)

            filtered=res

            if filtered:
                fifo.put(filtered)

            if fifo.full():
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
    x = reader.read(skips=[35], chunksize=200000, escapechar=None, errors='warn')

    t0 = time.perf_counter()
    result = list(x)
    print(f'elapsed time: {time.perf_counter() - t0}')
