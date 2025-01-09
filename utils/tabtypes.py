"""A module for detecting & converting strs to python intrinsic types."""

import operator
import regex
from typing import Any, Dict, List
from collections import abc
import itertools
from datetime import datetime


def rich_comparisons() -> Dict:
    """Returns a dict of Python's rich comparison operators organized by their
    string representation."""

    strings = '< > <= >= == !='.split()
    funcs = [getattr(operator, x) for x in 'lt gt le ge eq neq'.split()]
    return dict(zip(strings, funcs))


def date_formats() -> List:
    """Creates commonly used date format specifiers.

    This function returns many common date formats but not all. As new formats
    are encountered this function should be modified to detect more.

    Returns:
        A list of date formats specifiers for datetime's strptime method.
    """

    months, seperators, years = 'mbB', ' /-.', 'yY'
    fmts = []
    for mth, sep, yr in itertools.product(months, seperators, years):
        # build month and day first fmts
        x = [f'%{mth}{sep}%d{sep}%{yr}', f'%d{sep}%{mth}{sep}%{yr}']
        fmts.extend(x)

    return fmts


def time_formats() -> List:
    """Creates commonly used time format specifiers.

    This function returns many common time formats but not all. As new formats
    are encountered this function should be modified.

    Returns:
        A list of time format specifiers for datetime's strptime method.
    """

    hrs, microsecs, diurnal = ['I', 'H'], ['', ':%f',  '.%f'], ['', '%p']
    fmts = []
    for hrs, micro, di in itertools.product(hrs, microsecs, diurnal):
        fmts.append(f'%{hrs}:%M:%S{micro}{di}')

    return fmts


def datetime_formats() -> List:
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
    except:
        return False


def is_regex(item: Any) -> bool:
    """Test if item is a compiled regular expression pattern.

    Args:
        item:
            Object to test if compiled regex.

    Returns:
        True if item is instance of re.Pattern and False otherwise.
    """

    return isinstance(item, regex.Pattern)


def is_comparison(astring: str, count=1) -> bool:
    """Test if astring contains any rich comparisons.

    This method is susceptible to False positives since strings may contain rich
    comparison notation without an actual comparison intended. The count kwarg
    may be used to reject astring if it contains more than count comparisons.

    Args:
        astring:
            A string that possibly contains a rich comparison.
        count:
            The maximum number of rich comparisons allowed in astring before it
            is declared to contain None. This can eliminate strings like <...>
            from consideration.

    Returns:
        True if astring contains no more than count rich comparisons.
    """

    found = [key for key in rich_comparisons() if key in astring]
    if found > count:
        return False

    return True if found else False


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

    for fmt in date_formats():
        try:
            datetime.strptime(astring, fmt)
            return fmt
        except ValueError:
            continue

    return None


def is_time(astring: str) -> bool:
    """Test if astring represents a time.

    Args:
        astring:
            A string that possibly represents a time.

    Returns:
        True if astring can be converted to a datetime and False otherwise.
    """

    for fmt in time_formats():
        try:
            datetime.strptime(astring, fmt)
            return fmt
        except ValueError:
            continue

    return None


def is_datetime(astring: str) -> bool:
    """Test if astring represents a datetime.

    Args:
        astring:
            A string that possibly represents a datetime.

    Returns:
        True if astring can be converted to a datetime and False otherwise.
    """

    for fmt in datetime_formats():
        try:
            datetime.strptime(astring, fmt)
            return fmt
        except ValueError:
            continue

    return None


def from_string(
    astring: str,
    func: Optional[Callable[[str, ...], int|float|complex|str|datetime]] = None,
    **kwargs):
    """ """

    # use the function provided
    if func:
        return func(astring, **kwargs)

    # numeric
    if is_numeric(astring):

        # look for imag part for complex
        if re.findall('[ij]', astring):
            return complex(astring)

        # look for a decimal
        if re.findall('\.', astring):
            return float(astring)

        else:
            return int(astring)

    # datetimes
    # TODO fix docs on is_date(times) since they now return a fmt
    for func in (is_date, is_time, is_datetime):
        fmt = func(astring)
        if fmt:
            return datetime.strptime(astring, fmt)

    else:
        return astring





if __name__ == '__main__':

    astring = '9.17.2024'
    print(is_date(astring))

    """
    dtime0 = datetime.strptime('12/3/2024 10:08:35', '%m/%d/%Y %I:%M:%S')
    dtime1 = datetime.strptime('12/3/2024', '%m/%d/%Y')
    dtime2 = datetime.strptime('10:34:27.907', '%I:%M:%S.%f')
    """

    atime = '14:49:01.009am'
    print(is_time(atime))

    btime = '12/3/2024 14:22:21.008'
    print(is_datetime(btime))

    ctime = 'December 3 2024 14:22:21.008'
    print(is_datetime(ctime))




