"""A pytest module for testing Tabbed's celltyping module, a module with
functions for type determination and conversion."""

import pytest
from itertools import product
import re
import random
import string
import datetime

from src.tabbed.utils import celltyping

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

@pytest.fixture(params=['Janua', '20', "10.5", "-1", "J"])
def invalid_month(request):
    """Returns invalid month"""

    return request.param


@pytest.fixture(params=['3', '03'])
def valid_day(request):
    """Returns a valid day using all possible day fmts."""

    return request.param

@pytest.fixture(params=["-1", "50", "10.4", "Tuesday"])
def invalid_day(request):
    """Returns invalid day"""

    return request.param

@pytest.fixture(params=['2025', '25'])
def valid_year(request):
    """Returns a valid year using all possible year fmts."""

    return request.param

@pytest.fixture(params=["-20", "Twenty Twenty-Five", "25.01"])
def invalid_year(request):
    """Returns an invalid year"""

    return request.param

@pytest.fixture(params=set(' /.-'))
def invalid_date_month(request, invalid_month, valid_day, valid_year):
    """Returns a list of invalid dates where the invalid part is the month

    These dates are all month first
    """

    x = f'{invalid_month}{request.param}{valid_day}{request.param}{valid_year}'
    return x

@pytest.fixture(params=set(' /.-'))
def invalid_date_day(request, valid_month, invalid_day, valid_year):
    """Returns a list of invalid dates where the invalid part is the day

    These dates are all month first
    """

    x = f'{valid_month}{request.param}{invalid_day}{request.param}{valid_year}'
    return x

@pytest.fixture(params=set(' /.-'))
def invalid_date_year(request, valid_month, valid_day, invalid_year):
    """Returns a list of invalid dates where the invalid part is the year

    These dates are all month first
    """

    x = f'{valid_month}{request.param}{valid_day}{request.param}{invalid_year}'
    return x

@pytest.fixture(params=set('*:\\~,;|_&'))
def invalid_date_separator(request, valid_month, valid_day, valid_year):
    """Returns a list of invalid dates where the invalid part is the separator
    
    These dates are all month first
    """

    x = f'{valid_month}{request.param}{valid_day}{request.param}{valid_year}'
    return x


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

    assert celltyping.find_format(valid_date, celltyping.date_formats())

@pytest.mark.xfail
def test_find_date_invalid_date_month(invalid_date_month):
    """Test that find format does not find any format for a date with an invalid month"""

    assert celltyping.find_format(invalid_date_month, celltyping.date_formats())

@pytest.mark.xfail
def test_find_date_invalid_date_day(invalid_date_day):
    """Test that find format does not find any format for a date with an invalid day"""

    assert celltyping.find_format(invalid_date_day, celltyping.date_formats())

@pytest.mark.xfail
def test_find_date_invalid_date_year(invalid_date_year):
    """Test that find format does not find any format for a date with an invalid year"""

    assert celltyping.find_format(invalid_date_year, celltyping.date_formats())

@pytest.mark.xfail
def test_find_date_invalid_date_separator(invalid_date_separator):
    """Test that find format does not find any format for a date with an invalid separator"""

    assert celltyping.find_format(invalid_date_separator, celltyping.date_formats())

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

@pytest.fixture(
    params=[["13", "PM"],["-1", ""], ["26", ""], ["16", "AM"], ["0", ""]]
)
def invalid_hour_diurnal_pair(request):
    """Returns an invalid (hour, diurnal) pair"""

    return request.param

@pytest.fixture
def valid_minute():
    """Returns a valid minute using all possible minute formats"""

    return "01"

@pytest.fixture(
    params=["-3", "0003", "70", "20.3"]
)
def invalid_minute(request):
    """Returns an invalid minute"""

    return request.param

@pytest.fixture
def valid_second():
    """Returns a valid second using all possible second formats"""

    return "01"

@pytest.fixture(
    params=["-3", "0005", "70", "24.3"]
)
def invalid_second(request):
    """Returns an invalid second"""

    return request.param


@pytest.fixture(
    params=["", ".434623", ":434623"],
    ids=lambda val: f'microsecond={val}'    
)
def valid_microsecond(request):
    """Returns a valid microsecond using all the possible microsecond formats"""

    return request.param

@pytest.fixture(params=[".34", ":4345", ".42423423552", ":43234235235", "342"])
def invalid_microsecond(request):
    """Returns an invalid microsecond"""

    return request.param

@pytest.fixture
def valid_time(valid_hour_diurnal_pair, valid_minute, valid_second, valid_microsecond):
    """Returns a list of valid times that match a tabbed time format."""
    
    valid_hour = valid_hour_diurnal_pair[0]
    valid_diurnal = valid_hour_diurnal_pair[1]
    x = f'{valid_hour}:{valid_minute}:{valid_second}{valid_microsecond}{valid_diurnal}'
    return x

@pytest.fixture
def invalid_time_microsecond(valid_hour_diurnal_pair, valid_minute, valid_second, invalid_microsecond):
    """Returns a list of invalid times where the invalid part is the microsecond"""
    
    valid_hour = valid_hour_diurnal_pair[0]
    valid_diurnal = valid_hour_diurnal_pair[1]
    x = f'{valid_hour}:{valid_minute}:{valid_second}{invalid_microsecond}{valid_diurnal}'
    return x
    
@pytest.fixture
def invalid_time_minute(valid_hour_diurnal_pair, invalid_minute, valid_second, valid_microsecond):
    """Returns a list of invalid times where the invalid part is the microsecond"""
    
    valid_hour = valid_hour_diurnal_pair[0]
    valid_diurnal = valid_hour_diurnal_pair[1]
    x = f'{valid_hour}:{invalid_minute}:{valid_second}{valid_microsecond}{valid_diurnal}'
    return x

@pytest.fixture
def invalid_time_second(valid_hour_diurnal_pair, valid_minute, invalid_second, valid_microsecond):
    """Returns a list of invalid times where the invalid part is the second"""
    
    valid_hour = valid_hour_diurnal_pair[0]
    valid_diurnal = valid_hour_diurnal_pair[1]
    x = f'{valid_hour}:{valid_minute}:{invalid_second}{valid_microsecond}{valid_diurnal}'
    return x

@pytest.fixture
def invalid_time_hour_diurnal_pair(invalid_hour_diurnal_pair, valid_minute, valid_second, valid_microsecond):
    """Returns a list of invalid times where the invalid part is the (hour, diurnal) pair"""
    
    invalid_hour = invalid_hour_diurnal_pair[0]
    invalid_diurnal = invalid_hour_diurnal_pair[1]
    x = f'{invalid_hour}:{valid_minute}:{valid_second}{valid_microsecond}{invalid_diurnal}'
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
def test_find_invalid_time_microsecond(invalid_time_microsecond):
    """Test that find format does not locate a format given a time with an invalid microsecond"""

    assert celltyping.find_format(invalid_time_microsecond, celltyping.time_formats())

@pytest.mark.xfail
def test_find_invalid_time_second(invalid_time_second):
    """Test that find format does not locate a format given a time with an invalid second"""

    assert celltyping.find_format(invalid_time_second, celltyping.time_formats())

@pytest.mark.xfail
def test_find_invalid_time_minute(invalid_time_minute):
    """Test that find format does not locate a format given a time with an invalid minute"""

    assert celltyping.find_format(invalid_time_minute, celltyping.time_formats())

@pytest.mark.xfail
def test_find_invalid_time_hour_diurnal(invalid_time_hour_diurnal_pair):
    """Test that find format does not locate a format given a time with an invalid hour and diurnal pair"""

    assert celltyping.find_format(invalid_time_hour_diurnal_pair, celltyping.time_formats())

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