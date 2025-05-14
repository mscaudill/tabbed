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
def shape(rng):
    """Returns a rows, columns shape tuple for building tables."""

    # set min/max rows and columns
    rows = rng.randint(10, 100)
    cols = rng.randint(1, 10)

    return rows, cols


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
    """Returns a table of mixed stringed types supported by Tabbed."""

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
def meta(rng, valid_chars):
    """Returns a function for building metadata with no delimiters."""

    def make_metadata():
        """Constructs a metadata string without delimiters."""

        num_lines = rng.randint(1, 30)
        widths = rng.choices(range(100), k=num_lines)
        lines = [''.join(rng.choices(valid_chars, k=w)) for w in widths]

        return '\n'.join(lines)

    return make_metadata


@pytest.fixture
def delimited_meta(rng, valid_chars):
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
def empty_meta():
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


#########################################
# Temporary Delimited Files For Testing #
# #######################################

@pytest.fixture
def standard_file(rng, shape, delimited_meta, header, composite_table):
    """A file with delimited metadata, header and mixed type data table."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata, header and table
    metadata = delimited_meta(delimiter=delimiter)
    head = header(cols, delimiter=delimiter)
    heading = head.string
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    lines = [metadata, heading] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, head

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def empty_metadata_file(rng, shape, header, composite_table):
    """A file with no metadata, a header and a mixed type data table."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct header and table
    head = header(cols, delimiter=delimiter)
    heading = head.string
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    lines = [heading] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, head.line

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def empty_header_file(rng, shape, meta, header, composite_table):
    """A file with a non-delimited metadata, no header & mixed table type."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata and table
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    lines = [meta()] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, None

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def empty_meta_empty_header_file(rng, shape, composite_table):
    """A file with no metadata and no header and a a mixed type data table."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata and table
    lines = [delimiter.join(row) for row in composite_table(rows, cols)]
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, None

    # on Teardown, close and remove temp file
    outfile.close()


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

def test_metadata_immutability(delimited_meta):
    """Asserts the immutability of a MetaData instance"""

    meta = delimited_meta()
    with pytest.raises(AttributeError) as err:
        meta.string = 'the cat and the fiddle'


#################
# Sniffer Tests #
#################

def test_line_count(standard_file):
    """Validate the Sniffer's line count."""

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    measured = sniffer.line_count
    expected = len(infile.readlines())

    assert measured == expected


def test_dialect(standard_file):
    """Validate the Sniffers detected dialect for a file with header and
    metadata.

    Notes:
        Our metadata fixture is at most 30 lines and the default sniffing sample
        amount is 100 lines. This will ensure data rows are seen in sniffing.
    """

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    measured = sniffer.dialect.delimiter

    assert measured == delim


def test_dialect_no_metadata(empty_metadata_file):
    """Validate the Sniffers detected dialect for a file without metadata."""

    infile, delim, _ = empty_metadata_file
    sniffer = Sniffer(infile)
    measured = sniffer.dialect.delimiter

    assert measured == delim


def test_dialect_no_header(empty_header_file):
    """Validate the Sniffers detected dialect for a file without a header"""

    infile, delim, _ = empty_header_file
    sniffer = Sniffer(infile)
    measured = sniffer.dialect.delimiter

    assert measured == delim


def test_start_change(standard_file):
    """Validate sniffing sample changes when sniff start changes."""

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    sample_rows = sniffer.rows()
    sniffer.start = 4

    assert sample_rows[4] == sniffer.rows()[0]


def test_amount_change(standard_file):
    """Validate sniffing sample change when sniffing amount changes."""


    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    sample_rows = sniffer.rows()
    sniffer.amount = min(sniffer.line_count, 20)

    assert sniffer.rows() == sample_rows[:20]


def test_skip_change(standard_file):
    """Validate sniffing sample changes when skip parameter changes."""

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    sample_rows = sniffer.rows()
    sniffer.skips = [1, 2, 5]
    expected = [row for idx, row in enumerate(sample_rows) if idx not in
            sniffer.skips]

    assert sniffer.rows() == expected


# TODO start here 5/15
def test_header_standard(standard_file):
    """Validates the line number of the sniffed header."""

    infile, delim, head = standard_file
    sniffer = Sniffer(infile)
    aheader = sniffer.header()
    for idx, row in enumerate(sniffer.rows()):
        print(idx, row)

    assert aheader.line == head.line






"""
def test_textfile(empty_metadata_file):

    print(empty_metadata_file.read())
"""


"""
def test_textfile(empty_header_file):

    print(empty_header_file.read())
"""
