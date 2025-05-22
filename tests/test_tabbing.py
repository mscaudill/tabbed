"""A pytest module for testing Tabbed's tabbing system."""


import datetime
import random
import re
import string

import pytest
from tabbed.sniffing import Header
from tabbed.tabs import Tabulator, Accepting


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

        return [rng.randint(*extremes) for _ in range(length)]

    return make_list


@pytest.fixture
def rfloats(rng):
    """Returns a function for constructing a list of random floats."""

    def make_list(length, extremes = (-100, 100)):
        """Returns a list of rand floats."""

        return [rng.uniform(*extremes) for _ in range(length)]

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
def rtimes(rng):
    """Returns a function for constructing a list of random times."""

    def make_list(length):
        """Returns a list of random datetime time instances."""

        hours = [rng.randint(1, 23) for _ in range(length)]
        mins = [rng.randint(0, 59) for _ in range(length)]
        secs = [rng.randint(0, 59) for _ in range(length)]
        micros = [rng.randint(0, 999999) for _ in range(length)]
        times = [datetime.time(hour=h, minute=m, second=s, microsecond=mu)
                for h, m, s, mu in zip(hours, mins, secs, micros)
                ]

        return times
    return make_list


@pytest.fixture
def rdates(rng):
    """Returns a function for constructing a list of random dates."""

    def make_list(length):
        """Returns a list of random datetime date instances."""

        years = [rng.randint(1800, 2500) for _ in range(length)]
        months = [rng.randint(1, 12) for _ in range(length)]
        days = [rng.randint(1, 28) for _ in range(length)]
        dates = [datetime.date(y, m, d) for y, m, d in zip(years, months, days)]

        return dates
    return make_list


@pytest.fixture
def rdatetimes(rng):
    """Returns a function for constructing a list of random datetimes."""

    def make_list(length):
        """Returns a list of random datetime instances."""

        start = datetime.datetime.now()
        delta = datetime.timedelta
        deltas = [delta(seconds=rng.randint(1, 1000)) for _ in range(length)]

        return [start + delta for delta in deltas]
    return make_list


@pytest.fixture
def rstrings(rng):
    """Returns a function for constructing a list of random strings."""

    def make_list(length):
        """Returns a list of random string instances."""

        strs = ['tom', 'cat', 'dog', 'pig', 'cow', 'chicken', 'sue', 'billy']

        return rng.choices(strs, k=length)
    return make_list


@pytest.fixture
def data(rints, rfloats, rcomplexes, rtimes, rdates, rdatetimes, rstrings):
    """Returns a single sample data, a list of dictionaries, the output from
    python's DictReader that have undergone Tabbed's type conversion.

    This sample data contains all supported Tabbed CellTypes.
    """

    args = locals()
    shape = 100, 7
    header = [
        'integers',
        'floats',
        'complexes',
        'times',
        'dates',
        'datetimes',
        'strings',
    ]
    rows = list(zip(*[func(shape[0]) for func in args.values()]))

    return [dict(zip(header, row)) for row in rows]


def test_column_assign_by_name():
    """Validates the assignment of columns to extract by string name."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    # set columns to extract
    cols = ['peaches', 'oranges']
    tabulator = Tabulator(header, columns=cols)

    assert tabulator.columns == cols


def test_column_assign_by_index():
    """Validates the assignment of columns to extract by column index."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    # set columns to extract
    cols = [0, 2]
    tabulator = Tabulator(header, columns=cols)

    assert tabulator.columns == [header.names[col] for col in cols]


def test_column_assign_by_pattern():
    """Validates the assignment of columns to extract by re pattern."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    # find columns that start with 'pe'
    pattern = re.compile(r'^pe')
    tabulator = Tabulator(header, columns=pattern)

    assert tabulator.columns == ['pears', 'peaches']


def test_bad_assign():
    """Validates that a Sequence on mixed types raises a ValueError."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    cols = ['peaches', 3]
    with pytest.raises(ValueError):
        tabulator = Tabulator(header, columns=cols)


def test_invalid_name():
    """Validate that an invalid column assingment is ignored."""

    namestr = 'oranges,pears,peaches,plums'
    header = Header(names=namestr.split(','), line=2, string=namestr)

    cols = ['peaches', 'plums', 'kiwis']
    with pytest.warns():
        tabulator = Tabulator(header, columns=cols)

    assert tabulator.columns == cols[:-1]


def test_tab_construction():
    """Validates alternative constructor correctly instantiates tabs."""

    namestr = 'group,cnt,kind,color'
    header = Header(names=namestr.split(','), line=2, string=namestr)
    columns = namestr.split(',')[:4]

    #make Tabs of various types Equality, Membership, Regex, Comparison
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
    """Validates equality tabbing returns correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, strings='cat')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all(['cat' in row.values() for row in rows])


def test_tabbing_membership(data):
    """Validates membership tabbing returns correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, integers=[0, 1, 2, 3, 4])
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    assert all([row['integers'] in [0, 1, 2, 3, 4] for row in rows])


def test_tabbing_comparison(data):
    """Validates rich comparison tabbing returns the correct rows of data."""

    names = data[0].keys()
    header = Header(names = names, line=None, string=None)
    tabulator = Tabulator.from_keywords(header, floats = '>= 0 and < 50')
    rows = [tabulator(row) for row in data]
    rows = [row for row in rows if row]

    a = all([row['floats'] >= 0 for row in rows])
    b = all([row['floats'] < 50 for row in rows])

    assert a and b


def test_tabbing_regex(data):
    """Validates regular expression tabbing returns the correct rows of data."""

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








