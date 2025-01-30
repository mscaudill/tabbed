"""A module for creating & tracking tabs along rows & columns of tabular data.

Tabs are callables or booleans indicating if a single column or row should be
returned or skipped. These callables are defined in the Tabbed.utils.filters
module and are automatically constructed for clients from kwargs passed to the
'tab' method of a Columns or Rows instance.
"""

from collections import abc
from functools import partial
from functools import reduce
import operator as op
import re
from typing import Callable, Dict, List, Sequence

from tabbed.sniffing import Header
from tabbed.utils import celltyping
from tabbed.utils import filters
from tabbed.utils.celltyping import CellType
from tabbed.utils.filters import Comparable
from tabbed.utils.mixins import ReprMixin


class Columns(ReprMixin):
    """A Callable that reads specific columns from a dictionary row of delimited
    text file.

    Attributes:
        tabs:
            A dictionary of column names and booleans to indicate which columns
            to return from a row.

    Example:
        >>> # make some tabular data
        >>> header = ['group', 'count', 'color', 'temp']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> temp =  [33.5, 40.1, 29, 22, 20, 19.34, 50.0, 11.09, 11, 12, 11, 13]
        >>> # simulate rows of data arriving from a csv.DictReader instance
        >>> data = [
        ... dict(zip(header, items)) for items in zip(group, count, color, temp)
        ... ]
        >>> # make a columns instance
        >>> columns = Columns(Header(line=None, names=header, string=None))
        >>> # set tabs on columns to read just group and color
        >>> columns.tab(['group', 'color'])
        >>> [columns(row) for row in data]
        ... #doctest: +NORMALIZE_WHITESPACE
        [{'group': 'a', 'color': 'r'},
         {'group': 'c', 'color': 'g'},
         {'group': 'b', 'color': 'b'},
         {'group': 'b', 'color': 'b'},
         {'group': 'c', 'color': 'r'},
         {'group': 'a', 'color': 'r'},
         {'group': 'c', 'color': 'r'},
         {'group': 'b', 'color': 'g'},
         {'group': 'c', 'color': 'g'},
         {'group': 'a', 'color': 'b'},
         {'group': 'a', 'color': 'b'},
         {'group': 'c', 'color': 'g'}]
        >>> # delete the tabs and call again
        >>> del columns.tabs
        >>> [columns(row) for row in data]
        ... #doctest: +NORMALIZE_WHITESPACE
        [{'group': 'a', 'count': 22, 'color': 'r', 'temp': 33.5},
         {'group': 'c', 'count': 2,  'color': 'g', 'temp': 40.1},
         {'group': 'b', 'count': 13, 'color': 'b', 'temp': 29},
         {'group': 'b', 'count': 15, 'color': 'b', 'temp': 22},
         {'group': 'c', 'count': 4,  'color': 'r', 'temp': 20},
         {'group': 'a', 'count': 19, 'color': 'r', 'temp': 19.34},
         {'group': 'c', 'count': 4,  'color': 'r', 'temp': 50.0},
         {'group': 'b', 'count': 21, 'color': 'g', 'temp': 11.09},
         {'group': 'c', 'count': 5,  'color': 'g', 'temp': 11},
         {'group': 'a', 'count': 24, 'color': 'b', 'temp': 12},
         {'group': 'a', 'count': 18, 'color': 'b', 'temp': 11},
         {'group': 'c', 'count': 1,  'color': 'g', 'temp': 13}]
    """

    def __init__(self, header: Header) -> None:
        """Initialize this Columns' instance with a Header instance.

        Args:
            header:
                A Header immmutable dataclass instance (see tabbed.sniffing).

        Returns:
            None
        """

        self.header = dict(zip(header.names, header.names))
        self._tabs: Dict[str, bool]

    @property
    def tabs(self) -> Dict[str, bool]:
        """Return the tab that will filter each dictionary row."""

        return self._tabs

    @tabs.deleter
    def tabs(self) -> None:
        """On deletion, reset tabs to an empty dict."""

        self._tabs = {}

    def tab(self, elements: Sequence[str | int] | re.Pattern) -> None:
        """Set the tab function that will filter each dictionary row.

        Args:
            elements:
                A sequence of strings, integers or a single re pattern
                determining the column names to read. If a sequence of ints,
                header names with matching indices will be stored for reading,
                if a sequence of strings, header names that string match will be
                stored for reading and if a compiled re pattern, all header
                names containing pattern will be stored for reading.

        Returns:
            None

        Raises:
            A TypeError is issued if elements is not a Sequence or re.Pattern
            An IndexError is issued of elements is a sequence of strings with at
            least one element not in the header.
        """

        if not isinstance(elements, (Sequence, re.Pattern)):
            msg = 'Tab elements must be a Sequence or re.Pattern type'
            raise TypeError(msg)

        choose: List[str] = []
        if isinstance(elements, re.Pattern):
            # convert re pattern matching to membership
            func = partial(filters.search, row=self.header, other=elements)
            choose = [name for name in self.header if func(name=name)]

        elif all(isinstance(el, int) for el in elements):
            # convert indexing to a membership and we know type is ints
            names = list(self.header)
            choose = [names[el] for el in elements]  # type: ignore

        elif all(isinstance(el, str) for el in elements):
            # we were given membership and we know type is strings
            choose = elements  # type: ignore

        else:
            msg = 'Tabs must be a sequence of strings, ints or an re.Pattern'
            raise ValueError(msg)

        # validate the elements are a subset of the header names
        if not set(self.header).issuperset(choose):
            invalid = set(choose).difference(self.header)
            raise IndexError(f'[{invalid}] are not a valid column name(s)')

        func = partial(filters.membership, row=self.header, other=choose)
        self._tabs = {name: func(name=name) for name in self.header}

    def __call__(self, row: Dict[str, CellType]) -> Dict[str, CellType]:
        """Reads columns of a dictionary row that satisfy this instances tabs.

        Args:
            row:
                A dictionary row read by a csv.DictReader whose cells have been
                type converted.

        Returns:
            A dict containing only items whose names match satisfy tabs.
        """

        if not self.tabs:
            return row

        # extract only tabbed names
        return {name: value for name, value in row.items() if self._tabs[name]}


class Rows(ReprMixin):
    """A Callable determining whether a dictionary row satisfies a set of
    equality, membership, regex or rich comparison conditions.

    Attributes:
        tabs:
            A mapping of columns names to partial functions. Each partial
            accepts only a row of data and returns a boolean indicating if that
            row should be accepted.

    Example:
        >>> from datetime import datetime, timedelta
        >>> # make tabular data
        >>> header = ['group', 'count', 'color', 'temp', 'time']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> temp =  [33.5, 40.1, 29, 22, 20, 19.34, 50.0, 11.09, 11, 12, 11, 13]
        >>> time = [
        ... datetime(2025, 1, 14, 10, 12, 13) + timedelta(seconds=10*i)
        ... for i in range(12)
        ... ]
        >>> # simulate rows of data arriving from a csv.DictReader instance
        >>> data = [
        ... dict(zip(header, items)) for items in
        ... zip(group, count, color, temp, time)
        ... ]
        >>> # build a rows instance
        >>> rows = Rows(Header(line=0, names=header, string=None))
        >>> # tab rows with group a or c, time < 10:14:00, and count in (0, 10)
        >>> rows.tab(
        ... group=re.compile(r'a|c'), time='<01-14-2025 10:14:00', count=range(10)
        ... )
        >>> # apply the tabs by calling rows tab's on each row of data
        >>> row_results = [row for row in data if rows(row)]
        >>> row_results
        ... #doctest: +NORMALIZE_WHITESPACE
        [{'group': 'c',
          'count': 2,
          'color': 'g',
          'temp': 40.1,
          'time': datetime.datetime(2025, 1, 14, 10, 12, 23)},
         {'group': 'c',
          'count': 4,
          'color': 'r',
          'temp': 20,
          'time': datetime.datetime(2025, 1, 14, 10, 12, 53)},
         {'group': 'c',
          'count': 4,
          'color': 'r',
          'temp': 50.0,
          'time': datetime.datetime(2025, 1, 14, 10, 13, 13)},
         {'group': 'c',
          'count': 5,
          'color': 'g',
          'temp': 11,
          'time': datetime.datetime(2025, 1, 14, 10, 13, 33)}]
    """

    def __init__(self, header: Header) -> None:
        """Initialize this Rows instance with a Header instance.

        Args:
            header:
                An immutable Header dataclass instance (see tabbed.sniffing).
        """

        self.header = header.names
        self._tabs: Dict[str, partial[bool]] = {}

    @property
    def tabs(self) -> Dict[str, partial[bool]]:
        """Returns a list of filtering functions determining row inclusion."""

        return self._tabs

    @tabs.deleter
    def tabs(self) -> None:
        """On deletion, return tabs to an empty dict."""

        self._tabs = {}

    def tab(
        self,
        **kwargs: Dict[
            str,
            CellType | Sequence[CellType] | re.Pattern | Callable,
        ],
    ) -> None:
        """Sets a tab, a boolean filter that will be applied to each row of
        tabular data.

        Args:
            kwargs:
                A valid header column name and a value matching one of:
                - A CellType such as a str, int, float, complex, or datetime.
                  Values of this kind trigger an equality comparison of row[name]
                  with value.
                - A string containing up to 2 rich comparison operators separated
                  by a single logical and/or operator (eg.  '>10 and <100').
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

            # comparison is a subset of equality when value type is str
            if filters.is_comparison(value):
                func = partial(filters.comparison, name=name, other=value)
                self._tabs[name] = func

            # equality
            elif isinstance(value, celltyping.CellType):
                func = partial(filters.equality, name=name, other=value)
                self._tabs[name] = func

            # regex
            elif filters.is_regex(value):
                func = partial(filters.search, name=name, other=value)
                self._tabs[name] = func

            # membership
            elif filters.is_sequence(value):
                func = partial(filters.membership, name=name, other=value)
                self._tabs[name] = func

            # indicator callable -mypy has problems with callable types
            elif isinstance(value, abc.Callable):  # type: ignore[arg-type]
                # other will be required to be a func of a single variable
                func = partial(filters.indicator, name=name, other=value)
                self._tabs[name] = func

            else:
                msg = (
                    "Conversion of value into a comparison, equality, regex,"
                    f"membership or indicator test failed for column '{name}'"
                )
                raise TypeError(msg)

    def __call__(
        self,
        row: Dict[str, CellType],
        logical: Callable[[Comparable, Comparable], bool] = op.and_,
    ) -> bool:
        """Applies all of the row filter tabs to each dictionary row in data.

        Args:
            row:
                A dicts representing a row returned by csv.DictReader that has
                been type converted.
            logical:
                An callable that accepts two arguments to compare and returns
                a boolean. Defaults to Python's builtin operator and_.

        Returns:
            True if the row meets the logical combination of tab filters.
        """

        if self.tabs:
            return reduce(logical, [func(row) for func in self.tabs.values()])

        return True


if __name__ == '__main__':

    import doctest

    doctest.testmod()
