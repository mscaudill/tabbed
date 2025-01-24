"""

"""

import csv
from collections import abc
from itertools import islice
from typing import List

from tabbed import tabs
from tabbed.sniffer import Sniffer
from tabbed.utils.celltyping import convert
from tabbed.utils.containers import Header, Meta

# Planning
#
# 1. __init__ should take an open file instance to allow for readers to be
#    initialized with and without context management
# 2. reader should have a 'peek' or show method to show a sample of what will be
#    read in a nice format
# 3. reader should have an index method which will add a client named index to
#    the rows prior to filters to allow for row index filtering
# 4. reader will need to do auto type conversion using celltyping.convert
# 5. reader should store the sniffed metadata and header
# 6. reader will embedd a Rows and Columns instance for tab setting
# 7. reader's read method should support chunk interation of rows that yield
#    consistent sizes after filtering FIFO
# 8. Reader is the main type in Tabbed and should be available at package level
#    with no imports
# 9. Reader should have a sample method to show lines and indices to aid setting
#    specific numbers like count etc. Could call the method 'lines'
#
# Questions:
# 1. should we sniff file for header and metadata before constructing this
#    reader or try to sniff during reader initialization?
#    Pros of before:
#    a. The most versatile as it will make no assumptions about the sample used
#       to determine the dialect, the metadata and the header
#    Cons of before:
#    a. Users the would need to know how to use sniffers prior to reading
#    SOLN: we will sniff during reader initialization
#


class Reader:
    """ """
 
    def __init__(
        self,
        infile,
        dialect = None,
        **kwargs,
        ) -> None:
        """ """

        self.infile = infile
        self.sniffer = Sniffer(self.infile, **kwargs)
        self._header = self.sniffer.header
        # intercept sniff attr setting to update this reader's header
        self._set_sniff()
        self._columns = None
        self._rows = None

    def _set_sniff(self) -> None:
        """On update of a Sniffer attribute, update this readers header.

        Monkey patches Sniffer's __setattr__ method in order to update this
        Reader's header whenever our embedded sniffer instance changes.
        """

        def on_change(sniffer, name, value):
            """A replacement for Sniffer's __setattr__."""

            super(Sniffer, sniffer).__setattr__(name, value)
            self._header = sniffer.header

        Sniffer.__setattr__ = on_change

    @property
    def header(self) -> Header | None:
        """Returns the header from this reader's infile if it exist.

        Returns:
            A namedtuple of header names & a file line number if existant.
        """

        item = self._header
        return item() if isinstance(item, abc.Callable) else item

    @header.setter
    def header(self, value: int | List[str] | str) -> None:
        """Set the header of this reader.

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

            # TODO you'll need to sanitize each header here so pull sanitation
            # out of sniffer to a utils func to be recalled 
            # new sniffer to sniff single row at value
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

    def tab(self, columns=None, **rows):
        """ """

        if columns:
            ctabs = tabs.Columns(self.header.names)
            ctabs.tab(columns)
            self._columns = ctabs

        if rows:
            rtabs = tabs.Rows(self.header.names)
            rtabs.tab(**rows)
            self._rows = rtabs


    def read(self, start=None, skips=None, chunksize=None, **fmtparams):
        """ """

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

