"""

"""

import operator as op
from collections import abc
from functools import partial
import regex as re

from datetime import datetime

from tabbed.utils import typings

def regex(pattern):
    """ """

    try:
        raw = r'{}'.format(pattern)
        return re.compile(raw)
    except exception as e:
        msg = f"Pattern '{pattern}' could not be compiled to a valid regex"
        raise ValueError(msg) from e


####################3 TODO protocols
def rich_compare(row, name, expression )-> bool:
    """row is a dict keyed on header names

    """

    methods = comparisons()
    loc = re.search(r'[+-\d.eE]+', expression).start()
    comparator, val = methods[expression[:loc]], expression[loc:]
    # if numeric convert and return partial
    val = float(val) if is_numeric(val) else val

    return comparator(row[name], val)


def regex_compare(row, name, expression) -> bool:
    """row is a dict keyed on header names """

    return True if re.search(row[name], expression) else False


def is_equal(row, name, expression):
    """row is a dict keyed on header names."""

    value = float(expression) if is_numeric(expression) else expression
    return op.eq(row[name], expression)

def is_in(row, name, expression):
    """ """

    return row[name] in expression:q


###########################################################################

class Tabulator:
    """A callable that coordinates the reading of specific rows and columns from
    tabular data.

    Attrs:
        header:
            A sequence of string names for each column in data.

    """

    def __init__(self, header: List[str]):
        """Initialize this Tabulator with a header."""

        self.header = header
        self._columns = self.header
        self._rows = dict()
        self._comparators = None


    @property
    def columns(self) -> List[str]:
        """Return the columns this Tabulator will return when called."""

        return self._columns


    @columns.deleter
    def columns(self) -> None:
        """Sets columns this Tabulator will return to all columns in header."""

        self._columns = self.header


    @property
    def rows(self) -> Dict[[str, Callable], bool]:
        """Returns a dict of column names and partial functions that Tabulator
        will apply to each row in data when called."""

        return self._rows


    @rows.deleter
    def rows(self):
        """Sets rows this Tabulator will return to all rows in data."""

        self._rows = dict()
        self._comparators = None


    def set_columns(self, names: List[str|re.Pattern]) -> None:
        """Sets the columns this Tabulator will return when called.

        Args:
            names:
                A list of strings or regular expression patterns to match
                against header columns for selective column reading.

        Returns:
            None

        Raises:
            An IndexError if a name in names does not match a name in header.
        """

        result = []
        for name in names:

            if isinstance(name, str):
                # raises index error if name not in header
                idx = self.header.index(name)
                result.append(self.header[idx])

            elif isinstance(name, re.Pattern):
                matches = [re.search(name, col) for col in self.header]
                # verify name pattern matches at least one header column
                if not any(matches):
                    msg = (f"Pattern '{name}' does not match with any header"
                            "column")
                    raise IndexError(msg)

                # find all header matches
                cols = [self.header[idx] for idx, m in enumerate(matches) if m]
                result.extend(cols)

            else:
                msg = 'Columns must be str or re.Pattern type'
                raise TypeError(msg)

        self._columns = result


    def set_rows(self, *args, comparators=op.and_, **kwargs):
        """ """

        self._rows = dict()

        comparisons = dict()
        comparisons.update(dict(args))
        comparisons.update(kwargs)
        for name, expression in comparisons.items():

            if typings.is_comparison(expression):
                func = partial(rich_compare, name=name, expression=expression)
                self._rows.update({name: func})

            elif typings.is_regex(expression):
                func = partial(regex_compare, name=name, expression=expression)
                self._rows.update({name: func})

            elif is_datetime(expression):
                pass

            elif is_sequence(expression):
                func = partial(is_in, name=name, expression=expression)
                self._rows.update({name: func})

            #elif is_callable(expression):
            #    pass

            else:
                func = partial(is_equal, name=name, expression=expression)
                self._rows.update({name: func})


    def __call__(self, lines):
        """ """

        result = []
        for line in lines:
            include = [True] * len(self.rows)
            for name, func in self.rows.items():
                include.append(func(dict(zip(self.header, line))))
    
            if all(include):
                result.append(line)

        return result



if __name__ == '__main__':

    table = [['Genotype', 'marbles', 'color', 'stype'],
             ['WT', 10, 'k', 1],
             ['wT', 8, 'b', 1.2],
             ['Mut', 0, 'g', 1.0],
             ['MUT', 2, 'g', 3],
             ]

    tabs = Tabs(header=table[0])
    #tabs.set_columns = ['marbles', regex('type')]
    tabs.set_rows(('marbles', '>=2'), Genotype=['WT', 'MUT'])
    tabs.set_rows(stype=1, color=['k', 'b', 'g'])
    result = tabs(table[1:])

