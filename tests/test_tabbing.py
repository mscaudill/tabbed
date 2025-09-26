"""A pytest module for testing Tabbed's tabbing system."""


import datetime
import random
import re
import string

import pytest

from tabbed.sniffing import Header
from tabbed.tabbing import Accepting
from tabbed.tabbing import Tabulator
from tabbed.utils import parsing


@pytest.fixture
def rng():
    """Returns a single random number generator of fixed seed."""

    random.seed(0)
    return random


@pytest.fixture
def rints(rng):
    """Returns a function for constructing a list of random integers."""

    def make_list(length, extremes = (-10, 10)):
        """Returns a list of rand integers."""

        values = (list(range(*extremes)) * length)[:length]
        rng.shuffle(values)
        return values

    return make_list


@pytest.fixture
def rfloats(rng):
    """Returns a function for constructing a list of random floats."""

    def make_list(length, extremes = (-10, 10)):
        """Returns a list of rand floats."""

        values = (list(range(*extremes)) * length)[:length]
        values = [float(val) for val in values]
        rng.shuffle(values)
        return values

    return make_list


@pytest.fixture
def rcomplexes(rng):
    """Returns a function for constructing a list of random complex numbers."""

    def make_list(length, extremes = (-1, 1)):
        """Returns a list of rand integers."""

        return [complex(rng.uniform(*extremes), rng.randint(*extremes))
                for _ in range(length)]

    return make_list


@pytest.fixture
def rdates(rng):
    """Returns a function for constructing a list of random datetimes."""

    def make_list(length):
        """Returns a list of datetime instances that cover upto 1 year"""

        start = parsing.convert('1/1/2025', decimal='.')
        deltas = ([datetime.timedelta(days=x) for x in range(364)]*length)[:length]
        return [start + delta for delta in deltas]

    return make_list


@pytest.fixture
def rstrings(rng):
    """Returns a function for constructing a list of randomly drawn strings."""

    def make_list(length):
        """Returns a list of random string instances."""

        result = (['cat', 'dog', 'pig', 'cow', 'chicken'] * length)[:length]
        rng.shuffle(result)

        return result

    return make_list


@pytest.fixture
def data(rints, rfloats, rcomplexes, rdates, rstrings):
    """Returns a single sample data, a list of dictionaries, the output from
    python's DictReader that have undergone Tabbed's type conversion.

    This sample data contains all supported Tabbed CellTypes.
    """

    args = locals()
    shape = 1000, 7
    header = [
        'integers',
        'floats',
        'complexes',
        'dates',
        'strings',
    ]
    rows = list(zip(*[func(shape[0]) for func in args.values()]))

    return [dict(zip(header, row)) for row in rows]


def test_column_assign_by_name():
    """Test Tabulator's string name column assignment."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    # set columns to extract
    cols = ['peaches', 'oranges']
    tabulator = Tabulator(header, columns=cols)

    assert tabulator.columns == cols


def test_column_assign_by_index():
    """Test Tabulators index column assignment."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    # set columns to extract
    cols = [0, 2]
    tabulator = Tabulator(header, columns=cols)

    assert tabulator.columns == [header.names[col] for col in cols]


def test_column_assign_by_pattern():
    """Test Tabulators regular expression column assingment."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    # find columns that start with 'pe'
    pattern = re.compile(r'^pe')
    tabulator = Tabulator(header, columns=pattern)

    assert tabulator.columns == ['pears', 'peaches']


def test_bad_assign():
    """Test Tabulator raises ValueError on mixed type column assingment."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    cols = ['peaches', 3]
    with pytest.raises(ValueError):
        tabulator = Tabulator(header, columns=cols)


def test_invalid_name():
    """Test Tabulator warns when given an invalid column assingment."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    cols = ['peaches', 'plums', 'kiwis']
    with pytest.warns():
        tabulator = Tabulator(header, columns=cols)

    assert tabulator.columns == cols[:-1]


def test_tab_construction():
    """Test Tabulator's tab construction from keyword arguments."""

    namestr = 'group,cnt,kind,color'
    header = Header(names=namestr.split(','), line=2, string=namestr)
    columns = namestr.split(',')[:4]

    # make Tabs of various types Equality, Membership, Regex, Comparison
    tabulator = Tabulator.from_keywords(
            header,
            columns,
            kind='awesome',
            group=['a', 'b'],
            color=re.compile(r'red|blue'),
            cnt= '>=4',
    )

    kinds = 'Equality Membership Regex Comparison'.split()
    assert all([type(tab).__name__ in kinds for tab in tabulator.tabs])


def test_tabbing_equality(data):
    """Test Equality tab returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, strings='cat')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all(['cat' in row.values() for row in rows])


def test_tabbing_membership(data):
    """Test Mmebership tab returns correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, integers=[2, -3])
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all([row['integers'] in [2, -3] for row in rows])


def test_lessthanequal(data):
    """Test that Comparison tab returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, floats='<=0')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all([row['floats'] <= 0 for row in rows])


def test_greaterthanequal(data):
    """Test that Comparison Tab returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, dates= '>6/1/2025')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all([row['dates'] >= datetime.date(2025, 6, 1) for row in rows])


def test_mixed_comparison(data):
    """Test Comparison tab returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, floats = '>= -2.0 and <2.0')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    a = all([row['floats'] >= -2.0 for row in rows])
    b = all([row['floats'] < 2.0 for row in rows])

    assert a and b


def test_neq_comparison(data):
    """Test Comparison tab returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, integers='!=0')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all([row['integers'] != 0 for row in rows])


def test_tabbing_regex(data):
    """Test Regular expression tab returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    # find rows whose string contains a t anywhere
    tabulator = Tabulator.from_keywords(header, strings=r't')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    # only tom and cat values contain a 't'
    assert all([row['string'] in ['tom', 'cat'] for row in rows])


def test_calling_tab(data):
    """Validates that a Calling tab return the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    # find rows whose integer values are even
    def is_even(row, name):
        return row[name] % 2 == 0

    tabulator = Tabulator.from_keywords(header, integers=is_even)
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all([row['integers'] % 2 == 0 for row in rows])


def test_accepting_tab(data):
    """Validates that accepting tab returns all rows if data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator(header, tabs=[Accepting()])

    assert data == [tabulator(row) for row in data]


def test_multitab(data):
    """Validates that multiple tabs return correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    # find rows whose string contains a t anywhere and integer value is <= 0
    tabulator = Tabulator.from_keywords(header, strings=r't', integers='<= 0')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    has_t = ['t' in row['string'] for row in rows]
    leq0 = [row['integers'] <= 0 for row in rows]

    assert all(has_t) and all(leq0)







