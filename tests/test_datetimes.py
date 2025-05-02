"""A pytest module for testing Tabbed's detection and conversion of cells with
string encoded dates, times and datetime instances.
"""

import calendar
import datetime
import random

import pytest

from tabbed.utils import parsing

NUM_TEST = 1000


@pytest.fixture(params=range(NUM_TEST))
def rng(request):
    """Returns NUM_TEST number of fixed random generators."""

    random.seed(request.param)
    return random


@pytest.fixture
def separators():
    """Returns a list of Tabbed supported separators for date formats."""

    return '/ - .'.split()


@pytest.fixture
def named_months():
    """Returns the month code %B and a list of named calendar months."""

    return '%B', calendar.month_name[1:]


@pytest.fixture
def abbr_months():
    """Returns the month code %b and a list of calendar month abbreviations."""

    return '%b', calendar.month_abbr[1:]


@pytest.fixture
def digit_months():
    """Returns the month code %m and a list of valid digit months."""

    unpadded = [str(x) for x in range(1, 13)]
    padded = ['0' + up for up in unpadded if len(up) < 2]

    return '%m', unpadded + padded


@pytest.fixture
def century_years():
    """Returns the year code %Y and a list of 4 digit years in [1900, 2099]."""

    return '%Y', list(range(1900, 2100))


@pytest.fixture
def noncentury_years():
    """Returns the year code %y and a list of 2 digit years in [2000, 2099]."""

    return '%y', [str(x)[-2:] for x in range(2000, 2100)]


@pytest.fixture()
def valid_date(
        rng,
        separators,
        named_months,
        abbr_months,
        digit_months,
        century_years,
        noncentury_years):
    """Returns a format string and a corresponding random datestring."""

    # choose a separator, month format and year format
    sep = rng.choice(separators)
    # choose month format then choose a month in that format
    mfmt, months = rng.choice([named_months, abbr_months, digit_months])
    month = rng.choice(months)
    # choose a year format then choose a year in that format
    yfmt, years = rng.choice([century_years, noncentury_years])
    year = rng.choice(years)
    # choose day from minimum number of days in a given month
    day = rng.choice(range(1, 29))
    # choose if day is first in fmt
    day_first = rng.choice([True, False])

    # build formats and date example for day first and otherwise
    fmts = [f'%d{sep}{mfmt}{sep}{yfmt}', f'{mfmt}{sep}%d{sep}{yfmt}']
    dates = [f'{day}{sep}{month}{sep}{year}', f'{month}{sep}{day}{sep}{year}']

    return (fmts[0], dates[0]) if day_first else (fmts[1], dates[1])


@pytest.fixture
def hour24():
    """Returns the hour code %H and hours in [0, 23]."""

    return '%H', list(range(24))


@pytest.fixture
def hour12():
    """Returns the hour code %I and hours in [1, 11]."""

    return '%I', list(range(1, 12))


@pytest.fixture
def minutes():
    """Returns a list of valid minutes in [0, 59]."""

    return list(range(60))


@pytest.fixture
def seconds():
    """Returns a list of valid seconds in [0, 59]."""

    return list(range(60))


@pytest.fixture
def diurnal():
    """Returns the am/pm code %p and the list ['am', 'pm']."""

    return '%p', 'am pm'.split()


@pytest.fixture
def microsecs():
    """Returns a list of microseconds in [0, 999999]."""

    return list(range(999999))


@pytest.fixture
def time_seperators():
    """Returns two variations of the time separators supported by Tabbed for
    microsecs."""

    return ': .'.split()


# FIXME the diurnal ma have a space before it that our time formats aren't
# account for!!!
@pytest.fixture()
def valid_time(
        rng,
        time_seperators,
        hour12,
        hour24,
        minutes,
        seconds,
        microsecs,
        diurnal):
    """ """

    # choose a microseconds separator
    sep = rng.choice(time_seperators)
    # choose an hour format and hour
    hfmt, hours = rng.choice([hour12, hour24])
    hour = rng.choice(hours)
    # choose number of mins, secs and microsecs
    mins, secs, musecs = [rng.choice(x) for x in (minutes, seconds, microsecs)]
    # set diurnal based on hourfmt adding a space if am/pm is present
    dicode = '%p' if hfmt == '%I' else ''
    diurn = ' ' + rng.choice(diurnal[1]) if dicode else ''

    fmt = f'{hfmt}:%M:%S{sep}%f{dicode}'
    example = f'{hour}:{mins}:{secs}{sep}{musecs}{diurn}'

    return fmt, example


"""
def test_times(valid_time):
    print(valid_time)
    assert True
"""


def test_convert_of_date(valid_date):
    """Validates that conversion returns a datetime instance for a stringed date.

    This is a catch-all test because if format detection fails, conversion returns
    a string. If format detection succeeds but conversion fails then we again
    return a string. Success of all subfunctions in parsing is required to return
    a datetime instance and therefore this is the only test needed to validate
    date, time and datetime conversions.
    """

    _, date = valid_date
    assert isinstance(parsing.convert(date), datetime.datetime)


def test_convert_of_time(valid_time):
    """Validates that conversion returns a datetime instance for a stringed time.

    This is a catch-all test because if format detection fails, conversion returns
    a string. If format detection succeeds but conversion fails then we again
    return a string. Success of all subfunctions in parsing is required to return
    a datetime instance and therefore this is the only test needed to validate
    date, time and datetime conversions.
    """

    _, time = valid_time
    assert isinstance(parsing.convert(time), datetime.datetime)
