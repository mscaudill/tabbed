# FIXME Add a module string explaining that you will construct tables of
# different types

import tempfile
import string
import datetime
import pytest
import random
from itertools import batched

from tabbed.sniffing import Sniffer


NUM_TEST = 3

@pytest.fixture(params=range(NUM_TEST))
def rng(request):
    """Returns a random number generator."""

    random.seed(request.param)
    return random


@pytest.fixture(params=[',', ';', '|', r'\t'])
def delimiters(request):
    """Returns a subset of tabbed compatible delimiters."""

    return request.param


@pytest.fixture
def valid_chars():
    """Returns a string of all valid characters.

    Invalid characters are a delimiters and quote chars
    """

    chars = list(string.ascii_letters +
                 string.digits +
                 string.punctuation +
                 ' ')
    invalid = set([',', ';', '|', '\t', '\'', '"'])

    return [char for char in chars if char not in invalid]


@pytest.fixture
def string_table(rng, valid_chars):
    """Returns a function for building random tables of valid string chars."""

    def make_table(rows, cols):
        """Returns a rows x cols table of strings of random lengths."""

        cnt = rows * cols
        lengths = [rng.randint(1, 15) for _ in range(cnt)]
        cells = [''.join(rng.choices(valid_chars, k=l)) for l in lengths]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def integer_table(rng):
    """Returns a function for building random tables of stringed integers."""

    def make_table(rows, cols):
        """Returns a rows x cols table of integers between -1000 and 1000."""

        cnt = rows * cols
        cells = [str(rng.randint(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def float_table(rng):
    """Returns a function for building random tables of stringed floats."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [str(rng.uniform(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def complex_table(rng):
    """Returns a func. for building random tables of stringed complex values."""

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
    """Returns a function for building random tables of stringed scientific
    notation values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of E notation floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [f'{rng.uniform(-1000, 1000):.2E}' for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def time_table(rng, time_formats):
    """Returns a function for building random tables of stringed times."""

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
    """Returns a function for building random tables of stringed dates."""

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
    """Returns a function for building random tables of stringed datetimes."""

    def make_table(rows, cols):
        """Returns a rows x cols table of datetime strings."""

        timed_table = time_table(rows, cols)
        dated_table = date_table(rows, cols)

        cells = []
        for date_row, time_row in zip(dated_table, timed_table):
            cells.extend([' '.join((d, t)) for d, t in zip(date_row, time_row)])

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def shape(rng):
    """Returns a reproducible random shape tuple for a table."""

    row_count = rng.randint(1, 200)
    col_count = rng.randint(1, 20)

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
    """Returns a randomly shaped table for each rng of the rng fixture.

    This table is constructed from single type tables for all types supported by
    Tabbed.
    """

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


# TODO test what happens for invalid tables, specifically
# 1. tables with invalid types (expect string returns) e.g. stringed tuples
# 2. ragged tables with rows of different numbers of columns


@pytest.fixture
def header(rng, valid_chars):
    """Returns a function for building a random valid header."""

    def make_header(cols):
        """Returns a list of valid header names."""

        return [''.join(rng.choices(valid_chars, k=15)) for _ in range(cols)]

    return make_header


@pytest.fixture
def repeating_header(rng, valid_chars):
    """Returns a function for building headers with repeating names."""

    def make_header(cols):
        """Returns a list of valid header names with repeats of length cols."""

        names = [''.join(rng.choices(valid_chars, k=15)) for _ in range(cols)]
        indices = rng.choices(range(len(names)), k=min(len(names) // 2, 1))
        for idx in indices:
            names[idx] = names[0]

        return names

    return make_header


@pytest.fixture
def numeric_header(rng):
    """Returns a function for building an invalid numeric header."""

    def make_header(cols):
        """Returns a list of stringed numeric names."""

        return [str(rng.randint(0, 100)) for _ in range(cols)]

    return make_header


@pytest.fixture
def date_header(rng):
    """Returns invalid headers composed of stringed date names."""

    def make_header(cols):
        """Returns a list of stringed date names."""

        start = datetime.datetime(2023, 9, 13)
        days = [rng.randint(0, 500) for _ in range(cols)]
        deltas = [datetime.timedelta(days=d) for d in days]

        return [str((start + delta).date()) for delta in deltas]

    return make_header


@pytest.fixture
def time_header(rng):
    """Returns invalid headers composed of stringed time names."""

    def make_header(cols):
        """Returns a list of stringed time names."""

        start = datetime.datetime(1, 1, 1, 10, 32, 15, 63200)
        secs = [rng.randint(0, 10000) for _ in range(cols)]
        deltas = [datetime.timedelta(seconds=sec) for sec in secs]

        return [str((start + delta).time()) for delta in deltas]

    return make_header


@pytest.fixture
def metadata(rng, valid_chars, delimiters):
    """Return valid metadata strings for each rng and delimiter."""

    num_lines = rng.randint(1, 30)
    cell_counts = [rng.randint(1, 8) for _ in range(num_lines)]

    lines = []
    for cell_count in cell_counts:
        line = [''.join(rng.choices(valid_chars, k=16)) for _ in range(cell_count)]
        lines.append(delimiters.join(line))

    return '\n'.join(lines)


@pytest.fixture
def empty_metadata():
    """Returns a metadata with only new line characters."""

    return '\n'.join([''] * 10)


@pytest.fixture
def skipping_metadata(rng, valid_chars):
    """Returns a metadata with a blank line."""

    rows = list(batched(rng.choices(valid_chars, k=100), 5))
    lines = [';'.join(row) for row in rows]
    lines[3] = ''

    return '\n'.join(lines)










"""
def test_validchars(valid_chars):

    print(valid_chars)

    assert True
"""


"""
def test_stringtable(string_table):

    print(string_table(4, 5))

    assert True
"""

"""
def test_inttabel(integer_table):

    print(integer_table(4, 5))

    assert True
"""

"""
def test_datetable(date_table):

    print(date_table(3,6))

    assert True
"""


"""
def test_table(table):

    print('shape =', len(table), len(table[0]))
    for row in table:
        print(row)

    assert True
"""

"""
def test_header(header):

    print(header(5))

    assert True
"""

"""
def test_repeat_header(repeating_header):

    print(repeating_header(4))

    assert True
"""

"""
def test_numericheader(numeric_header):

    print(numeric_header)
    assert True
"""

"""
def test_dateheader(date_header):

    print(date_header(6))
    assert True
"""

"""
def test_timeheader(time_header):

    print(time_header(10))

    assert True
"""

"""
def test_metadata(metadata):

    print(metadata)

    assert True
"""

def test_skippingmetadata(skipping_metadata):

    print(skipping_metadata)

    assert True

