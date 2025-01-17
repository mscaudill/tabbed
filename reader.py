"""

"""

import csv
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

    # need to work out how to pass no header and no metadata 
    def __init__(
        self,
        infile,
        dialect = None,
        **kwargs,
        ) -> None:
        """ """

        self.infile = infile
        self.sniffer = Sniffer(self.infile, **kwargs)
        self._header = self.sniffer.Header()

    @property
    def header(self):
        """" """

        return self._header

    @header.setter
    def header(self, value: int | List[str] | None):
        """ """

        column_count = len(self.sniffer.rows[-1])
        if isinstance(value, int):
            # the index here should be wrt 0 top of infile
            # need to check value is in sniffer start + amount
            self._header = Header(self.sniffer.rows[value], value)

        if isinstance(value, List):
            # need to check that its size seems right
            if len(value) != column_count:
                msg = (f'The number of columns {len(value)} does not match the'
                      f'inferred number of columns is {column_count}')
                raise ValueError(msg)

            self._header = Header(value, None)

        if value is None:
            # generate a list of column names
            h = Header([f'Column_{i}' for i in range(column_count)], None)
            self._header = h

        raise TypeError('Header names must be type int, List[str], or None not'
                        f'{type(value)}')



    def __len__(self):
        """ """

        return self.sniffer.line_count


if __name__ == '__main__':

    fp = '/home/matt/python/nri/tabbed/__data__/fly_sample.txt'

    with open(fp, 'r') as infile:
        reader = Reader(infile)
        reader.sniffer.skips = [35]
        print(reader.sniffer.has_header())
        for idx, row in enumerate(reader.sniffer.rows()):
            print(idx, row)



