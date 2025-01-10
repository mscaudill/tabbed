"""

"""

import operator as op
from collections import abc
from functools import partial
import re

from typing import Callable, Dict, List, Sequence
from datetime import datetime

from tabbed.utils import tabtypes, filters
from tabbed.mixins import ReprMixin


class ColumnTabs(abc.Container, ReprMixin):
    """A Container for setting & storing a subset of column names.

    Attributes:
        header:
            A dict of all possible column names from which a subset of named
            columns may be set using the Column's set method.
        names:
            The subset of columns this Container is storing.
    """

    def __init__(self, header: List[str]) -> None:
        """Initialize this Columns instance with a header.

        Args:
            header:
                A list of all possible column names in a tabular dataset.

        Returns:
            None
        """

        self.header = header
        self._header = dict(zip(header, header))
        self._names = header


    # TODO for consistency maybe rename names to columns
    @property
    def names(self) -> List[str]:
        """Return the currently stored column names."""

        return self._names


    @names.deleter
    def names(self) -> None:
        """On column names deletion, reset names to all names in header."""

        self._names = self.header


    def _membership(self, others: List[str]) -> List[str]:
        """Sets the currently stored names using the membership filter.

        Args:
            other:
                A list of names. The intersection of this list with the header
                names will be returned.

        Returns:
            A list of strings, the intersection between other and this
            instance's header.

        Raises:
            An IndexError is issued if any string in other is not in header.
        """

        if not set(self.header).issuperset(others):
            invalid = set(other).difference(header)
            raise IndexError(f'[{invalid}] are not a valid column name(s)')

        func = partial(filters.membership, row=self._header, other=others)
        result = [name for name in self.header if func(name=name)]

        return result


    def _index(self, indices: List[int]) -> List[str]:
        """Sets the currently stored names by index selection from header.

        Args:
            indices:
                A list of integer indices of header names to use as Columns'
                stored names.

        Returns:
            A list of strings, the header names at each index in indices.

        Raises:
            An IndexError is issued if any index in indices is not less than
            header's length.
        """

        return [self.header[idx] for idx in indices]


    def _regex(self, pattern: re.Pattern) -> List[str]:
        """Sets the currently stored names by regular expression matching.

        Args:
            pattern:
                A compiled regular expression pattern, an re.Pattern instance.
                Each name in header will be searched for this pattern and stored
                if a match is found.

        Returns:
            A list of strings, header names in which pattern is found. If no
            matches are found an empty list is returned.
        """

        func = partial(filters.search, row=self._header, other=pattern)
        result = [name for name in self.header if func(name=name)]

        return result


    def set(self, tabs: Sequence[str|int] | re.Pattern) -> None:
        """Set the header column names this Column's instance should manage.

        Args:
            tabs:
                A sequence or regular expression pattern to mark header names
                for storage. If a sequence of ints, header names with matching
                indices will be stored, if a sequence of strings, header names
                that match will be stored and if a compiled re pattern all
                header names containing pattern will be stored.

        Returns:
            None
        """

        if isinstance(tab, re.Pattern):
            result = self._regex(tabs)

        elif isinstance(tabs[0], int):
            result = self._index(tabs)

        else:
            result = self._membership(tabs)

        self._names = result


    def __contains__(self, name):
        """Test name for membership in this Columns' names."""

        return name in self.names


class RowTabs(abc.Container, ReprMixin):
    """ """

    def __init__(self, header: List[str]):
        """ """

        self.header = header
        self._header = dict(zip(header, header))
        self._rows = []
        self.comparators = []

    @property
    def rows(self) -> List[Callable]:
        """ """

        return self._rows


    @rows.deleter
    def rows(self) -> None:
        """ """

        self._rows = []
        self.comparators = []


    def set(self, comparators=op.and_, **kwargs):
        """ """

        # membership
        # comparison
        # regex
        # equality
        # indicator
        # index










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
        self.columns = Columns(header)
        self._rows = dict()
        self._comparators = None


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

    """
    tabs = Tabs(header=table[0])
    #tabs.set_columns = ['marbles', regex('type')]
    tabs.set_rows(('marbles', '>=2'), Genotype=['WT', 'MUT'])
    tabs.set_rows(stype=1, color=['k', 'b', 'g'])
    result = tabs(table[1:])
    """

    columns = Columns(table[0])
    columns.set(tabs=[0, 1,3])
    print(columns.names)

    pattern = re.compile(r'stype|mar|col')
    columns.set(pattern)
    print(columns.names)

    columns.set(['Genotype', 'marbles', 'color'])
    print(columns.names)

