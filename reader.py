"""

"""

import csv
from collections import abc
from itertools import islice
from typing import List

from tabbed import tabs
from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.utils.queues import ListFIFO
from tabbed.utils.celltyping import CellType, convert

# Planning
#
# 2. reader should have a 'peek' or show method to show a sample of what will be
#    read in a nice format
# 3. reader should have an index method which will add a client named index to
#    the rows prior to filters to allow for row index filtering
# 4. reader will need to do auto type conversion using celltyping.convert
# 6. reader will embedd a Rows and Columns instance for tab setting
# 7. reader's read method should support chunk interation of rows that yield
#    consistent sizes after filtering FIFO
# 8. Reader is the main type in Tabbed and should be available at package level
#    with no imports
# 9. Reader should have a sample method to show lines and indices to aid setting
#    specific numbers like count etc. Could call the method 'lines'


class Reader:
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
        self._columns = None
        self._rows = None

    def _set_sniff(self) -> None:
        """On update of a Sniffer attribute, update this readers header.

        Monkey patches Sniffer's __setattr__ method in order to update this
        Reader's header whenever the embedded sniffer instance changes. This
        protected method should not be externally called.
        """

        def on_change(sniffer, name, value):
            """A replacement for Sniffer's __setattr__."""

            super(Sniffer, sniffer).__setattr__(name, value)
            self.header = sniffer.header

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

        # on header change delete tabs
        del self.rows
        del self.columns

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

    @property
    def columns(self):
        """Returns the column tabs this reader will apply during reading."""

        return self._columns

    @columns.deleter
    def columns(self):
        """Deletion of column tabs sets them to None."""

        self._columns = None

    @property
    def rows(self):
        """Returns the row tabs this reader will apply during reading."""

        return self._rows

    @rows.deleter
    def rows(self):
        """Deletion of row tabs sets them to None."""

        self._rows = None

    def tab(
        self,
        columns: Optional[List[str|int] | re.Pattern] = None,
        **rows: dict[
            str,
            CellType | Sequence[CellType] | re.Pattern | Callable],
        ):
        """Sets the rows or columns that will be read by this Reader during a
        read method call.

        Args:
            columns:
                A list of column names, column indices or regular expression
                pattern to match column names. These columns will be the ones
                returned. If None, all columns will be returned.
            **rows:
                A mapping of column names and one of; CellType, list of
                Celltype, a compiled re pattern, a rich comparison or
                a callable.

        Returns:
            None
        """

        if columns:
            ctabs = tabs.Columns(self.header.names)
            ctabs.tab(columns)
            self._columns = ctabs

        if rows:
            rtabs = tabs.Rows(self.header.names)
            rtabs.tab(**rows)
            self._rows = rtabs

    def read(
        self,
        start=None,
        skips=None,
        chunksize=None,
        index_name='index',
        **fmtparams,
        ):
        """ """

        if start is None:
            start = self.header.line + 1 if self.header.line else 0

        skips = [] if not skips else skips
        chunksize = len(self) if not chunksize else chunksize
        # advance to the data section
        [next(self.infile) for _ in range(start))
        dictreader = csv.DictReader(
                    infile,
                    self.header,
                    restkey=None,
                    restval='',
                    dialect = self.sniffer.dialect, **fmtparams)

        # TODO could update with custom converters if desired
        converters = dict(zip(self.header, self.sniffer.types))
        fifo = ListFIFO()
        for line, dic in enumerate(dictreader, start):
            if line in skips:
                continue

            unnamed = dic.pop(None)
            converted = {name: converters[name](dic[name]) for name in dic}
            converted.ins({index_name: line})
            self._header.names.append(index_name) # this may be a problem frozen
            filtered = self.rows(converted)
            filtered = self.columns(filtered)
        
            if filtered:
                # TODO FIFO will need to change since we place dict into it not
                # list
                fifo.put(filtered)






    def _read(self, start=None, skips=None, chunksize=None, **fmtparams):
        """ """


        # To avoid dealing with infile yourself due to seperators at line
        # endings you could just let DictReader do it and ignore the restkey
        # remainder

        if start is None:
            start = self.header.index+1 if self.header.index else 0

        skips = [] if not skips else skips

        [next(self.infile) for _ in range(start)]


        sep = fmtparams.get('delimiter', self.sniffer.dialect.delimiter)
        results = []
        for num, line in enumerate(islice(self.infile, 0, 10000), start):

            if num in skips:
                continue

            # need to wrap below in a try block and decide if you will raise or
            # just warn about lines that had problems, this probably should be
            # a parameter?

            try:
                # lines may end in delimiter leading to empty trailing cells
                stripped = line.rstrip(sep)
                row = stripped.split(sep)
                # remove any double quotes
                row = [astring.replace('"', '') for astring in row]
                dic = dict(zip(self.header.names, row))

                # perform type conversion
                dic = {name: convert(val) for name, val in dic.items()}

                # apply the row tabs -- expecting list of dics
                result = self.rows([dic]) if self.rows else [dic]
                # apply the col tabs
                result = self.columns(result) if self.columns else result

                if result: # some rows will not survive tabs
                    results.append(result)
            except:
                print(num, line)
                continue

        return results


    def preview(self):
        """ """

        pass

    def close(self):
        """ """

        self.infile.close()

    def __len__(self):
        """ """

        return self._sniffer.line_count


if __name__ == '__main__':

    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)
    print(reader.header)

    # FIXME Trial time column shows we need to sanitize header by subs spaces in
    # names -- where should this occur? Sniffer?
    reader.tab(columns=['Trial_time', 'X_center', 'Y_center', 'Area'])
    reader.tab(Area='>0.025 and <0.03', Trial_time='>0')
    x = reader.read(skips=[35])



    """
    reader.header = 'auto'
    print(reader.header)

    reader.header = 34
    print(reader.header)

    reader.sniffer.skips=[35]
    """

