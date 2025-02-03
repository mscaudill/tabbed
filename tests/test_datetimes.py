"""A pytest module for testing Tabbed's celltyping module, a module with
functions for type determination and conversion."""

import pytest
from itertools import product

from tabbed.utils import celltyping

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



