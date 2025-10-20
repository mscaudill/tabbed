"""A module for detecting & converting strings to python types supported by
Tabbed. These tools are wrapped by the `convert` function which dispatches
a string to a type specific convert callable.
"""

import itertools
import re
import string
from collections import Counter
from datetime import date, datetime, time

# define the supported intrinsic types for each list element read by Tabbed
CellType = int | float | complex | time | date | datetime | str
CellTypes = list[type[CellType]]


def time_formats() -> list[str]:
    """Creates commonly used time format specifiers.

    This function returns many common time formats but not all. As new formats
    are encountered this function should be modified.

    Returns:
        A list of time format specifiers for datetime's strptime method.
    """

    fmts = []
    hours, microsecs = ['I', 'H'], ['', ':%f', '.%f']
    diurnal = '%p'
    for hrs, micro in itertools.product(hours, microsecs):
        if hrs == 'I':
            # If 12 hour clock allow for possible space before am/pm
            fmts.append(f'%{hrs}:%M:%S{micro}{diurnal}')
            fmts.append(f'%{hrs}:%M:%S{micro} {diurnal}')
        else:
            fmts.append(f'%{hrs}:%M:%S{micro}')

    return fmts


def date_formats() -> list[str]:
    """Creates commonly used date format specifiers.

    This function returns many common date formats but not all. As new formats
    are encountered this function should be modified to detect more.

    Returns:
        A list of date formats specifiers for datetime's strptime method.
    """

    months, separators, years = 'mbB', ' /-.', 'Yy'
    fmts = []
    for mth, sep, yr in itertools.product(months, separators, years):
        # currently support year without century in last position only
        # future vers will support 1st position year without century but sniffer
        # datetime_formats will need to disambiguate %m from %y in 1st pos.
        x = [
            f'%{mth}{sep}%d{sep}%{yr}',
            f'%d{sep}%{mth}{sep}%{yr}',
            f'%Y{sep}%{mth}{sep}%d',
        ]

        fmts.extend(x)

    return fmts


def datetime_formats() -> list[str]:
    """Creates commonly used datetime format specifiers.

    This function returns many common datetime formats but not all. As new
    formats are encountered the functions date_formats and time_formats should
    be modified.

    Returns:
        A list of datetime formats specifiers for datetime's strptime method.
    """

    datefmts, timefmts = date_formats(), time_formats()
    fmts = []
    for datefmt, timefmt in itertools.product(datefmts, timefmts):
        fmts.append(' '.join([datefmt, timefmt]))

    return fmts


def find_format(astring: str, formats: list[str]) -> str | None:
    """Returns the date, time, or datetime format of astring.

    Args:
        astring:
            A string instance that possibly represents a date, a time, or
            a datetime.
        formats:
            A list of formats to try to convert astring with. See date_formats,
            time_formats and datetime_formats functions of this module.

    Returns:
        A format string or None.
    """

    for fmt in formats:
        try:
            datetime.strptime(astring, fmt)
            return fmt
        except ValueError:
            continue

    return None


def is_numeric(astring: str, decimal: str) -> bool:
    """Test if astring is a stringed numeric.

    Args:
        astring:
            A string that possibly represents a numeric type.
        decimal:
            A string representing the decimal notation.

    Returns:
        True if astring can be converted to any type in {int, float, complex}.
    """

    if decimal != '.':
        astring = astring.replace(decimal, '.')

    try:
        complex(astring)
        return True
    except (ValueError, OverflowError):
        return False


def is_time(astring: str) -> bool:
    """Test if astring represents a time.

    Args:
        astring:
            A string that possibly represents a time.

    Returns:
        True if astring can be converted to a datetime and False otherwise.
    """

    # all times contain 2 ':' separators
    if Counter(astring)[':'] < 2:
        return False

    # another method to time detect without fmt testing could give speedup
    fmt = find_format(astring, time_formats())
    return bool(fmt)


def is_date(astring: str) -> bool:
    """Test if astring represents a date.

    Args:
        astring:
            A string instance that possibly represents a datetime instance.

    Returns:
        True if astring can be converted to a datetime and False otherwise.
    """

    # another method to date detect without fmt testing could give speedup
    fmt = find_format(astring, date_formats())
    return bool(fmt)


def is_datetime(astring: str) -> bool:
    """Test if astring represents a datetime.

    Args:
        astring:
            A string that possibly represents a datetime.

    Returns:
        True if astring can be converted to a datetime and False otherwise.
    """

    # another method to datetime detect without fmt testing could give speedup
    fmt = find_format(astring, datetime_formats())
    return bool(fmt)


def as_numeric(astring: str, decimal: str) -> int | float | complex | str:
    """Converts astring representing a numeric into an int, float or complex.

    Args:
        astring:
            A string that represents a numeric type.
        decimal:
            A string representing the decimal notation.

    Returns:
        A numeric type but on conversion failure returns input string.
    """

    if decimal != '.':
        astring = astring.replace(decimal, '.')

    # look for imag part for complex
    if re.findall(r'[ij]', astring):
        return complex(astring)

    # look for a decimal
    if re.findall(r'\.', astring):
        return float(astring)

    try:
        return int(astring)
    except ValueError:
        return astring


def as_time(astring: str, fmt: str) -> time | str:
    """Converts astring representing a time into a datetime time instance.

    Args:
        astring:
            A string representing a time.

    Returns:
        A datetime.time instance or astring on conversion failure
    """

    try:
        return datetime.strptime(astring, fmt).time()
    except ValueError:
        return astring


def as_date(astring: str, fmt: str) -> date | str:
    """Converts astring representing a date into a datetime date instance.

    Args:
        astring:
            A string representing a date.

    Returns:
        A datetime.date instance or astring on conversion failure
    """

    try:
        return datetime.strptime(astring, fmt).date()
    except ValueError:
        return astring


def as_datetime(astring: str, fmt: str) -> datetime | str:
    """Converts astring representing datetime into a datetime instance.

    Args:
        astring:
            A string representing a datetime.

    Returns:
        A datetime instance or astring on conversion failure
    """

    try:
        return datetime.strptime(astring, fmt)
    except ValueError:
        return astring


# conversion stops on first success so allow multi-returns
# pylint: disable-next=too-many-return-statements
def convert(
    astring: str,
    decimal: str = '.',
    celltype: type[CellType] | None = None,
    fmt: str | None = None,
) -> CellType:
    """Attempts to convert a string to a valid Cell type.

    Tabbed supports string conversion of each row's elements to the following types:

        - str
        - int
        - float
        - complex
        - time
        - date
        - datetime

    Args:
        astring:
            A string that possibly represents a CellType, one of int, float,
            complex, datetime or string.
        decimal:
            A string that represents the decimal notation for numeric types.
        celltype:
            A CellType callable class, one of int, float, complex, str, time,
            date or datetime. If None, automatic and slower conversion of
            astring will be attempted.
        fmt:
            A datetime format required by time, date and datetime celltypes. If
            None, automatic conversion of astring will be attempted.

    Returns:
        A CellType

    Raises:
        ValueError: if celltype is provided and conversion fails.
    """

    if celltype and fmt:
        adatetime = datetime.strptime(astring, fmt)
        if celltype == datetime:
            return adatetime
        # avoid instance assertions for speed here
        # we know this should be a date or time instance
        return getattr(  # type: ignore[no-any-return]
            adatetime, celltype.__name__
        )()

    # replace decimal notation with dot notation
    if celltype in {float, complex, int}:
        try:
            return celltype(astring)  # type: ignore[call-arg, arg-type]
        except ValueError:
            astring = astring.replace(decimal, '.')
            return celltype(astring)  # type: ignore[call-arg, arg-type]

    if celltype == str:
        return astring

    # numeric
    if is_numeric(astring, decimal):
        return as_numeric(astring, decimal)

    # simple string a subset of ascii
    if set(astring.lower()).issubset(string.ascii_letters):
        return astring

    # times,dates, datetimes - use asserts for mypy type narrowing
    if is_time(astring):
        fmt = find_format(astring, time_formats())
        assert isinstance(fmt, str)
        return as_time(astring, fmt)

    if is_date(astring):
        fmt = find_format(astring, date_formats())
        assert isinstance(fmt, str)
        return as_date(astring, fmt)

    if is_datetime(astring):
        # perform datetime last since it has many fmts to test
        fmt = find_format(astring, datetime_formats())
        assert isinstance(fmt, str)
        return as_datetime(astring, fmt)

    return astring
