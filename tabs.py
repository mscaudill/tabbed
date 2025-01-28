"""A module for creating & tracking tabs along rows & columns of tabular data.

Tabs are callables that return a boolean indicating if a single column or row
should be returned or skipped. These callables are defined in the
Tabbed.utils.filters module and are automatically constructed for clients from
kwargs passed to the 'tab' method of a Columns or Rows instance.
"""

from collections import abc
from functools import partial
from functools import reduce
import operator as op
import re
from typing import Callable, Dict, List, Optional, Sequence

from tabbed.sniffing import Header, MetaData
from tabbed.utils import celltyping, filters
from tabbed.utils.celltyping import CellType
from tabbed.utils.filters import Comparable
from tabbed.utils.mixins import ReprMixin


class Columns(ReprMixin):
    """A Callable that sets & reads specific columns from tabular data.

    Tabular data is defined as a list of dicts of named data read by Python's
    csv.DictRreader class. This object tracks and reads specific columns of the
    data by applying a callable, the tabs attribute, to rows of data.

    Attributes:
        header:
            A dataclass containing column names, a subset of which can be set
            using the 'tab' method for reading.
        tabs:
            A callable the determines which columns of tabular data will be
            returned by this callable. A tab may be a Sequence of strings, ints
            or re.Pattern instance for selective filtering of the header column
            names.

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
        >>> columns(data)
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
        >>> columns(data)
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
        self._tabs: Optional[partial[bool]] = None

    @property
    def tabs(self) -> partial[bool] | None:
        """Return the tab function that will filter the tabular data columns."""

        return self._tabs

    @tabs.deleter
    def tabs(self) -> None:
        """On deletion, reset tabs to None."""

        self._tabs = None

    def tab(self, elements: Sequence[str | int] | re.Pattern) -> None:
        """Set the tab function that will filter the tabular data columns.

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

        if isinstance(elements, re.Pattern):
            # re search of header column names
            func = filters.search
            self._tabs = partial(func, row=self.header, other=elements)

        elif isinstance(elements[0], int):
            # index of header column names
            func = filters.index
            self._tabs = partial(func, other=elements)

        else:
            # membership of header column names
            if not set(self.header).issuperset(elements):
                invalid = set(elements).difference(self.header)
                raise IndexError(f'[{invalid}] are not a valid column name(s)')

            func = filters.membership
            self._tabs = partial(func, row=self.header, other=elements)

    def __call__(self, data: List[Dict[str, celltyping.CellType]]):
        """Reads the columns of data that have been tabbed by this instance.

        Args:
            data:
                A list of dicts, rows read by a csv.DictReader instance whose
                cells have already been type converted.

        Returns:
            A list of dicts containing only items whose names match the stored
            tab names of this instance.
        """

        if not self.tabs:
            return data

        # narrow type for mypy
        assert isinstance(self._tabs, partial)

        # get the tabbed names by calling tabs
        # pylint misses that tabs is a partial with a func member
        # pylint: disable-next = no-member
        if self.tabs.func.__name__ == 'index':
            h = list(self.header.keys())
            names = [h[idx] for idx in range(len(h)) if self._tabs(idx=idx)]
        else:
            names = [name for name in self.header if self._tabs(name=name)]

        # extract only whose name is in tabbed names
        result = []
        for row in data:
            result.append({name: row[name] for name in names})

        return result


class Rows(ReprMixin):
    """A Callable that sets & reads rows from tabular data.

    Tabular data is defined as a list of dicts of named data read by Python's
    csv.DictRreader class. This object tracks and reads specific rows of the
    data by applying a list of callables, the tabs attribute, to each row of
    data. These callables are defined in tabbed.utils.filters and are
    automatically set using the kwargs passed to this instance's 'tab' method.

    Attributes:
        tabs:
            A list of partial functions that accept only a dict representing
            a single row of tabular data. These filtering functions return
            a boolean indicating if the row should be included in the return.

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
        >>> # apply the tabs by calling the rows instance on data
        >>> row_results = rows(data)
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
        self._tabs: List = []

    @property
    def tabs(self) -> List[partial[bool]]:
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
                self._tabs.append(func)

            # equality
            elif isinstance(value, celltyping.CellType):
                func = partial(filters.equality, name=name, other=value)
                self._tabs.append(func)

            # regex
            elif filters.is_regex(value):
                func = partial(filters.search, name=name, other=value)
                self._tabs.append(func)

            # membership
            elif filters.is_sequence(value):
                func = partial(filters.membership, name=name, other=value)
                self._tabs.append(func)

            # indicator callable -mypy has problems with callable types
            elif isinstance(value, abc.Callable): # type: ignore[arg-type]
                # other will be required to be a func of a single variable
                func = partial(filters.indicator, name=name, other=value)
                self._tabs.append(func)

            else:
                msg = (
                    "Conversion of value into a comparison, equality, regex,"
                    f"membership or indicator test failed for column '{name}'"
                )
                raise TypeError(msg)

    def __call__(
        self,
        data: List[Dict[str, CellType]],
        logical: Callable[[Comparable, Comparable], bool] = op.and_,
    ) -> List[Dict[str, CellType]]:
        """Applies all of the row filter tabs to each dictionary row in data.

        Args:
            data:
                A list of dicts representing each row in data.
            logical:
                An callable that accepts two arguments to compare and returns
                a boolean. Defaults to Python's builtin operator and_.
        """

        if not self.tabs:
            return data

        results = []
        for row in data:
            if reduce(logical, [func(row) for func in self.tabs]):
                results.append(row)

        return results


if __name__ == '__main__':

    import doctest

    doctest.testmod()
