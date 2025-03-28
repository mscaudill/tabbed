# FIXME Add a module string explaining that you will construct tables of
# different types

import tempfile
import string
import datetime
import pytest
import random
from itertools import batched

from tabbed.sniffing import Sniffer


@pytest.fixture(params=[0])
def rng(request):
    """Returns a random number generator."""

    random.seed(request.param)
    return random


@pytest.fixture(params=",;|\t")
def delimiter(request):
    """Returns tabbed compatible delimiters."""

    return request.param


@pytest.fixture
def valid_chars():
    """Returns a string of all valid characters.

    Invalid characters are a delimiters and quote chars
    """

    chars = list(string.ascii_letters + string.digits + string.punctuation)
    invalid = set([',', ';', '|', '\t', '\'', '"'])

    return [char for char in chars if char not in invalid]


@pytest.fixture
def string_table(rng, valid_chars):
    """A fixture that returns a function for building random tables of valid
    string characters."""

    # FIXME when I call this fixture over and over in table I want to produce
    # new random tables that are reproducible across table calls. I think
    # turning rng into  a function returning fixture is the way to go
    def make_table(rows, cols):
        """Returns a rows x cols table of strings of random lengths."""

        cnt = rows * cols
        lengths = [rng.randint(1, 15) for _ in range(cnt)]
        cells = [''.join(rng.choices(valid_chars, k=l)) for l in lengths]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def integer_table(rng):
    """A fixture that returns a function for building random tables of stringed
    integer values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of integers between -1000 and 1000."""

        cnt = rows * cols
        cells = [str(rng.randint(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def float_table(rng):
    """A fixture that returns a function for building random tables of stringed
    float values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [str(rng.uniform(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def complex_table(rng):
    """A fixture that returns a function for building random tables of stringed
    complex values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed complex values with real and
        imag parts in [-1000, 1000]."""

        # * 2 for real and complex parts
        cnt = rows * cols * 2
        parts = [rng.uniform(-1000, 1000) for _ in range(cnt)]
        cells = [str(complex(tup)) for tup in batched(parts, 2)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def enotation_table(rng):
    """A fixture that returns a function for building random tables of stringed
    scientific notation float values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of E notation floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [f'{rng.uniform(-1000, 1000):.2E}' for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def time_table(rng, time_formats):
    """A fixture that returns a function for building random tables of stringed
    times."""

    def make_table(rows, cols):
        """Returns a rows x cols table of times."""

        cnt = rows * cols
        hours = [rng.randint(1, 23) for _ in range(cnt)]
        mins = [rng.randint(0, 59) for _ in range(cnt)]
        secs = [rng.randint(0, 59) for _ in range(cnt)]
        micros = [rng.randint(0, 999999) for _ in range(cnt)]
        times = [
                datetime.time(hour=h, minute=m, second=s, microsecond=mu)
                for h, m, s, mu in zip(hours, mins, secs, micros)
                ]
        fmts = [rng.choice(time_formats) for _ in range(cnt)]
        cells = [time.strftime(fmt) for time, fmt in zip(times, fmts)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def date_table(rng, date_formats):
    """A fixture that returns a function for building random tables of stringed
    dates."""

    def make_table(rows, cols):
        """Returns a rows x cols table of dates."""

        cnt = rows * cols
        years = [rng.randint(1800, 2500) for _ in range(cnt)]
        months = [rng.randint(1, 12) for _ in range(cnt)]
        days = [rng.randint(1, 28) for _ in range(cnt)]
        dates = [datetime.date(y, m, d) for y, m, d in zip(years, months, days)]
        fmts = [rng.choice(date_formats) for _ in range(cnt)]
        cells = [date.strftime(fmt) for date, fmt in zip(dates, fmts)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def datetime_table(time_table, date_table):
    """A fixture that returns a function for building random tables of stringed
    datetime instances."""

    def make_table(rows, cols):
        """Returns a rows x cols table of datetime strings."""

        timed_table = time_table(rows, cols)
        dated_table = date_table(rows, cols)

        cells = []
        for date_row, time_row in zip(dated_table, timed_table):
            cells.extend([' '.join((d, t)) for d, t in zip(date_row, time_row)])

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture(params=[2])
def shape(request):
    """A fixture that returns a reproducible random shape tuple for a table."""

    # to generate different shapes if rng seed is not None use fresh random
    random.seed(request.param)
    row_count = random.randint(1, 200)
    col_count = random.randint(1, 20)

    return row_count, col_count


@pytest.fixture
def table(
        rng,
        shape,
        string_table,
        integer_table,
        float_table,
        enotation_table,
        time_table,
        date_table,
        datetime_table,
):
    """Returns random tables of random shapes with random tabbed supported
    data types."""

    args = locals()
    rng = args.pop('rng')
    rows, cols = args.pop('shape')

    # build each table type then conncatenate along columns
    subtables = [atable(rows, cols) for atable in args.values()]
    combined = [sum(row_tuple, start=[]) for row_tuple in zip(*subtables)]

    # randomly choose cols from combined
    transpose = list(zip(*combined))
    chosen = rng.choices(transpose, k=cols)

    # transpose back to cols by rows and return
    return list(zip(*chosen))

# FIXME
# I don't yet full have the randomization to my satisfaction. I want to generate
# sequences of random but reproducible tables. This code with the current rng
# does not accomplish this



def test_stringtable(string_table):

    print(string_table(4, 5))

    assert True

def test_inttabel(integer_table):

    print(integer_table(4, 5))

    assert True



"""
def test_table(table):
    """ """

    print('shape =', len(table), len(table[0])) 
    for row in table:
        print(row)

    assert True
"""


"""
def test_shapes(shape):
    """ """

    print(shape)

    assert True

def test_rng(rng):

    a = [rng.randint(0,100) for _ in range(10)]
    b = [rng.randint(0,100) for _ in range(10)]

    print(a)
    print(b)

    assert True
"""
