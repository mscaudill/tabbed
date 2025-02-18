"""A pytest module for testing Tabbed's celltyping module, a module with
functions for type determination and conversion."""

import pytest
from itertools import product
import re
import random
import string
import datetime

from tabbed.utils import celltyping

# Fixture for returning a random number generator
@pytest.fixture
def rn_generator():
    """Returns a random number generator with the seed 1"""

    return random.Random(1)


# Date format tests

@pytest.fixture
def month():
    """Returns a set of month format codes."""

    return set(['%m', '%b', '%B'])


@pytest.fixture
def year():
    """Returns a set of year format codes."""

    return set(['%y', '%Y'])

@pytest.fixture
def separators():
    """Returns a set of tabbed supported separators for date formats."""

    return set(' /-.')


@pytest.fixture(params=['January', 'Jan', '01', '1'])
def valid_month(request):
    """Returns a valid month using all possible month fmts."""

    return request.param


@pytest.fixture(params=['3', '03'])
def valid_day(request):
    """Returns a valid day using all possible day fmts."""

    return request.param


@pytest.fixture(params=['2025', '25'])
def valid_year(request):
    """Returns a valid year using all possible year fmts."""

    return request.param


@pytest.fixture(params=set(' /.-'))
def valid_date(request, valid_month, valid_day, valid_year):
    """Returns a list of valid dates that match a tabbed date format.

    These dates are all month first
    """

    x = f'{valid_month}{request.param}{valid_day}{request.param}{valid_year}'
    return x

@pytest.fixture(params=range(10))
def no_digit_string(request, rn_generator):
    """Returns strings that have no digits"""

    length = rn_generator.randint(1, 20)
    chars = string.ascii_letters + string.punctuation + " "
    return ''.join(rn_generator.choices(chars, k=length))

def test_date_format_months(month):
    """Test that tabbed's date formats include a month format code."""

    for fmt in celltyping.date_formats():
        sep = fmt[2]
        parts = fmt.split(sep)
        assert month.intersection(parts)


def test_date_format_day():
    """Test that Tabbed's date format includes a day format code."""

    for fmt in celltyping.date_formats():
        assert '%d' in fmt


# Example to show how to parameterize a test
#@pytest.mark.parametrize('year', [set(['%y', '%Y'])])
def test_date_format_year(year):
    """Test that tabbed's date formats include a year format code."""

    for fmt in celltyping.date_formats():
        sep = fmt[2]
        parts = fmt.split(sep)
        assert year.intersection(parts)


def test_date_format_seps(separators):
    """Test that tabbed's date formats include one of the supported seps."""

    seps = set([fmt[2] for fmt in celltyping.date_formats()])
    assert seps == separators


def test_date_format_count(month, year, separators):
    """Test that the number of formats is the twice the product of the number of
    month formats, the number of year formats and the number of separators."""

    count = len(celltyping.date_formats())
    assert count == 2 * len(month) * len(year) * len(separators)

def test_find_valid_date(valid_date):
    """Test that find format locates a format given a valid date."""

    print(valid_date)
    assert celltyping.find_format(valid_date, celltyping.date_formats())

@pytest.mark.xfail
def test_find_date_no_digit_string(no_digit_string):
    """Test that find format fails when there is a string with no digits (can't be a date)"""

    assert celltyping.find_format(no_digit_string, celltyping.date_formats())

def test_classify_valid_date(valid_date):
    """Test that is_date returns true for valid dates"""

    assert celltyping.is_date(valid_date)

def test_as_datetime_valid_date(valid_date):
    """Test that as_datetime does not return a string for a valid date (which indicates failure)"""

    fmt = celltyping.find_format(valid_date, celltyping.date_formats())
    assert fmt
    assert isinstance(celltyping.as_datetime(valid_date, fmt).date(), datetime.date)

def test_convert_valid_date(valid_date):
    """Test that convert does not return a string for a valid date (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_date).date(), datetime.date)

# Time format tests

@pytest.fixture
def hour():
    """Returns a set of hour format codes."""

    return set(['%I', "%H"])

@pytest.fixture
def microsecond():
    """Returns a set of microsecond format codes."""

    return set(['', ":%f", ".%f"])

@pytest.fixture
def diurnal():
    """Returns a set of diurnal format codes."""

    return set(['', " %p"])

def test_time_format_hour(hour):
    """Test that Tabbed's time format includes an hour format code"""

    for fmt in celltyping.time_formats():
        sep = ":"
        parts = fmt.split(sep)
        assert hour.intersection(parts)

def test_time_format_minute():
    """Test that Tabbed's time format includes a minute format code"""

    for fmt in celltyping.time_formats():
        assert '%M' in fmt

def test_time_format_second():
    """Test that Tabbed's time format include a second format code"""

    for fmt in celltyping.time_formats():
        assert "%S" in fmt

# Note: For microseconds and diurnal, the intersection will always match
# since the empty string will always be present at the end of the time format.

@pytest.fixture(
    params=[["13", ''], ["1", " PM"], ["1", ''], ["1", " AM"]],
    ids=lambda pair: f"hour={pair[0]}-diurnal={pair[1]}"
)
def valid_hour_diurnal_pair(request):
    """Returns a valid (hour, diurnal) pair using all possible (hour, diurnal) format pairs"""

    return request.param

@pytest.fixture
def valid_minute():
    """Returns a valid minute using all possible minute formats"""

    return "01"

@pytest.fixture
def valid_second():
    """Returns a valid second using all possible second formats"""

    return "01"

@pytest.fixture(
    params=["", ".434623", ":434623"],
    ids=lambda val: f'microsecond={val}'    
)
def valid_microsecond(request):
    """Returns a valid microsecond using all the possible microsecond formats"""

    return request.param

@pytest.fixture
def valid_time(valid_hour_diurnal_pair, valid_minute, valid_second, valid_microsecond):
    """Returns a list of valid times that match a tabbed time format."""
    
    valid_hour = valid_hour_diurnal_pair[0]
    valid_diurnal = valid_hour_diurnal_pair[1]
    x = f'{valid_hour}:{valid_minute}:{valid_second}{valid_microsecond}{valid_diurnal}'
    return x


def test_time_format_count(hour, microsecond):
    """Test that the number of formats is the twice the product of the number of
    month formats, the number of year formats and the number of separators."""

    count = len(celltyping.time_formats())
    assert count == len(hour) * len(microsecond)

def test_find_valid_time(valid_time):
    """Test that find format locates a format given a valid time."""

    assert celltyping.find_format(valid_time, celltyping.time_formats())

@pytest.mark.xfail
def test_find_time_no_digit_string(no_digit_string):
    """Test that find format fails when there is a string with no digits (can't be a time)"""

    assert celltyping.find_format(no_digit_string, celltyping.time_formats())

def test_classify_valid_time(valid_time):
    """Test that is_time returns true for valid times"""

    assert celltyping.is_time(valid_time)

def test_as_datetime_valid_time(valid_time):
    """Test that as_datetime does not return a string for a valid time (which indicates failure)"""

    fmt = celltyping.find_format(valid_time, celltyping.time_formats())
    assert fmt
    assert isinstance(celltyping.as_datetime(valid_time, fmt).time(), datetime.time)

def test_convert_valid_time(valid_time):
    """Test that convert does not return a string for a valid time (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_time).time(), datetime.time)

# Datetime format tests

@pytest.fixture
def valid_datetime(valid_date, valid_time):
    """Returns a list of valid dates that match a tabbed date format.

    These dates are all month first
    """

    x = f"{valid_date} {valid_time}"
    return x

def test_datetime_format_months(month):
    """Test that tabbed's datetime formats include a month format code."""

    for fmt in celltyping.datetime_formats():
        sep = fmt[2]
        parts = fmt.split(sep)
        assert month.intersection(parts)

def test_datetime_format_day():
    """Test that Tabbed's datetime format includes a day format code."""

    for fmt in celltyping.datetime_formats():
        assert '%d' in fmt

def test_datetime_format_year(year):
    """Test that tabbed's datetime formats include a year format code."""

    for fmt in celltyping.datetime_formats():
        patterns = f"[{fmt[2]} ]"
        parts = re.split(patterns, fmt)
        assert year.intersection(parts)

def test_datetime_format_hour(hour):
    """Test that Tabbed's datetime format includes an hour format code"""

    for fmt in celltyping.datetime_formats():
        seps = [":", " "]
        pattern = "|".join(seps)
        parts = re.split(pattern ,fmt)
        assert hour.intersection(parts)

def test_datetime_format_minute():
    """Test that Tabbed's datetime format includes a minute format code"""

    for fmt in celltyping.datetime_formats():
        assert '%M' in fmt

def test_datetime_format_second():
    """Test that Tabbed's datetime format include a second format code"""

    for fmt in celltyping.datetime_formats():
        assert "%S" in fmt

def test_find_valid_datetime(valid_datetime):
    """Test that find format locates a format given a valid datetime."""

    assert celltyping.find_format(valid_datetime, celltyping.datetime_formats())

@pytest.mark.xfail
def test_find_datetime_no_digit_string(no_digit_string):
    """Test that find format fails when there is a string with no digits (can't be a datetime)"""

    assert celltyping.find_format(no_digit_string, celltyping.datetime_formats())

def test_classify_valid_datetime(valid_datetime):
    """Test that is_datetime returns true for valid datetimes"""

    assert celltyping.is_datetime(valid_datetime)

def test_as_datetime_valid_datetime(valid_datetime):
    """Test that as_datetime does not return a string for a valid datetime (which indicates failure)"""

    fmt = celltyping.find_format(valid_datetime, celltyping.datetime_formats())
    assert fmt
    assert isinstance(celltyping.as_datetime(valid_datetime, fmt), datetime.datetime)

def test_convert_valid_datetime(valid_datetime):
    """Test that convert does not return a string for a valid datetime (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_datetime), datetime.datetime)