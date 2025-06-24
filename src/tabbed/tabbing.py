"""Tab instances are callables that return a boolean for a single row dictionary
to indicate if the row should be accepted or rejected. This module has equality,
membership, regular expression, rich comparison and custom callable Tabs. The
Tabulator is the client facing interface for building Tab instances. It allows
for Tab instances to be constructed from keyword arguments.
"""

import abc
from datetime import datetime
import operator as op
import re
from typing import Callable, cast, Dict, List, Literal, Optional, Sequence
import warnings

from typing_extensions import Self

from tabbed.sniffing import Header
from tabbed.utils import parsing
from tabbed.utils.mixins import ReprMixin
from tabbed.utils.parsing import CellType

# Tabs are designed to be function-like and so have few public methods
# pylint: disable=too-few-public-methods

Comparable = int | float | datetime | str


class Tab(abc.ABC, ReprMixin):
    """Abstract base class declaring required methods of all Tabs.

    A Tab is a callable that accepts a single row dictionary from an open file
    and returns a boolean indicating if the row should be accepted or rejected.
    Tabbed supports row evaluation using Equality, Membership, Re matching,
    numerical or date Comparison, and user specified Callables on the row's
    values. These types are the concrete implementations this abstract Tab.
    """

    @abc.abstractmethod
    def __call__(self, row: Dict[str, CellType]) -> bool:
        """All Tabs implement a call method accepting a row dictionary."""


class Equality(Tab):
    """A Tab to test if a value in a row dictionary equals another value.

    Attributes:
        name:
            The item name in row dictionary whose value will be compared.
        matching:
            The value to compare against the named item in row dictionary.

    Examples:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # make an Equality tab
        >>> tab = Equality('group', 'a')
        >>> # call the tab on the rows and print rows that match
        >>> results = [tab(row) for row in data]
        >>> print([idx for idx, boolean in enumerate(results) if boolean])
        [0, 5, 9, 10]
    """

    def __init__(self, name: str, matching: CellType) -> None:
        """Initialize this tab."""

        self.name = name
        self.matching = matching

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a row dictionary.

        Args:
            row:
                A row dictionary of a file whose values have been type casted.

        Returns:
            True if row's named value equals matching value and False otherwise.
        """

        return bool(row[self.name] == self.matching)


class Membership(Tab):
    """A Tab to test if a value in a row dictionary is a member of a collection.

    Attributes:
        name:
            The named value in row dict. to be member tested against collection.
        collection:
            A sequence of items for testing membership.

    Examples:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # make a membership tab
        >>> members = Membership('color', ['r', 'b'])
        >>> # call the tab on data and print matching rows
        >>> results = [members(row) for row in data]
        >>> print([idx for idx, boolean in enumerate(results) if boolean])
        [0, 2, 3, 4, 5, 6, 9, 10]
    """

    def __init__(self, name: str, collection: Sequence[CellType]) -> None:
        """Initialize this tab."""

        self.name = name
        self.collection = set(collection)

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a row dictionary.

        Args:
            row:
                A row dictionary of a file whose values have been type casted.

        Returns:
            True if named value in row is in collection.
        """

        return row[self.name] in self.collection


class Regex(Tab):
    """A Tab to test a compiled re pattern against a string value in a row dict.

    Attributes:
        name:
            The named value in row dictionary to be pattern tested.
        pattern:
            A compiled regular expression pattern (see re.compile).

    Examples:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # make a re pattern tab looking for a or c in group
        >>> regex = Regex('group', re.compile(r'a|c'))
        >>> #apply tab and find rows that match
        >>> booleans = [regex(row) for row in data]
        >>> print([idx for idx, boolean in enumerate(booleans) if boolean])
        [0, 1, 4, 5, 6, 8, 9, 10, 11]
    """

    def __init__(self, name: str, pattern: re.Pattern) -> None:
        """Initialize this tab."""

        self.name = name
        self.pattern = pattern

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a row dictionary.

        Args:
            row:
                A row dictionary of a file whose values have been type casted.

        Returns:
            True if pattern is found in named value of row & False otherwise.
        """

        # row[self.name] may not be str type but let re throw error to avoid
        # type checking every row of a file
        return bool(
            re.search(self.pattern, row[self.name])  # type: ignore [arg-type]
        )


class Comparison(Tab):
    """A Tab to test if named value in a row dictionary satisfies a comparison.

    Attributes:
        name:
            The named value in row dictionary to compare.
        comparison:
            A string containing one or two rich comparison operators followed by
            a Comparable type (e.g. '>= 8.3', '< 9 and > 2'). The logical 'and'
            or 'or' may be used for double comparisons.
        permissive:
            A boolean indicating whether comparisons between mismatched types
            should result in the row being accepted (True) or rejected (False).
            For example if row[name] = '-' and comparison requires row[name]
            > 3, permissive can accept or reject the row. The default value is
            True.

    Examples:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # make a comparison tab and apply it
        >>> comparison = Comparison('count', '>=4 and < 18')
        >>> booleans = [comparison(row) for row in data]
        >>> print([idx for idx, boolean in enumerate(booleans) if boolean])
        [2, 3, 4, 6, 8]
    """

    comparators = {
        '<': op.lt,
        '>': op.gt,
        '<=': op.le,
        '>=': op.ge,
        '==': op.eq,
        '!=': op.ne,
    }

    logicals = {'and': op.__and__, 'or': op.__or__}

    def __init__(
        self,
        name: str,
        comparison: str,
        permissive: bool = True,
    ) -> None:
        """Initialize this tab instance."""

        self.name = name
        self.comparison = comparison
        self.permissive = permissive
        self._funcs, self._values, self._logical = self._parse()

    def _singleparse(self, compare_str: str):
        """Parses a string containing a single comparison operator.

        This protected method should not be called externally.

        Args:
            A string with one comparison operator followed by a Comparable type.

        Returns:
            An operator module function & the casted comparing value.
        """

        # -? => 0 or 1 occurence of negative sign
        # \d* => 0 or more integer occurences
        # .? => 0 or 1 occurence of a decimal
        # \d+ => greedily get remaining integers
        idx = re.search(r'-?\d*\.?\d+', compare_str).span()[0]
        name, value_str = compare_str[:idx], compare_str[idx:]
        comparator = self.comparators[name.strip()]
        value = parsing.convert(value_str)

        return comparator, value

    def _parse(self):
        """Parses a comparison string with one or two rich comparisons.

        The steps to parsing a comparison string are; (1). splitting a comparison
        string on any logicals, (2). extracting the comparator functions, and (3).
        type casting the comparing value.

        This protected method should not be called externally.

        Returns:
            A tuple of comparators, a tuple of comparing values, and a logical.
            Logical will be None if comparison string contains a single
            comparison.

        Raises:
            A ValueError is issued if comparison contains more than two rich
            comparisons.
        """

        logical = None
        multicomparison = re.search(r'\sand\s|\sor\s', self.comparison)
        if multicomparison:
            # match cannot be None -- for mypy
            logic_string = multicomparison.group()  # type: ignore [union-attr]
            logical = self.logicals[logic_string.strip()]

            # get each string comparisons and get func, value components
            cstrings = re.split(logic_string, self.comparison)
            if len(cstrings) > 2:
                raise ValueError('A maximum of two comparisons may be made')

            items = [self._singleparse(compare_str) for compare_str in cstrings]
            funcs, values = zip(*items)
        else:
            funcs, values = zip(*[self._singleparse(self.comparison)])

        return funcs, values, logical

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a row dictionary.

        Args:
            row:
                A row dictionary of a file whose values have been type casted.

        Returns:
            True if named value satisfies the comparison(s).

        Raises:
            ValueError: is issued if more than two logicals are in comparison.
        """

        try:

            booleans = []
            for func, val in zip(self._funcs, self._values):
                booleans.append(func(row[self.name], val))

            if self._logical:
                # combine multicomparison with logical
                return bool(self._logical(*booleans))

            return bool(booleans[0])

        except TypeError:
            # comparisons between incompatible types -> return permissive
            return self.permissive


class Calling(Tab):
    """A Tab to test if named value in a row satisfies a boolean function.

    Attributes:
        name:
            The name of the row dictionary item to supply to func.
        func:
            A boolean returning callable that accepts a row, a name and any
            required kwargs in that order.

    Examples:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # make a callable that determines if values are even
        >>> def is_even(row, name):
        ...     return row[name] % 2 == 0
        >>> calling = Calling('count', is_even)
        >>> # apply the tab and print rows that are even
        >>> booleans = [calling(row) for row in data]
        >>> print([idx for idx, boolean in enumerate(booleans) if boolean])
        [0, 1, 4, 6, 9, 10]
    """

    def __init__(
        self,
        name: str,
        func: Callable[[Dict[str, CellType], str], bool],
        **kwargs,
    ) -> None:
        """Initialize this tab instance."""

        self.name = name
        self.func = func
        self.kwargs = kwargs

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a row dictionary.

        Args:
            row:
                A row dictionary of a file whose values have been type casted.

        Returns:
            True if func returns True for this row and False otherwise.
        """

        return self.func(row, self.name, **self.kwargs)


class Accepting(Tab):
    """A Tab that returns True for any row dictionary.

    This Tab defines what to do with a row when no tabs are present.

    Examples:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # make Accepting tab
        >>> accepting = Accepting(x='twiddle', y='dee')
        >>> # apply the accepting tab to data
        >>> booleans = [accepting(row) for row in data]
        >>> print([idx for idx, val in enumerate(booleans) if val])
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    """

    def __init__(self, **kwargs):
        """Initialize this Tab."""

        self.__dict__.update(kwargs)

    def __call__(self, row: Dict[str, CellType]) -> Literal[True]:
        """Returns True for a row dictionary always."""

        return True


class Tabulator(ReprMixin):
    """A Callable for creating, storing & applying Tabs to a row dictionary.

    Tablulators are the interface that should be used to create Tab instances.
    They allow Tabs to be constructed from keyword arguments and apply multiple
    Tabs sequentially to a row dictionary of file data. If columns from the file
    are provided, the Tabulator will restrict which columns of the row
    dictionary will be returned.

    Attributes:
        header:
            A Header instance storing all column names of a file.
        tabs:
            A list of tab instances to apply to each row.
        columns:
            Columns to extract from each row as a list of column names, a list
            of integer column indices or a single re pattern to match column
            names against.

    Examples:
        >>> # make tabular data
        >>> names = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(names, values)) for values in items]
        >>> #create a Header instance
        >>> header = Header(line=0, names=names, string=''.join(names))
        >>> # create a tabulator from keyword args defining tabs
        >>> tabulator = Tabulator.from_keywords(
        ... header,
        ... columns=[0, 1],
        ... group=['a', 'c'],
        ... count='<=20')
        >>> # show the tab types tabulator will use
        >>> print([type(tab).__name__ for tab in tabulator.tabs])
        ['Membership', 'Comparison']
        >>> # apply the tabulator to get the same rows
        >>> rows = [tabulator(row) for row in data if tabulator(row)]
        >>> print(rows)
        ... # doctest: +NORMALIZE_WHITESPACE
        [{'group': 'c', 'count': 2},
        {'group': 'c', 'count': 4},
        {'group': 'a', 'count': 19},
        {'group': 'c', 'count': 4},
        {'group': 'c', 'count': 5},
        {'group': 'a', 'count': 18},
        {'group': 'c', 'count': 1}]
    """

    def __init__(
        self,
        header: Header,
        tabs: Optional[List[Tab]] = None,
        columns: Optional[List[str] | List[int] | re.Pattern] = None,
    ) -> None:
        """Initialize with tabs, columns to extract & Header instance."""

        self.header = header
        self.tabs = tabs if tabs else [Accepting()]
        self.columns = self._assign(columns) if columns else self.header.names

    def _assign(self, value: List[str] | List[int] | re.Pattern):
        """Assigns the passed column value(s) to valid column names.

        Args:
            value:
                A list of column string names, a list of column indices, or
                a single re pattern to match against names in header

        Returns:
            A list of column names.

        Raises:
            A ValueError is issued if value is not a list of strings, a list of
            ints or an re Pattern.
        """

        if isinstance(value, re.Pattern):
            return [x for x in self.header.names if re.search(value, x)]

        if all(isinstance(val, int) for val in value):
            # cast for mypy to know value is list of ints
            value = cast(List[int], value)
            result = [self.header.names[val] for val in value]

        elif all(isinstance(val, str) for val in value):
            # cast for mypy to know value is list of strs
            value = cast(List[str], value)
            result = value

        else:
            msg = (
                'Columns must be a sequence of ints, a sequence of strings, '
                'or a compiled re pattern.'
            )
            raise ValueError(msg)

        invalid = set(result).difference(self.header.names)
        if any(invalid):
            msg = f'Invalid name(s): {invalid} are being ignored.'
            warnings.warn(msg)
            result = [el for el in result if el not in invalid]

        return result

    # define a static method for a classmethod without instant access
    # pylint: disable-next=no-self-argument
    def _from_keyword(  # type: ignore [misc]
        name: str,
        value: (
            str
            | CellType
            | Sequence[CellType]
            | re.Pattern
            | Callable[[Dict[str, CellType], str], bool]
        ),
    ) -> Tab:
        """Returns a Tab instance from the name, value kwarg pair.

        This is a protected static method that aides the alternative
        from_keywords constructor. It should not be externally called.

        Args:
            name:
                The column name to provide to a Tab constructor.
            value:
                A value to provide to a Tab constructor.

        Returns:
            A Tab instance.
        """

        rich_comparisons = '< > <= >= == !='.split()

        if isinstance(value, str):
            if any(compare in value for compare in rich_comparisons):
                return Comparison(name, value)

            return Equality(name, value)

        if isinstance(value, CellType):
            # non-string CellType value -> make equality tab
            return Equality(name, value)

        if isinstance(value, Sequence):
            return Membership(name, value)

        if isinstance(value, re.Pattern):
            return Regex(name, value)

        if callable(value):
            return Calling(name, value)

        msg = f'Invalid value type {type(value)} in keyword argument'
        raise TypeError(msg)

    @classmethod
    def from_keywords(
        cls,
        header: Header,
        columns: Optional[List[str] | List[int] | re.Pattern] = None,
        **kwargs: (
            CellType
            | Sequence[CellType]
            | re.Pattern
            | Callable[[Dict[str, CellType], str], bool]
        ),
    ) -> Self:
        """Alternative instance constructor using keyword args to define Tabs.

        Args:
            header:
                A Header type containing the names of all the columns in infile.
            columns:
                Columns to extract from each row as a list of column names, a list
                of integer column indices or a single re pattern to match column
                names against.
            kwargs:
                A mapping of column names and values to convert to Tab
                instances (e.g. 'group' = ['a', 'b'], 'count' = '<=20', ...)

        Returns:
            A Tabulator instance
        """

        tabs = [cls._from_keyword(*item) for item in kwargs.items()]
        return cls(header, tabs, columns)

    def __call__(self, row: Dict[str, CellType]) -> Dict[str, CellType] | None:
        """Apply Tab instances and column filter to this row.

        Args:
            row:
                A row dictionary of a file whose values have been type casted.

        Returns:
            A row dictionary or None if row does not satisfy all tabs.
        """

        if all(tab(row) for tab in self.tabs):
            return {key: val for key, val in row.items() if key in self.columns}

        return None


if __name__ == '__main__':

    import doctest

    doctest.testmod()
