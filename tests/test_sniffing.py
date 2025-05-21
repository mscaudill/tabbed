"""A pytest module to test Tabbed's Sniffer and associated utilities. This
module builds temporary text files containing mixtures of Tabbed's supported
numeric and datetime types.
"""

import functools
import tempfile
import string
import datetime
import pytest
import random
from itertools import batched, chain

from clevercsv.dialect import SimpleDialect

from tabbed.sniffing import Header, MetaData, Sniffer
from tabbed.utils import parsing


NUM_TEST = 100

@pytest.fixture(params=range(NUM_TEST), scope='module')
def rng(request):
    """Returns a random number generator."""

    random.seed(request.param)
    return random


def delimiters():
    """Returns all of tabbed's compatible delimiters."""

    return [',', ';', '|', '\t']


@pytest.fixture(scope='module')
def valid_chars():
    """Returns a string of all valid characters.

    Invalid characters are a delimiter and quote chars
    """

    # modify digits so they cant be an accidental integer
    digits = ['_' + d for d in string.digits]
    # single j chars are convertible to complex -> remove them
    letters = string.ascii_letters.replace('j', '')
    letters = letters.replace('J', '')
    chars = list(letters + string.punctuation + ' ')
    chars += digits
    # remove '\' to avoid escaped char choices
    chars.remove('\\')

    return [char for char in chars if char not in delimiters()]


@pytest.fixture(scope='module')
def shape(rng):
    """Returns a rows, columns shape tuple for building tables."""

    # set min/max rows and columns
    rows = rng.randint(30, 300)
    cols = rng.randint(3, 15)

    return rows, cols


@pytest.fixture(scope='module')
def string_table(rng, valid_chars):
    """Returns a function for building random tables of valid string chars."""

    def make_table(rows, cols):
        """Returns a rows x cols table of strings of random lengths."""

        cnt = rows * cols
        lengths = [rng.randint(3, 15) for _ in range(cnt)]
        cells = [''.join(rng.choices(valid_chars, k=l)) for l in lengths]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture(scope='module')
def rstring_table(rng):
    """Returns a function for building random tables of repeated strings."""

    fruits = [
            'apples',
            'oranges',
            'pears',
            'peaches',
            'kiwis',
            'watermelon',
            'jack_fruit',
            'melons',
            ]
    def make_table(rows, cols):
        """Returns a rows x cols table of items from fruits list."""

        cnt = rows * cols
        cells = rng.choices(fruits, k=cnt)

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture(scope='module')
def integer_table(rng):
    """Returns a function for building random tables of stringed integers."""

    def make_table(rows, cols):
        """Returns a rows x cols table of integers between -1000 and 1000."""

        cnt = rows * cols
        cells = [str(rng.randint(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture(scope='module')
def float_table(rng):
    """Returns a function for building random tables of stringed floats."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [str(rng.uniform(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
def enotation_table(rng):
    """Returns a function for building random tables of stringed scientific
    notation values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of E notation floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [f'{rng.uniform(-1000, 1000):.2E}' for _ in range(cnt)]

        return [list(row) for row in batched(cells, cols)]

    return make_table


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
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

    def make_header(cols, delimiter=',', line=None):
        """Returns a list of valid header names."""

        names = [''.join(rng.choices(valid_chars, k=15)) for _ in range(cols)]
        string = delimiter.join(names)

        return Header(line, names, string)

    return make_header


@pytest.fixture
def repeating_header(rng, valid_chars):
    """Returns a function for building headers with repeating names."""

    def make_header(cols, delimiter=',', line=None):
        """Returns a list of valid header names with repeats of length cols."""

        # set cols//2 to be unique names and choose cols from this set
        cnt = max(cols//2, 1)
        unames = [''.join(rng.choices(valid_chars, k=15)) for _ in range(cnt)]
        names = rng.choices(unames, k=cols)
        string = delimiter.join(names)

        return Header(line, names, string)

    return make_header


@pytest.fixture
def meta(rng, valid_chars):
    """Returns a function for building metadata with no delimiters."""

    def make_metadata():
        """Constructs a metadata string without delimiters."""

        num_lines = rng.randint(1, 10)
        widths = rng.choices(range(100), k=num_lines)
        lines = [''.join(rng.choices(valid_chars, k=w)) for w in widths]
        metastring = '\n'.join(lines)

        return MetaData((0, num_lines), metastring)


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

        num_lines = rng.randint(1, 10)
        cell_counts = [rng.randint(1, 8) for _ in range(num_lines)]

        lines = []
        for cell_count in cell_counts:
            line = [''.join(rng.choices(valid_chars, k=16)) for _ in range(cell_count)]
            lines.append(delimiter.join(line))

        metastring = '\n'.join(lines)

        return MetaData((0, num_lines), metastring)

    return make_metadata


@pytest.fixture
def skipping_metadata(rng, valid_chars):
    """Returns a metadata with a blank line."""

    def make_metadata(delimiter=','):
        """Constructs delimited metadata that skips a line."""

        num_lines = 10
        rows = list(batched(rng.choices(valid_chars, k=100), num_lines))
        lines = [delimiter.join(row) for row in rows]
        lines[3] = ''

        metastring = '\n'.join(lines)

        return MetaData((0, num_lines), metastring)

    return make_metadata


################################
# Temporary Text File Fixtures #
# ##############################

@pytest.fixture
def standard_file(rng, shape, delimited_meta, header, composite_table):
    """A file with delimited metadata, header and mixed type data table."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata, header and table
    metadata = delimited_meta(delimiter=delimiter)
    head = header(cols, delimiter=delimiter, line=metadata.lines[-1])
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    lines = [metadata.string, head.string] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, head

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def float_file(rng, shape, meta, header, float_table):
    """A file with undelimited metadata, header and float type data table."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata, header and table
    metadata = meta()
    head = header(cols, delimiter=delimiter, line=metadata.lines[-1])
    tabled = [delimiter.join(row) for row in float_table(rows, cols)]
    lines = [metadata.string, head.string] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, head

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def rstring_file(rng, shape, meta, header, rstring_table):
    """A file with some consistency in the strings of the data section."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct header and table
    metadata = meta()
    head = header(cols, delimiter=delimiter, line=metadata.lines[-1])
    tabled = [delimiter.join(rw) for rw in rstring_table(rows, cols)]
    lines = [metadata.string, head.string] + tabled
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
    head = header(cols, delimiter=delimiter, line=0)
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    lines = [head.string] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, head

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def empty_header_file(rng, shape, meta, header, composite_table):
    """A file with a non-delimited metadata, no header & mixed table type."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata and table
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    metadata = meta()
    lines = [metadata.string] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, metadata

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


@pytest.fixture
def skipping_meta_file(rng, shape, skipping_metadata, header, composite_table):
    """A file with a blank metadata line."""

    delimiter = rng.choice(delimiters())
    rows, cols = shape

    # construct metadata, header and table
    metadata = skipping_metadata(delimiter=delimiter)
    head = header(cols, delimiter=delimiter, line=metadata.lines[-1])
    tabled = [delimiter.join(row) for row in composite_table(rows, cols)]
    lines = [metadata.string, head.string] + tabled
    text = '\n'.join(lines)

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, head


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

def has_dialect(testfunc):
    """"Wraps a test function to ensure a file from a file fixture has
    a detected dialect.

    Clevercsv may fail to detect the dialect which disrupts testing. This
    decorator ensures a dialect (not necessarily the correct one) is found prior
    to testing.
    """

    @functools.wraps(testfunc)
    def decorator(**kwargs):
        """Returns a test functions result if dialect is known and asserts True
        otherwise.

        Pytest stores fixtures to kwargs. This wrapper just assumes a single
        fixture and no variables. Future versions could use inspect to iprove
        this.
        """

        infile, delimiter, _ = list(kwargs.values())[0]
        sniffer = Sniffer(infile)
        if sniffer.dialect and sniffer.dialect.delimiter in delimiters():
            return testfunc(**kwargs)
        else:
            assert True

    return decorator


@has_dialect
def test_dialect(standard_file):
    """Validate the Sniffers detected dialect for a file with header and
    metadata.

    Notes:
        Our metadata fixture is at most 30 lines and the default sniffing sample
        amount is 100 lines. This will ensure data rows are seen in sniffing.
    """

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    assert sniffer.dialect.delimiter == delim


def test_set_dialect(standard_file):
    """Validate that dialects with non-valid escape and quote chars are amended
    by dialect setter."""

    d = SimpleDialect(',', '', None)
    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    sniffer.dialect = d
    assert sniffer.dialect.escapechar == None
    assert sniffer.dialect.quotechar == '"'


@has_dialect
def test_dialect_no_metadata(empty_metadata_file):
    """Validate the Sniffers detected dialect for a file without metadata."""

    infile, delim, _ = empty_metadata_file
    sniffer = Sniffer(infile)
    assert sniffer.dialect.delimiter == delim


@has_dialect
def test_dialect_no_header(empty_header_file):
    """Validate the Sniffers detected dialect for a file without a header"""

    infile, delim, _ = empty_header_file
    sniffer = Sniffer(infile)
    assert sniffer.dialect.delimiter == delim


@has_dialect
def test_start_change(standard_file):
    """Validate sniffing sample changes when sniff start changes."""

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    old_rows = sniffer.rows
    sniffer.start = 4
    new_rows = sniffer.rows

    assert old_rows[4] == new_rows[0]


@has_dialect
def test_amount_change(standard_file):
    """Validate sniffing sample change when sniffing amount changes."""

    infile, delim, _ = standard_file
    sniffer = Sniffer(infile)
    old_rows = sniffer.rows
    sniffer.amount = 10
    new_rows = sniffer.rows

    assert new_rows == old_rows[:10]


@has_dialect
def test_lines(standard_file):
    """Validates the line numbers on a standard file."""

    infile, delim, header = standard_file
    file_length = sum(1 for _ in infile)

    sniffer = Sniffer(infile)

    skips = list(range(2, 13))
    # enumerate all lines not in skips and slice amount of them
    lines = [x for x in range(file_length) if x not in skips]
    expected = lines[:sniffer.amount]

    # set sniffer skips and validate lines are expected
    sniffer.skips = skips
    assert sniffer.lines == expected


@has_dialect
def test_skip_change(standard_file):
    """Validate sniffing sample changes when skip parameter changes."""

    infile, delim, header = standard_file
    sniffer = Sniffer(infile, amount=200)
    old_rows = sniffer.rows
    sniffer.skips = [1, 2, 5]
    sniffer.amount = 100
    new_rows = sniffer.rows

    expected = [row for idx, row in enumerate(old_rows) if idx not in
            sniffer.skips][:sniffer.amount]

    assert new_rows == expected


def test_start_EOF(standard_file):
    """Validate that setting start to > file length raises StopIteration."""

    infile, delim, _ = standard_file
    size = sum(1 for line in infile)
    sniffer = Sniffer(infile)
    with pytest.raises(StopIteration):
        sniffer.start = size + 10


@has_dialect
def test_amount_EOF(standard_file):
    """Validate that an amount that reads off a file gives the whole file."""

    infile, delim, _ = standard_file
    size = sum(1 for line in infile)
    sniffer = Sniffer(infile)
    sniffer.amount = size + 10

    assert len(sniffer.rows) == size


# Type checking test are carried out in-full in test_parsing -- just check
# 'types' method is error free
@has_dialect
def test_float_types(float_file):
    """Validate that the sniffer correctly detects all float type."""

    infile, delim, header = float_file
    sniffer = Sniffer(infile)
    types, consistent = sniffer.types(poll=5)

    assert [float] * len(header.names) == types


####################
# Header detection #
####################
@pytest.mark.slow
@has_dialect
def test_header_standard(standard_file):
    """Validates the line number of the sniffed header for a standard file
    containing mixed data section types."""

    infile, delim, head = standard_file
    sniffer = Sniffer(infile)
    aheader = sniffer.header()

    assert aheader.line == head.line


@pytest.mark.slow
@has_dialect
def test_header_allstring(rstring_file):
    """Validate the header is correctly detected for a data section containing
    all string types."""

    infile, delim, head = rstring_file
    sniffer = Sniffer(infile)
    aheader = sniffer.header(poll=20)

    assert aheader.line == head.line


@pytest.mark.slow
@has_dialect
def test_header_no_meta(empty_metadata_file):
    """Validates header detection when no metadata is present."""

    infile, delim, head = empty_metadata_file
    sniffer = Sniffer(infile)
    aheader = sniffer.header()

    assert aheader.line == head.line


@pytest.mark.slow
@has_dialect
def test_header_skipping_metadata(skipping_meta_file):
    """Validates header is correctly detected if metadata has blank lines."""

    infile, delim, head = skipping_meta_file
    sniffer = Sniffer(infile)
    aheader = sniffer.header()

    assert aheader.line == head.line


@pytest.mark.slow
@has_dialect
def test_header_no_header(empty_header_file):
    """Validates that no header is detected for a file with no header."""

    infile, delim, _ = empty_header_file
    sniffer = Sniffer(infile)
    header = sniffer.header()

    assert header.string is None


######################
# Metadata Detection #
######################

@pytest.mark.slow
@has_dialect
def test_metadata_standard(standard_file):
    """Validates the metadata locations for a standard file."""

    infile, delim, head = standard_file
    sniffer = Sniffer(infile)
    aheader = sniffer.header()
    meta = sniffer.metadata(aheader)

    assert meta.lines == (0, aheader.line)


@pytest.mark.slow
@has_dialect
def test_metadata_no_header(empty_header_file):
    """Validates the metadata location for a file with no header."""

    infile, delim, expected = empty_header_file
    sniffer = Sniffer(infile)
    meta = sniffer.metadata(header=None)

    assert meta.lines == expected.lines


@pytest.mark.slow
@has_dialect
def test_metadata_no_metadata_no_header(empty_meta_empty_header_file):
    """Validates the metadata string is None when no metadata is present."""

    infile, delim, _ = empty_meta_empty_header_file
    sniffer = Sniffer(infile)

    assert sniffer.metadata(None).string is None

