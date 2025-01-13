"""A collection of functions that accept a row of data and return a boolean
indicator that the row meets a specific criterion.
"""

import re
import operator as op
from typing import Callable, Dict, Sequence
from tabbed.utils import tabtypes
from tabbed.utils.tabtypes import CellType, Comparable


def _singlecompare(row: Dict[str, CellType], name:str, other: str) -> bool:
    """Compares the named item in row dict with other, a string containing
    one rich comparison operator.

    This "protected" function not intended for external call.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for comparison with other.
        other:
            A string containing a comparison operator followed by an int, float,
            string, date, time or datetime (eg. '>=-12e6')

    Notes:
        This function supports comparisons between ints, floats, strings, dates,
        times and datetimes.

    Returns:
        True if row[name] compared against other is True and False otherwise.

    Raises:
        A TypeError is issued if the value in other is not a Comparable type.
    """

    operators = tabtypes.rich_comparisons()
    key, val = re.split(r'\b', other, maxsplit=1)
    operation = operators[key]
    value = tabtypes.convert(val)

    if not isinstance(value, Comparable):
        msg = f'type(other) must be a Comparable type not {type(val)}'
        raise TypeError(msg)

    return operation(row[name], value)


def _multicompare(row: Dict[str, CellType], name, other: str) -> bool:
    """Compares the named item in row dict with other, a string containing
    two rich comparison operators and a logical one of {and, or}.

    This "protected" function not intended for external call.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for comparison with other.
        other:
            A string containing two comparison operators sandwiching a logical
            (e.g. '>10 and <=87').

    Notes:
        This function supports comparisons between ints, floats, strings, dates,
        times and datetimes.

    Returns:
        True if row[name] compared against other is True and False otherwise.

    Raises:
        A ValueError is issued if the number of comparisons exceeds 2 in other.
    """

    logicals = {'and': op.__and__, 'or': op.__or__}

    # find first occurrence of a logical
    found = re.search(r'\sand\s|\sor\s', other).group()
    logical = logicals[found.strip()]
    # split on the logical
    comparisons = re.split(found, other)

    if len(comparisons) > 2:
        raise ValueError('A maximum of two comparisons may be made')

    results = [_singlecompare(row, name, cstring) for cstring in comparisons]

    return logical(*results)


def comparison(row: Dict[str, CellType], name: str, other: str) -> bool:
    """Compares the named item in row dict with other, a string containing
    one or two rich comparison operators.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for comparison with other.
        other:
            A string containing a comparison operator followed by an int, float,
            string, date, time or datetime (eg. '>=-12e6 and <= 0')

    Notes:
        This function supports comparisons between ints, floats, strings, dates,
        times and datetimes.

    Returns:
        True if row[name] compared against other is True and False otherwise.

    Raises:
        A TypeError is issued if the value component in other is not
        Comparable type; str, int, float or datetime.
    """

    multicomparison = re.search(r'\sand\s|\sor\s', other)
    if multicomparison:
        return _multicompare(row, name, other)
    else:
        return _singlecompare(row, name, other)


def search(row: Dict[str, CellType], name: str, other: re.Pattern) -> bool:
    """Searches a named item in row for other, a compiled regex pattern.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for regex search.
        other:
            A regex Pattern instance.

    Returns:
        True if row[name] contains other and False otherwise.
    """

    #return True if other.search(row[name]) else False
    return True if re.search(other, row[name]) else False


def equality(row: Dict[str, CellType], name: str, other: CellType) -> bool:
    """Compares the named item in row with other.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for comparison with other.
        other:
            A Comparable type; one of str, int, float, or datetime.

    Returns:
        True if row[name] equals other and False otherwise.
    """

    return row[name] == other


def membership(
    row: Dict[str, CellType],
    name: str,
    other: Sequence[CellType],
) -> bool:
    """Determines if named item in row is one of other.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for testing membership in other.
        other:
            A sequence of values for determining row[name]'s membership.

    Returns:
        True if row[name] is in other and False otherwise.
    """

    return row[name] in other


def indicator(
    row: Dict[str, CellType],
    name: str,
    other: Callable[[str], bool],
    **kwargs,
) -> bool:
    """Dispatches row and name to other callable that returns a boolean type.

    Args:
        row:
            A dict representation of a row of tabular data.
        name:
            The key of row to extract value for testing by other.
        other:
            A callable that accepts row[name] and returns a boolean.
        kwargs:
            Any valid kwarg for other.

    Returns:
        True if other(row[name], **kwargs) evaluates to True & False otherwise.

    """

    return other(row[name], **kwargs)


def index(idx: int,
    other: range | Sequence[int],
) -> bool:
    """Determines if integer row index is in other.

    Args:
        idx:
            The index of the dict representing a row of tabular data.
        other:
            A range instance or sequence of ints that must contain idx for the
            row to evaluate to True.

    Returns:
        True if idx in other and False otherwise.
    """

    return idx in other


if __name__ == '__main__':

    from datetime import datetime

    row = {'name': 'Canada', 'population': 1349,
           'founding': datetime.strptime('12/12/1798', '%m/%d/%Y')}

    x = comparison(row, 'population', '>10 and <10000')
    y = comparison(row, 'founding', '>7/4/1776 and <12/1/1998')
