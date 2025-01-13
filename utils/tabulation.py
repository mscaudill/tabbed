"""

"""

import operator as op
from collections import abc
from functools import partial, reduce
import re

from typing import Callable, Dict, List, Sequence
from datetime import datetime

from tabbed.utils import tabtypes, filters
from tabbed.utils.mixins import ReprMixin


class Columns(abc.Callable, ReprMixin):
    """A callable that sets & reads column names from tabular data.

    Tabular data is defined as a list of dicts of named data read by Python's
    csv.DictRreader class. This object tracks and reads specific column names,
    called tabs, from this data.

    Attributes:
        header:
            A dict of all possible column names, a subset of which can be set
            using the 'set' method for reading.
        tabs:
            The subset of column names of header this Callable is set to read.
    """

    def __init__(self, header: List[str]) -> None:
        """Initialize this Columns' instance with a header.

        Args:
            header:
                A list of all possible column names in a tabular dataset.

        Returns:
            None
        """

        self.header = header
        self._header = dict(zip(header, header))
        self._tabs = header


    @property
    def tabs(self) -> List[str]:
        """Return the column names to be read."""

        return self._tabs


    @tabs.deleter
    def tabs(self) -> None:
        """On deletion, reset tabs to all names in header."""

        self._tabs = self.header


    def _membership(self, others: List[str]) -> List[str]:
        """Sets tabs to read using a membership filter.

        Args:
            other:
                A list of name tabs. The intersection of this list with the
                header names will be returned.

        Returns:
            An others lengthed list of string column names.

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
        """Sets tabs to read by indexing this instance's header.

        Args:
            indices:
                Indices of the header names to store to this instance.

        Returns:
            A indices lengthed list of string column names.

        Raises:
            An IndexError is issued if any index exceeds headers length.
        """

        return [self.header[idx] for idx in indices]


    def _regex(self, pattern: re.Pattern) -> List[str]:
        """Sets tabs to read by re pattern matching with this instance's
        header.

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


    def tab(self, tabs: Sequence[str|int] | re.Pattern) -> None:
        """Set the tabs this instance will read from tabular data.

        Args:
            tabs:
                A sequence of strings, integers or a single re pattern denoting
                the column names to read. If a sequence of ints, header names
                with matching indices will be stored for reading, if a sequence
                of strings, header names that string match will be stored for
                reading and if a compiled re pattern, all header names
                containing pattern will be stored for reading.

        Returns:
            None
        """

        if isinstance(tabs, re.Pattern):
            result = self._regex(tabs)

        elif isinstance(tabs[0], int):
            result = self._index(tabs)

        else:
            result = self._membership(tabs)

        self._tabs = result


    def __call__(self, data: List[Dict[str, tabtypes.CellType]]):
        """Reads the data for each name stored in this instance.

        Args:
            data:
                A list of dicts, rows read by a csv.DictReader instance whose
                cells have already been type converted.

        Returns:
            A list of dicts containing only items whose names match the stored
            tab names of this instance.
        """

        result = []
        for row in data:
            result.append({name: row[name] for name in self.tabs})

        return result


class Rows(abc.Callable, ReprMixin):
    """A callable that sets & reads rows from tabular data.

    Tabular data is defined as a list of dicts of named data read by Python's
    csv.DictRreader class. This object tracks partial functions each of which
    accepts a dictionary row & returns a boolean indicating if the row should be part
    of the return. The partial functions can perform membership test, comparison
    test, re pattern match tests, equality test or run a custom callable test.

    Attributes:
        tabs:
            A list of partial functions that accept only a dict representing
            a single row of tabular data. These filtering functions return
            a boolean indicating if the row should be included in the return.
 """

    def __init__(self, header: List[str]):
        """Initialize this Rows instance with a header of column names."""

        self.header = header
        self._tabs = []


    @property
    def tabs(self) -> List[Callable]:
        """Returns a list of filtering functions determining row inclusion."""

        return self._tabs


    @tabs.deleter
    def tabs(self) -> None:
        """On deletion, return tabs to an empty list."""

        self._tabs = []


    def tab(
        self,
        **kwargs: Dict[
                    str,
                    CellType|Sequence[CellType]|re.Pattern|Callable[dict, bool]],
        ) -> None:
        """Sets a tab, a boolean filter that will be applied to each row of
        tabular data.

        Args:
            kwargs:
                A valid header column name and a value matching one of:
                - A CellType such as a str, int, float, complex, or datetime.
                  Values of this kind trigger an equality comparison of row[name]
                  with value.
                - A string containing up to 2 rich comparison operators sepearated
                  by a single logical and/or operator (eg.  '>10 and <100'.
                  Values of this kind trigger comparison with row[name].
                - A Sequence of CellType (e.g. ['a' ,'b']). This value triggers
                  a membership test of row[name] in value.
                - A compiled re Pattern instance (e.g. re.compile(r'a|b')). Values
                  of this kind trigger an re search of row[name] for pattern.
                - A callable that takes the dict row as the only parameter and
                  returns a boolean. Partial should be used to freeze all other
                  arguments.

        Returns:
            None

        Raises:
            A ValueError is issued if a column name key in keyword arguments is
            not in the tabular data's header.
        """

        if not set(kwargs).issubset(self.header):
            invalid = set(kwargs).difference(self.header)
            msg = f'{invalid} is not a column of this dataset.'
            raise ValueError(msg)

        for name, value in kwargs.items():

            # comparison
            if tabtypes.is_comparison(value):
                func = partial(filters.comparison, name=name, other=value)
                self._tabs.append(func)

            # equality
            elif isinstance(value, tabtypes.CellType):
                func = partial(filters.equality, name=name, other=value)
                self._tabs.append(func)

            # regex
            elif tabtypes.is_regex(value):
                func = partial(filters.search, name=name, other=value)
                self._tabs.append(func)

            # membership
            elif tabtypes.is_sequence(value):
                func = partial(filters.membership, name=name, other=value)
                self._tabs.append(func)

            # indicator callable
            elif isinstance(value, Callable):
               # other will be required to be a func of a single variable
               func = partial(filters.indicator(name=name, other=other))
               self._tabs.append(func)

            else:
                msg = ("Conversion of value into a comparison, equality, regex,
                        membership or indicator test failed for column '{name}'")
                raise TypeError(msg)


    def __call__(
        self,
        data,
        logical: Callable[[Comparable, Comparable], bool] = op.and_,
        ) -> List[Dict[str, CellType]]:
        """Applies all of the row filter tabs to each dictionary row in data
        and reduces the result to a single boolean with logical.

        Args:
            data:
                A list of dicts representing each row in data.
            logical:
                An callable that accepts two arguments to compare and returns
                a boolean. Defaults to Python's builtin operator and_.
        """

        if not tabs:
            return data

        results = []
        for row in data:
            if reduce(logical, [func(row) for func in self.tabs]):
                results.append(row)

        return results



if __name__ == '__main__':

    table = [['Genotype', 'marbles', 'color', 'stype'],
             ['WT', 10, 'k', 1],
             ['WT', 11, 'g', 1],
             ['wt', 8, 'b', 1.2],
             ['mut', 0, 'g', 1.0],
             ['MUT', 2, 'g', 3],
             ['MUT', 1, 'g', 3],
             ['MUT', 4, 'g', 3],
            ]

    header = table[0]
    data = [dict(zip(table[0], ls)) for ls in table[1:]]

    """
    columns = Columns(table[0])
    columns.tab(tabs=[0, 1,3])
    print(columns.tabs)

    pattern = re.compile(r'stype|mar|col')
    columns.tab(pattern)
    print(columns.tabs)

    columns.tab(['Genotype', 'marbles', 'color'])
    print(columns.tabs)

    filtered = columns(data)
    """

    rows = Rows()
    rows.tab(Genotype=['WT', 'MUT'], marbles='>1 and <=10',
            color=re.compile(r'g|b'), stype=3)
    results = rows(data)

