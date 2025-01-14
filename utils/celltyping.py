"""A module for detecting & converting strs to python intrinsic types."""

from collections import abc
from datetime import datetime
import itertools
import operator
from typing import Any, Callable, Dict, List, NewType, Optional

import re

# define the supported intrinsic types for each list element read by Tabbed
CellType = int | float | complex | datetime | str
Comparable = int | float | datetime | str


def rich_comparisons() -> Dict[str, Callable[[Comparable, Comparable], bool]]:
    """Returns a dict of Python's rich comparison operators organized by their
    string representation."""

    strings = '< > <= >= == !='.split()
    funcs = [getattr(operator, x) for x in 'lt gt le ge eq ne'.split()]
    return dict(zip(strings, funcs))


def date_formats() -> List[str]:
    """Creates commonly used date format specifiers.

    This function returns many common date formats but not all. As new formats
    are encountered this function should be modified to detect more.

    Returns:
        A list of date formats specifiers for datetime's strptime method.
    """

    months, separators, years = 'mbB', ' /-.', 'Yy'
    fmts = []
    for mth, sep, yr in itertools.product(months, separators, years):
        # build month and day first fmts
        x = [f'%{mth}{sep}%d{sep}%{yr}', f'%d{sep}%{mth}{sep}%{yr}']
        fmts.extend(x)

    return fmts


def time_formats() -> List[str]:
    """Creates commonly used time format specifiers.

    This function returns many common time formats but not all. As new formats
    are encountered this function should be modified.

    Returns:
        A list of time format specifiers for datetime's strptime method.
    """

    fmts = []
    hours, microsecs, diurnal = ['I', 'H'], ['', ':%f', '.%f'], ['', '%p']
    for hrs, micro, di in itertools.product(hours, microsecs, diurnal):
        fmts.append(f'%{hrs}:%M:%S{micro}{di}')

    return fmts


def datetime_formats() -> List[str]:
    """Creates commonly used datetime format specifiers.

    This function returns many common datetime formats but not all. As new
    formats are encountered the functions date_formats and time_formats should
    be modified.

    Returns:
        A list of datetime formats specifiers for datetime's strptime method.
    """

    dates, times = date_formats(), time_formats()
    fmts = []
    for date, time in itertools.product(dates, times):
        fmts.append(' '.join([date, time]))

    return fmts


def find_format(astring: str, formats: List[str]) -> str | None:
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


def is_numeric(astring: str) -> bool:
    """Test if astring is a stringed numeric.

    Args:
        A string that possibly represents a numeric type.

    Returns:
        True if astring can be converted to any type in {int, float, complex}.
    """

    try:
        complex(astring)
        return True
    except (ValueError, OverflowError):
        return False


def is_regex(item: Any) -> bool:
    """Test if item is a compiled regular expression pattern.

    Args:
        item:
            Object to test if compiled regex.

    Returns:
        True if item is instance of re.Pattern and False otherwise.
    """

    return isinstance(item, re.Pattern)


def is_comparison(astring: str) -> bool:
    """Test if astring contains any rich comparisons.

    This method is susceptible to False positives since strings may contain rich
    comparison notation without an actual comparison intended.

    Args:
        astring:
            A string that possibly contains a rich comparison.

    Returns:
        True if astring contains no more than count rich comparisons.
    """

    # comparisons are always string type
    if not isinstance(astring, str):
        return False

    # remove all spaces
    x = ''.join(astring.split())
    found = [key for key in rich_comparisons() if key in x]

    return bool(found)


def is_sequence(item: Any) -> bool:
    """Test if item is Sequence type.

    Args:
        item:
            Object to test if Sequence type.

    Returns:
        True if item is Sequence type and False otherwise.
    """

    return isinstance(item, abc.Sequence)


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


def is_time(astring: str) -> bool:
    """Test if astring represents a time.

    Args:
        astring:
            A string that possibly represents a time.

    Returns:
        True if astring can be converted to a datetime and False otherwise.
    """

    # another method to time detect without fmt testing could give speedup
    fmt = find_format(astring, time_formats())
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


# conversion stops on first success so allow multi-returns
# pylint: disable-next=too-many-return-statements
def convert(
    astring: str,
    func: Optional[Callable[..., CellType]] = None,
    **kwargs,
) -> CellType:
    """Attempts to convert a string to a valid Cell type.

    Tabbed supports string conversion of each row's elements to the following types:
    str, int, float, complex, datetime. These are the valid Cell types.

    Args:
        astring:
            A string that possibly represents a CellType, one of int, float,
            complex, datetime or string.
        func:
            A callable for performing conversion that must accept at least
            astring and return a CellType. If provided, this callable
            supersedes any autoconversion.
        kwargs:
            All keyword arguments are passed to func if provided and ignored
            otherwise.

    Returns:
        A CellType

    Raises:
        Convert raises no Errors but silently leaves astring as a string type.
    """

    # give the converter a try if provided
    if func:
        try:
            return func(astring, **kwargs)

        # catch any exception raised by generic func and keep trying
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            msg = str(e) + ' ... attempting autoconversion'
            print(msg)

    # numeric
    if is_numeric(astring):

        # look for imag part for complex
        if re.findall(r'[ij]', astring):
            return complex(astring)

        # look for a decimal
        if re.findall(r'\.', astring):
            return float(astring)

        return int(astring)

    # datetimes - use asserts for mypy type narrowing
    if is_date(astring):
        fmt = find_format(astring, date_formats())
        assert isinstance(fmt, str)
        return datetime.strptime(astring, fmt)

    if is_time(astring):
        fmt = find_format(astring, time_formats())
        assert isinstance(fmt, str)
        return datetime.strptime(astring, fmt)

    if is_datetime(astring):
        # perform this datetime last since it has many fmts to test
        fmt = find_format(astring, datetime_formats())
        assert isinstance(fmt, str)
        return datetime.strptime(astring, fmt)

    return astring
