"""A collection of filters that all return a boolean indicating if a row passes
the filter.

"""

import re
from tabbed.utils import typings


def comparison(row, name, other):
    """Compares the named item in row dict with a string comparison.

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
    """

    operators = typings.rich_comparisons()
    name, val = re.split(r'\b', stringed, maxsplit=1)
    func = operators[name]

    # need to autoconvert val to int, float, complex, datetime or leave as str

    return func(row[name], val)
