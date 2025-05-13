# FIXME Add a module string explaining that you will construct tables of
# different types

import tempfile
import string
import datetime
import pytest
import random
from itertools import batched, chain

from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.utils import parsing


NUM_TEST = 3

@pytest.fixture(params=range(NUM_TEST))
def rng(request):
    """Returns a random number generator."""

    random.seed(request.param)
    return random


def delimiters():
    """Returns all of tabbed's compatible delimiters."""

    return [',', ';', '|', r'\t']


@pytest.fixture
def valid_chars():
    """Returns a string of all valid characters.

    Invalid characters are a delimiter and quote chars
    """

    chars = list(string.ascii_letters +
                 string.digits +
                 string.punctuation +
                 ' ')
    # remove '\' to avoid escaped char choices
    chars.remove('\\')

    return [char for char in chars if char not in delimiters()]


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
def time_table(rng):
    """Returns a function for building random tables of stringed times.

    Note:
        The format of the dates will be consistent across all table cells.
    """

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
        fmt = rng.choice(parsing.time_formats())
        cells = [time.strftime(fmt) for time  in times]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture
def date_table(rng):
    """Returns a function for building random tables of stringed dates.

    Note:
        The format of the dates will be consistent across all table cells.
    """

    fmt = rng.choice(parsing.date_formats())
    def make_table(rows, cols):
        """Returns a rows x cols table of dates."""

        cnt = rows * cols
        years = [rng.randint(1800, 2500) for _ in range(cnt)]
        months = [rng.randint(1, 12) for _ in range(cnt)]
        days = [rng.randint(1, 28) for _ in range(cnt)]
        dates = [datetime.date(y, m, d) for y, m, d in zip(years, months, days)]
        cells = [date.strftime(fmt) for date in dates]

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
def composite_table(
        rng,
        string_table,
        integer_table,
        float_table,
        enotation_table,
        time_table,
        date_table,
        datetime_table,
):
    """Returns a randomly shaped table a composite of single type tables
    supported by Tabbed."""

    args = locals()
    rng = args.pop('rng')

    def make_table(rows, cols):
        """Returns a rows x cols table of mixed table types."""

        # build each table type then conncatenate along columns
        subtables = [atable(rows, cols) for atable in args.values()]
        combined = [sum(row_tuple, start=[]) for row_tuple in zip(*subtables)]

        # randomly choose cols from combined
        transpose = list(zip(*combined))
        chosen = rng.sample(transpose, k=cols)

        # transpose back to cols by rows and return
        return list(zip(*chosen))

    return make_table


@pytest.fixture
def header(rng, valid_chars):
    """Returns a function for building a random valid header."""

    def make_header(cols, delimiter=','):
        """Returns a list of valid header names."""

        names = [''.join(rng.choices(valid_chars, k=15)) for _ in range(cols)]
        string = delimiter.join(names)
        line = rng.randint(0, 100)

        return Header(line, names, string)

    return make_header


@pytest.fixture
def repeating_header(rng, valid_chars):
    """Returns a function for building headers with repeating names."""

    def make_header(cols, delimiter=','):
        """Returns a list of valid header names with repeats of length cols."""

        # set cols//2 to be unique names and choose cols from this set
        cnt = max(cols//2, 1)
        unames = [''.join(rng.choices(valid_chars, k=15)) for _ in range(cnt)]
        names = rng.choices(unames, k=cols)
        string = delimiter.join(names)
        line = rng.randint(0, 100)

        return Header(line, names, string)

    return make_header


@pytest.fixture
def delimited_metadata(rng, valid_chars):
    """Returns a function for building metadatas that use delimiters.

    Metadata may not include delimiters but to ensure headers are detected
    correctly we test metadata that can look like a header (i.e. it has
    delimiters).
    """

    def make_metadata(delimiter=','):
        """Constructs a metadata string with delimiters."""

        num_lines = rng.randint(1, 30)
        cell_counts = [rng.randint(1, 8) for _ in range(num_lines)]

        lines = []
        for cell_count in cell_counts:
            line = [''.join(rng.choices(valid_chars, k=16)) for _ in range(cell_count)]
            lines.append(delimiter.join(line))

        return '\n'.join(lines)

    return make_metadata


@pytest.fixture
def empty_metadata():
    """Returns a metadata with only new line characters."""

    return '\n'.join([''] * 10)


@pytest.fixture
def skipping_metadata(rng, valid_chars):
    """Returns a metadata with a blank line."""

    delimiter = rng.choice(delimiters)
    rows = list(batched(rng.choices(valid_chars, k=100), 5))
    lines = [delimiter.join(row) for row in rows]
    lines[3] = ''

    return '\n'.join(lines)


# TODO WIP here
@pytest.fixture
def composite_file(rng, delimited_metadata, header, composite_table):
    """ """

    def make_file(shape):
        """ """

        delimiter = rng.choice(delimiters())
        rows, cols = shape
        metastr = delimited_metadata(delimiter=delimiter)
        headstr = header(cols, delimiter=delimiter).string
        lines = [delimiter.join(row) for row in composite_table(rows, cols)]
        lines.insert(0, headstr)
        lines.insert(0, metastr)
        text = '\n'.join(lines)

        outfile = tempfile.TemporaryFile(mode='w+')
        yield outfile

        print('Removing temp file')
        outfile.close()

    return make_file





# ##############
# Header Tests #
# ##############

def test_header_names(header):
    """Validates header names contain no spaces and has correct length."""

    # make a header of 20 columns with a '\t' delimiter
    aheader = header(20)
    has_empty = any(' ' in s for s in aheader.names)

    assert has_empty is False and len(aheader.names) == 20


def test_header_uniqueness(repeating_header):
    """Validates header names are unique when given repeating header names."""

    # make a 30 column header with repeating names
    aheader = repeating_header(30)

    assert len(set(aheader.names)) == 30


def test_header_immutability(header):
    """Asserts the immmutability of a header instance."""

    aheader = header(4)
    with pytest.raises(AttributeError) as err:
        aheader.names = 'a b c d'.split()


##################
# Metadata Tests #
# ################

def test_metadata_immutability(delimited_metadata):
    """Asserts the immutability of a MetaData instance"""

    meta = delimited_metadata()
    with pytest.raises(AttributeError) as err:
        meta.string = 'the cat and the fiddle'


#################
# Sniffer Tests #
#################












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

    print(date_table(5,6))

    assert True
"""

"""
def test_table(composite_table):

    composite = composite_table(20, 5)
    print('shape =', len(composite), len(composite[0]))
    for row in composite:
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

"""
def test_skippingmetadata(skipping_metadata):

    print(skipping_metadata)

    assert True
"""

def test_textfile(composite_file):
    
    outfile = composite_file((20, 5))
    with open(outfile, 'rb') as fp:
        for row in fp:
            print(row)
