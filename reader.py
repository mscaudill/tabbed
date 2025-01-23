"""

"""

import csv
from collections import abc
from typing import List

from tabbed.sniffer import Sniffer
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
        self._intercept()

    def _intercept(self) -> None:
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
            A Header namedtuple containing header names and the row number of
            the header line in infile or None.
        """

        item = self._header
        return item() if isinstance(item, abc.Callable) else item

    @header.setter
    def header(self, value: int | List[str] | str ):
        """ """

        column_count = len(self.sniffer.rows()[-1])
        if isinstance(value, int):

            # build a new sniffer that reads only value row
            # if value exceeds line count the last row is the header
            sniffer = Sniffer(self.infile, start=value, amount=1)
            self._header = Header(sniffer.rows()[0], value)

        elif isinstance(value, List):
            if len(value) != column_count:
                msg = (f'The number of columns {len(value)} does not match the'
                      f'inferred number of columns is {column_count}')
                raise ValueError(msg)

            self._header = Header(value, None)

        elif isinstance(value, str):
            valid = ['generate', 'sniff']
            val = value.lower()
            if val not in valid:
                msg = f"unexpected string value {value} must be one of {valid}"
                raise ValueError(msg)

            if val == 'generate':
                # generate a list of column names
                h = Header([f'Column_{i}' for i in range(column_count)], None)
                self._header = h
            else:
                self._header = self.sniffer.header

        else:
            raise TypeError('Header names must be type int, List[str], or str'
                            f'not {type(value)}'
                            )



    def __len__(self):
        """ """

        return self._sniffer.line_count


if __name__ == '__main__':

    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)
    print(reader.header)



    """
    reader.header = 'auto'
    print(reader.header)

    reader.header = 34
    print(reader.header)

    reader.sniffer.skips=[35]
    """

