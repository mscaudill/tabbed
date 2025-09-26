"""A pytest module for testing Tabbed's detection and conversion of cells."""

import calendar
import datetime
import random

import pytest

from tabbed.utils import parsing

# Number of random runs per test function
NUM_TEST = 1000


# Fixtures
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
    """Returns the year code %Y and a range of 4 digit years in [1900, 2099]."""

    return '%Y', range(1900, 2100)


@pytest.fixture
def noncentury_years():
    """Returns the year code %y and a list of 2 digit years in [2000, 2099]."""

    return '%y', [str(x)[-2:] for x in range(2000, 2100)]


@pytest.fixture
def hour24():
    """Returns the hour code %H and hours in [0, 23]."""

    return '%H', range(24)


@pytest.fixture
def hour12():
    """Returns the hour code %I and hours in [1, 11]."""

    return '%I', range(1, 12)


@pytest.fixture
def minutes():
    """Returns a range of valid minutes in [0, 59]."""

    return range(60)


@pytest.fixture
def seconds():
    """Returns a range of valid seconds in [0, 59]."""

    return range(60)


@pytest.fixture
def diurnal():
    """Returns the am/pm code %p and the list ['am', 'pm']."""

    return '%p', 'am pm'.split()


@pytest.fixture
def microsecs():
    """Returns a range of microseconds in [0, 999999]."""

    return range(999999)


@pytest.fixture
def time_seperators():
    """Returns two variations of the time separators supported by Tabbed for
    microsecs."""

    return ': .'.split()


@pytest.fixture()
def valid_date(
        rng,
        separators,
        named_months,
        abbr_months,
        digit_months,
        century_years,
        noncentury_years):
    """Returns a format string and a corresponding random stringed date."""

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
    """Returns a format string and random stringed time."""

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

    fmt = f'{hfmt}:%M:%S{sep}%f {dicode}'
    example = f'{hour}:{mins}:{secs}{sep}{musecs}{diurn}'

    return fmt, example


@pytest.fixture
def valid_datetime(
    valid_date,
    valid_time):
    """Returns a format string and valid stringed datetime instance."""

    date_fmt, date = valid_date
    time_fmt, time = valid_time
    return ' '.join([date_fmt, time_fmt]), ' '.join([date, time])


@pytest.fixture
def integer_numeric(rng):
    """Returns a stringed random integer value in [-1e4, 1e4]."""

    return str(rng.randrange(int(-1e4), int(1e4)))


@pytest.fixture
def float_numeric(rng):
    """Returns a random float values in [-1e4, 1e4]."""

    return str(rng.uniform(-1e4, 1e4))


@pytest.fixture
def float_comma_numeric(rng):
    """Returns a random float string with a comma decimal."""

    return str(rng.uniform(-1e4, 1e4)).replace('.', ',')


@pytest.fixture
def scientific_numeric(rng):
    """Returns a stringed random scientific notation float."""

    # rounding not nessary but enotation usually is short
    mantissa = round(rng.uniform(-1, 1), 6)
    exponent = rng.randrange(-10, 10)
    form = rng.choice(['e', 'E'])
    return str(mantissa) + form + str(exponent)


@pytest.fixture
def scientific_comma_numeric(rng):
    """Returns a stringed random scientific notation float."""

    # rounding not nessary but enotation usually is short
    mantissa = round(rng.uniform(-1, 1), 6)
    exponent = rng.randrange(-10, 10)
    form = rng.choice(['e', 'E'])
    r = str(mantissa).replace('.', ',') + form + str(exponent).replace('.',',')
    return r

@pytest.fixture
def complex_numeric(rng):
    """Returns a stringed complex number."""

    real = rng.uniform(-1e4, 1e4)
    imag = rng.uniform(-1e4, 1e4)
    return str(complex(real, imag))


@pytest.fixture
def complex_comma_numeric(rng):
    """Returns a stringed complex number using a comma decimal."""

    real = rng.uniform(-1e4, 1e4)
    imag = rng.uniform(-1e4, 1e4)
    return str(complex(real, imag)).replace('.', ',')


# Tests
def test_convert_of_date(valid_date):
    """Validates that conversion returns a datetime instance for a stringed date.

    This is a catch-all test because if format detection fails, conversion returns
    a string. If format detection succeeds but conversion fails then we again
    return a string. Success of all subfunctions in parsing is required to return
    a datetime instance and therefore this is the only test needed to validate
    date, time and datetime conversions.
    """

    _, date = valid_date
    assert isinstance(parsing.convert(date, decimal='.'), datetime.date)


def test_convert_of_time(valid_time):
    """Validates that conversion returns a datetime instance for a stringed time.

    This is a catch-all test because if format detection fails, conversion returns
    a string. If format detection succeeds but conversion fails then we again
    return a string. Success of all subfunctions in parsing is required to return
    a datetime instance and therefore this is the only test needed to validate
    date, time and datetime conversions.
    """

    _, time = valid_time
    assert isinstance(parsing.convert(time, decimal='.'), datetime.time)


def test_convert_of_datetime(valid_datetime):
    """Validates that conversion returns a datetime instance for a stringed
    datetime.

    This is a catch-all test because if format detection fails, conversion returns
    a string. If format detection succeeds but conversion fails then we again
    return a string. Success of all subfunctions in parsing is required to return
    a datetime instance and therefore this is the only test needed to validate
    date, time and datetime conversions.
    """

    _, dtime = valid_datetime
    assert isinstance(parsing.convert(dtime, decimal='.'), datetime.datetime)


def test_numeric(
    integer_numeric,
    float_numeric,
    scientific_numeric,
    complex_numeric):
    """Validates that conversion returns a numeric instance for a stringed
    numeric type.

    This is a catch-all test because if conversion fails then convert returns
    a string. Success of all subfunctions in parsing is required to return
    a numeric and therefore this is the only test needed to validate date, time
    and datetime conversions.
    """

    assert all(parsing.convert(x, decimal='.') for x in locals().values())


def test_numeric_comma(
    integer_numeric,
    float_comma_numeric,
    scientific_comma_numeric,
    complex_comma_numeric):
    """Validates that conversion returns a numeric instance for a stringed
    numeric type with a comma decimal.

    This is a catch-all test because if conversion fails then convert returns
    a string. Success of all subfunctions in parsing is required to return
    a numeric and therefore this is the only test needed to validate date, time
    and datetime conversions.
    """

    assert all(parsing.convert(x, decimal=',') for x in locals().values())


