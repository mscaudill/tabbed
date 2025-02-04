"""A module for creating tab instances, callables that return a boolean for
a single dictionary row indicating if the row should be accepted or rejected.
"""

import abc
from datetime import datetime
import operator as op
import re
from typing import Callable, Dict, List, Sequence

from tabbed.sniffing import Header
from tabbed.utils import celltyping
from tabbed.utils.celltyping import CellType
from tabbed.utils.mixins import ReprMixin

# Tabs are designed to be function-like and so have few public methods
# pylint: disable=too-few-public-methods

Comparable = int | float | datetime | str


class Tab(abc.ABC, ReprMixin):
    """Abstract base class declaring the required methods of all Tabs."""

    @abc.abstractmethod
    def __call__(self, row: Dict[str, CellType]) -> bool:
        """All Tabs implement a call method accepting a row dictionary."""


class Equality(Tab):
    """A Callable to test if a value in a dictionary row equals another value.

    Attributes:
        name:
            The item name in row dictionary whose value will be compared.
        matching:
            The value to compare against the named item in row dictionary.

    Example:
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
        """Initialize this tab.

        Args:
            name:
                The name of the item in the row dictionary to compare.
            matching:
                The value to compared named item in row dictionary against.

        Returns:
            None
        """

        self.name = name
        self.matching = matching

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a dictionary row.

        Args:
            row:
                A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            True if the named value in row equals this instances matching value
            and False otherwise.
        """

        return bool(row[self.name] == self.matching)


class Membership(Tab):
    """A Callable that test if a named item id a dictionary row belongs to
    a collection.

    Attributes:
        name:
            The named item in row dictionary whose value will be member tested.
        collection:
            A set to test named items membership against.

    Example:
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
        """Initialize this tab.

        Args:
            name:
                The named item in row dictionary whose value will be member tested.
            collection:
                A sequence to test named items membership against.

        Returns:
            None
        """

        self.name = name
        self.collection = set(collection)

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a dictionary row.

        Args:
            row:
                A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            True if the named value in row is in this instances collection.
        """

        return row[self.name] in self.collection


class Regex(Tab):
    """A Callable that test if a compiled re pattern is in the named item of
    a row dictionary.

    Attributes:
        name:
            The named item in row dictionary whose value will be pattern tested.
        pattern:
            A compiled regular expression pattern (see re.compile).

    Example:
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
        """Initialize this tab.

        Args:
            name:
               The named item in row dictionary whose value will be pattern tested.
            pattern:
                A compiled regular expression pattern (see re.compile).

        Returns:
            None
        """

        self.name = name
        self.pattern = pattern

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a dictionary row.

        Args:
            row:
               A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            True if pattern is in named value of row and False otherwise.
        """

        return bool(re.search(self.pattern, row[self.name]))


class Comparison(Tab):
    """A Callable that test if a named value in a row dictionary satisfies
    a comparison.

    Attributes:
        name:
            The named value in row dictionary to test with comparison.
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

    Example:
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

    comparators = dict(
        zip(
            '< > <= >= == !='.split(),
            [op.lt, op.gt, op.le, op.ge, op.eq, op.ne],
        )
    )

    def __init__(
        self,
        name: str,
        comparison: str,
        permissive: bool = True,
    ) -> None:
        """Initialize this tab instance.

        Args:
            name:
                The named value in row dictionary to test with comparison.
            comparison:
                A string containing one or two rich comparison operators
                followed by a Comparable type (e.g. '>= 8.3', '< 9 and > 2').
                The logical 'and' or 'or' may be used for double comparisons.
            permissive:
                A boolean indicating whether comparisons between mismatched
                types should result in the row being accepted (True) or rejected
                (False).

        Returns:
            None
        """

        self.name = name
        self.comparison = comparison
        self.permissive = permissive

    def _single(self, row: Dict[str, CellType], comparison: str) -> bool:
        """Determines if named value in row satisfies comparison.

        This "protected" function not intended for external call.

        Args:
            row:
               A mapping representing a dictionary row of an infile that has
                undergone type conversion.
            comparison:
                A string containing one or two rich comparison operators
                followed by a Comparable type (e.g. '>= 8.3', '< 9 and > 2').
                The logical 'and' or 'or' may be used for double comparisons.

        Returns:
            True if named value in row satisfies comparison.
        """

        # boundary split comparison to get value and comparator str
        comparator, value = re.split(r'\b', comparison, maxsplit=1)
        func = self.comparators[comparator.strip()]
        value = celltyping.convert(value)

        try:
            return bool(func(row[self.name], value))
        except TypeError:
            # comparisons between incompatible types -> return permissive
            return self.permissive

    def __call__(self, row: Dict[str, CellType]):
        """Apply this tab to a dictionary row.

        Args:
            row:
               A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            True if named value satisfies the condition.

        Raises:
            A ValueError is issued if more than two logicals are in comparison.
        """

        # determine if multi-comparison
        multicomparison = re.search(r'\sand\s|\sor\s', self.comparison)
        if multicomparison:

            logicals = {'and': op.__and__, 'or': op.__or__}
            # find occurrence of a logical string 'and' or 'or'
            match = re.search(r'\sand\s|\sor\s', self.comparison)
            # match cannot be None -- for mypy
            logic_string = match.group()  # type: ignore [union-attr]
            logical = logicals[logic_string.strip()]

            comparisons = re.split(logic_string, self.comparison)
            if len(comparisons) > 2:
                raise ValueError('A maximum of two comparisons may be made')

            booleans = [self._single(row, cstring) for cstring in comparisons]

            return logical(*booleans)

        return self._single(row, self.comparison)


class Calling(Tab):
    """A Callable that test if a named value in a row satisfies a boolean
    returning Callable.

    Attributes:
        name:
            The name of the row dictionary item to supply to func.
        func:
            A boolean returning callable that accepts a row, a name and any
            required kwargs in order.

    Example:
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
        """Initialize this tab instance.

        Args:
            name:
                The name of the row dictionary value to supply to func.
            func:
                A boolean returning callable that accepts (in order) a row
                dictionary, a name and any kwargs.

        Returns:
            None
        """

        self.name = name
        self.func = func
        self.kwargs = kwargs

    def __call__(self, row: Dict[str, CellType]) -> bool:
        """Apply this tab to a row dictionary.

        Args:
            row:
               A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            True if func returns True for this row and False otherwise.
        """

        return self.func(row, self.name, **self.kwargs)


class Columns(ReprMixin):
    """A Callable for reading a subset of a row's columns.

    This class, like tabs, is a callable that accepts a data row. However,
    it returns the row filtered by this instance's stored column names rather
    than a boolean.

    Attributes:
        header:
            A Header instance containing the names of each column in the
            delimited text file.

    Example:
        >>> # make tabular data
        >>> header = ['group', 'count', 'color']
        >>> group = ['a', 'c', 'b', 'b', 'c', 'a', 'c', 'b', 'c', 'a', 'a', 'c']
        >>> count = [22,   2,   13,  15,  4,   19,  4,   21,  5,   24,  18,  1]
        >>> color = 'r g b b r r r g g  b b g'.split()
        >>> items = zip(group, count, color)
        >>> data = [dict(zip(header, values)) for values in items]
        >>> # create a Columns selector
        >>> columns = Columns(Header(line=None, names=header, string=None))
        >>> # set the secret names list -- this will be controlled by readers
        >>> columns._names = [0, 2] #may be set by strings, ints or re.Pattern
        >>> #apply the named tabs
        >>> rows = [columns(row) for row in data]
        >>> print(rows[0:3])
        ... # doctest: +NORMALIZE_WHITESPACE
        [{'group': 'a', 'color': 'r'},
        {'group': 'c', 'color': 'g'},
        {'group': 'b', 'color': 'b'}]
    """

    def __init__(self, header: Header) -> None:
        """Initialize this Columns instance."""

        self.header = header
        self._names: List[str] = header.names

    def __setattr__(
        self,
        name: str,
        value: Sequence[str | int] | re.Pattern,
    ) -> None:
        """On set of names by sequence or re pattern, fetch names from
        this instance's header.

        Args:
            name:
                String name of the attribute of this object to set. Only _names
                attr is intercepted, all others delegate to supers setattr
                method.

        Raises:
            A TypeError is issued of the _names attribute is set to a value that
            is not a Sequence of strings, a Sequence of ints or an re Pattern
            instance.
        """

        vals = value
        if name == '_names':

            if not isinstance(value, (Sequence, re.Pattern)):
                msg = 'Value must be a Sequence[str|int] or re.Pattern type'
                raise TypeError(msg)

            if isinstance(value, Sequence):
                if len(set(type(el) for el in value)) > 1:
                    msg = 'All sequence elements must have the same type'
                    raise TypeError(msg)

            if isinstance(value, re.Pattern):
                pattern = value
                vals = [x for x in self.header.names if re.search(pattern, x)]

            assert isinstance(value, Sequence)  # mypy type narrow
            if isinstance(value[0], int):
                indices = value
                vals = [self.header.names[idx] for idx in indices]

            # validate others is a subset of header names
            assert isinstance(vals, Sequence)  # mypy type narrow
            invalid = set(vals).difference(self.header.names)
            if invalid:
                raise IndexError(f'[{invalid}] are not a valid column name(s)')

        super().__setattr__(name, vals)

    def __call__(self, row: Dict[str, CellType]) -> Dict[str, CellType]:
        """Apply Columns to a row dictionary.

        Args:
            row:
               A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            A new mapping containing only the named columns from this instance.
        """

        return {key: value for key, value in row.items() if key in self._names}


class Tabbing:
    """A callable container for storing & applying tab instances to rows
    and filtering by columns.

    Attributes:
        rows:
            A list of tab instances to apply to each row.
        columns:
            A Columns callable returning a new row containing only the named
            columns.
    """

    def __init__(self, rows: List[Tab], columns: Columns) -> None:
        """Initialize with tabs to apply to rows & columns to extract."""

        self.rows = rows
        self.columns = columns

    def __contains__(self, tab: Tab) -> bool:
        """Returns True if tab is in this tabbing else False."""

        return tab in self.rows

    def __call__(self, row: Dict[str, CellType]) -> Dict[str, CellType] | None:
        """Apply the tabs and columns to this row.

        Args:
            row:
               A mapping representing a dictionary row of an infile that has
                undergone type conversion.

        Returns:
            A new row containing only columns if the row satisfies the tabs and
            None otherwise.
        """

        return self.columns(row) if all(tab(row) for tab in self.rows) else None


if __name__ == '__main__':

    import doctest

    doctest.testmod()
