"""A module for testing Tabbed's sniffer. Test are conducted on temporary files
with known metadata, header and data sections. The writing, sniffing and
destruction of these temporary files during testing can take time. The SEEDS,
DELIMITERS, and COLUMNS globals can be changed to alter the number of random
files per test.
"""

from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
import functools
import itertools
import random
import string
import tempfile
from types import SimpleNamespace
import warnings

from clevercsv.dialect import SimpleDialect
import pytest

from tabbed.sniffing import Header
from tabbed.sniffing import MetaData
from tabbed.sniffing import Sniffer
from tabbed.utils import parsing

# number of test to run per test is SEEDS * DELIMITERS * COLUMNS
SEEDS = range(10)
DELIMITERS = [',', ';', '|', '\t']
COLUMNS = [1, 4, 8, 12, 16]


@pytest.fixture(params=SEEDS)
def rng(request):
    """Returns a random number generator."""

    random.seed(request.param)
    return random


@pytest.fixture(params=DELIMITERS)
def delimiter(request):
    """Returns a delimiter."""

    return request.param


@pytest.fixture(params=COLUMNS)
def columns(request):
    """Returns a column count."""

    return request.param


@pytest.fixture
def rows():
    """Returns the number of rows of the data section of a sample."""

    return 100


@pytest.fixture
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

    return [char for char in chars if char not in DELIMITERS]


#####################
# Metadata fixtures #
#####################

@pytest.fixture
def unstructured_metadata():
    """Returns a Metadata instance representing a non-delimited paragraph."""

    verses = [
        'Hey diddle diddle!',
        'The cat and the fiddle.',
        'The cow jumped over the moon.',
        'The little dog laughed to see such sport!',
        'And the dish ran away with the spoon.'
        ]

    metastring = '\n'.join(verses)
    return MetaData((0, len(verses)), metastring)


@pytest.fixture
def structured_metadata(delimiter):
    """Returns delimited lines of metadata."""

    keys = 'metaline_0 metaline_1 metaline_2 metaline_3 metaline_4'.split()
    values = [str(v) for v in [0,  1, 2, 3, 4]]

    metastring = '\n'.join([(k + delimiter + v) for k, v in zip(keys, values)])
    return MetaData((0, len(keys)), metastring)


@pytest.fixture
def skipping_unstructured_metadata(unstructured_metadata):
    """Returns lines of unstructured metadata with blank lines present."""

    verses = unstructured_metadata.string.splitlines()
    verses[1] = '\n'
    verses[-1] = '\n'

    metastring = '\n'.join(verses)
    return MetaData((0, len(verses)), metastring)


@pytest.fixture
def skipping_structured_metadata(structured_metadata):
    """Returns structured metadata with blank lines present."""

    lines = structured_metadata.string.splitlines()
    lines[2] = '\n'

    metastring = '\n'.join(lines)
    return MetaData((0, len(lines)), metastring)


###################
# Header Fixtures #
###################

@pytest.fixture
def header_names(rng, delimiter, columns):
    """Returns a list of header names.

    Note: until metadata is formed we do not know the line number of a Header
    instance so we delay its construction.
    """

    triplets = itertools.combinations(string.ascii_letters, 3)
    return [''.join(next(triplets)) for _ in range(columns)]


@pytest.fixture
def repeat_header_names(delimiter, columns):
    """Returns a delimited string of header names with repeats."""


    return ['a' if i % 2 == 0 else 'b' for i in range(columns)]


#################
# Data Fixtures #
#################

@pytest.fixture()
def string_table(rng, valid_chars):
    """Returns a function for building random tables of valid string chars."""

    def make_table(rows, cols):
        """Returns a rows x cols table of strings of random lengths."""

        cnt = rows * cols
        lengths = [rng.randint(3, 15) for _ in range(cnt)]
        cells = [''.join(rng.choices(valid_chars, k=l)) for l in lengths]

        return [list(row) for row in itertools.batched(cells, cols)]

    return make_table


@pytest.fixture
def rstring_table(rng, valid_chars):
    """Returns a function for building a table with column values chosen from
    a subset of valid chars.

    Most data sections comprised of string data will have repeated values in
    columns. Tabbed uses this property to help identify header and metadata
    sections.
    """

    def make_table(rows, cols):
        """Returns a rows x cols table of strings of random lengths."""

        result = []
        subsets = [rng.choices(valid_chars, k=4) for col in range(cols)]
        for row in range(rows):
            result.append([rng.choice(subset) for subset in subsets])

        return result

    return make_table



@pytest.fixture
def integer_table(rng):
    """Returns a function for building random tables of stringed integers."""

    def make_table(rows, cols):
        """Returns a rows x cols table of integers between -1000 and 1000."""

        cnt = rows * cols
        cells = [str(rng.randint(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in itertools.batched(cells, cols)]

    return make_table


@pytest.fixture
def float_table(rng):
    """Returns a function for building random tables of stringed floats."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [str(rng.uniform(-1000, 1000)) for _ in range(cnt)]

        return [list(row) for row in itertools.batched(cells, cols)]

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
        cells = [str(complex(*tup)) for tup in itertools.batched(parts, 2)]

        return [list(row) for row in itertools.batched(cells, cols)]

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
                time(hour=h, minute=m, second=s, microsecond=mu)
                for h, m, s, mu in zip(hours, mins, secs, micros)
                ]
        fmt = rng.choice(parsing.time_formats())
        cells = [time.strftime(fmt) for time  in times]

        return [list(row) for row in itertools.batched(cells, cols)]

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
        dates = [date(y, m, d) for y, m, d in zip(years, months, days)]
        cells = [date.strftime(fmt) for date in dates]

        return [list(row) for row in itertools.batched(cells, cols)]

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

        return [list(row) for row in itertools.batched(cells, cols)]

    return make_table


@pytest.fixture
def table(
        rng,
        rows,
        columns,
        string_table,
        integer_table,
        float_table,
        complex_table,
        time_table,
        date_table,
        datetime_table,
):
    """Returns a rows x cols table of randomly selected data of each table type."""

    args = locals()
    rng = args.pop('rng')
    p = args.pop('columns')
    n = args.pop('rows')

    types = [str, int, float, complex, time, date, datetime]
    tables = dict(zip(types, [atable(n, p) for atable in args.values()]))
    # choose the types for each column and then the data
    chosen_types = rng.choices(list(tables), k=p)
    chosen_data = [rng.choice(list(zip(*tables[typ]))) for typ in chosen_types]
    # transpose data back to rows x columns shape
    data = list(zip(*chosen_data))

    return chosen_types, data


###################
# File Fixtures #
###################

@pytest.fixture
def umeta_header_file(unstructured_metadata, header_names, table, delimiter):
    """Returns an infile with unstructured metadata, header & data sections."""

    meta = unstructured_metadata
    hstring = delimiter.join(header_names)
    hline = meta.lines[-1]
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, hstring, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, Header(hline, header_names, hstring)

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def umeta_header_rstring_file(
        unstructured_metadata,
        header_names,
        rstring_table,
        delimiter,
        rows):
    """Returns an infile with unstructured metadata, header and a string only
    data section."""

    meta = unstructured_metadata
    hstring = delimiter.join(header_names)
    hline = meta.lines[-1]
    # make a string
    tabled = rstring_table(rows, len(header_names))
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, hstring, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, Header(hline, header_names, hstring)

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def smeta_header_file(structured_metadata, header_names, table, delimiter):
    """Returns an infile with structured metadata, header and data sections."""

    meta = structured_metadata
    hstring = delimiter.join(header_names)
    hline = meta.lines[-1]
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, hstring, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, Header(hline, header_names, hstring)

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def smeta_file(structured_metadata, table, delimiter):
    """Returns a file with structured metadata and no header."""

    meta = structured_metadata
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, meta

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def smeta_rstring_file(structured_metadata, rstring_table, delimiter, rows, columns):
    """Returns a file with structured metadata, no header, and repeating string
    data."""

    meta = structured_metadata
    tabled = rstring_table(rows, columns)
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, meta

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def uskipmeta_header_file(skipping_unstructured_metadata, header_names, table, delimiter):
    """Returns an infile with skipping unstructured metadata, header and data sections."""

    meta = skipping_unstructured_metadata
    hstring = delimiter.join(header_names)
    hline = meta.lines[-1]
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, hstring, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, Header(hline, header_names, hstring)

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def sskipmeta_header_file(skipping_structured_metadata, header_names, table, delimiter):
    """Returns an infile with skipping structured metadata, header and data sections."""

    meta = skipping_structured_metadata
    hstring = delimiter.join(header_names)
    hline = meta.lines[-1]
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, hstring, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, Header(hline, header_names, hstring)

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def empty_metadata_file(header_names, table, delimiter):
    """Returns an infile with header and data section only."""

    hstring = delimiter.join(header_names)
    hline = 0
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([hstring, datastring])

    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, Header(hline, header_names, hstring)

    # on Teardown, close and remove temp file
    outfile.close()


@pytest.fixture
def empty_header_file(unstructured_metadata, table, delimiter):
    """Returns an infile with unstructured metadata and data section only."""

    meta = unstructured_metadata
    types, tabled = table
    datastring = '\n'.join([delimiter.join(row) for row in tabled])

    text = '\n'.join([meta.string, datastring])
    # complete setup by writing to a temp file
    outfile = tempfile.TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)
    yield outfile, delimiter, None

    # on Teardown, close and remove temp file
    outfile.close()


###########
# Helpers #
###########

def safe_sniff(infile, delimiter):
    """Clevercsv may fail to detect the dialect which disrupts testing. This
    wrapper ensures a dialect (not necessarily the correct one) is found prior
    to testing."""

    sniffer = Sniffer(infile)

    msg = 'Dialect was not correctly detected... using known dialect.'
    if sniffer.dialect and sniffer.dialect.delimiter in DELIMITERS:
        return sniffer
    else:
        warnings.warn(msg)
        sniffer.dialect = SimpleDialect(delimiter, '"', None)

    return sniffer

# ########################
# Header Dataclass Tests #
# ########################

def test_header_names(header_names, columns):
    """Validates header names contain no spaces and has correct length."""

    aheader = Header(line=None, names=header_names, string=None)
    has_empty = any(' ' in s for s in aheader.names)

    assert has_empty is False and len(aheader.names) == columns


def test_header_uniqueness(repeat_header_names, columns):
    """Validates header names are unique when given repeating header names."""

    aheader = Header(line=None, names=repeat_header_names, string=None)

    assert len(set(aheader.names)) == columns


#####################
# Dialect Detection #
#####################

def test_dialect_unstruct_meta(umeta_header_file):
    """Validate the Sniffers detected dialect for unstructured metadata"""

    infile, delimiter, header = umeta_header_file
    sniffer = safe_sniff(infile, delimiter)
    assert sniffer.dialect.delimiter == delimiter


def test_dialect_struct_meta(smeta_header_file):
    """validate the sniffers detected dialect for structured metadata."""

    infile, delimiter, header = smeta_header_file
    sniffer = safe_sniff(infile, delimiter)
    assert sniffer.dialect.delimiter == delimiter


def test_dialect_skipping_ustruct_meta(uskipmeta_header_file):
    """validate the sniffers detected dialect for skipping unstructured metadata."""

    infile, delimiter, header = uskipmeta_header_file
    sniffer = safe_sniff(infile, delimiter)
    assert sniffer.dialect.delimiter == delimiter


def test_dialect_skipping_struct_meta(sskipmeta_header_file):
    """validate the sniffers detected dialect for skipping structured metadata."""

    infile, delimiter, header = sskipmeta_header_file
    sniffer = safe_sniff(infile, delimiter)
    assert sniffer.dialect.delimiter == delimiter


def test_dialect_no_metadata(empty_metadata_file):
    """Validate the Sniffers detected dialect for a file without metadata."""

    infile, delim, _ = empty_metadata_file
    sniffer = safe_sniff(infile, delim)
    assert sniffer.dialect.delimiter == delim


def test_dialect_no_header(empty_header_file):
    """Validate the Sniffers detected dialect for a file without a header."""

    infile, delim, _ = empty_header_file
    sniffer = safe_sniff(infile, delim)
    assert sniffer.dialect.delimiter == delim


####################
# Property changes #
####################

def test_start_change(umeta_header_file):

    infile, delimiter, header = umeta_header_file
    sniffer = safe_sniff(infile, delimiter)
    old_rows = sniffer.rows
    sniffer.start = 4
    new_rows = sniffer.rows

    assert old_rows[4] == new_rows[0]


def test_amount_change(umeta_header_file):
    """Validate sniffing sample change when sniffing amount changes."""

    infile, delim, _ = umeta_header_file
    sniffer = safe_sniff(infile, delim)
    old_rows = sniffer.rows
    sniffer.amount = 10
    new_rows = sniffer.rows

    assert new_rows == old_rows[:10]


def test_lines(umeta_header_file):
    """Validates the line numbers from an infile file on skip changes."""

    infile, delim, header = umeta_header_file
    file_length = sum(1 for _ in infile)

    sniffer = safe_sniff(infile, delim)

    skips = list(range(2, 13))
    # enumerate all lines not in skips and slice amount of them
    lines = [x for x in range(file_length) if x not in skips]
    expected = lines[:sniffer.amount]

    # set sniffer skips and validate lines are expected
    sniffer.skips = skips
    assert sniffer.lines == expected


def test_skip_change(umeta_header_file):
    """Validate sniffing sample changes when skip parameter changes."""

    infile, delim, header = umeta_header_file
    sniffer = safe_sniff(infile, delim)
    lines = sniffer.lines
    sniffer.skips = [33, 45, 77]
    assert set(sniffer.lines).isdisjoint(sniffer.skips)


def test_set_dialect(smeta_header_file):
    """Validate the dialect is changed when set to a new simple dialect."""

    d = SimpleDialect(',', '', None)
    infile, delimiter, header = smeta_header_file
    sniffer = safe_sniff(infile, delimiter)
    sniffer.dialect = d
    assert sniffer.dialect.delimiter == ','


def test_start_EOF(umeta_header_file):
    """Validate that setting start to > file length raises StopIteration."""

    infile, delim, _ = umeta_header_file
    size = sum(1 for line in infile)
    sniffer = safe_sniff(infile, delim)
    with pytest.raises(StopIteration):
        sniffer.start = size + 10


###################
# Types Detection #
###################

def test_detected_types(umeta_header_file, table):
    """Validate that the detected types match the known table types."""

    infile, delim, _ = umeta_header_file
    sniffer = safe_sniff(infile, delim)
    types, _ = table
    detected, _ = sniffer.types(poll=10)
    assert detected == types


####################
# Format Detection #
####################

def test_detected_fmts(smeta_header_file, table):
    """Validate that detected formats match expected formats from table."""

    infile, delim, _ = smeta_header_file
    sniffer = safe_sniff(infile, delim)
    types, _ = table
    detected_fmts, consistent = sniffer.datetime_formats(poll=5)

    fmts = {
            time: parsing.time_formats(),
            date: parsing.date_formats(),
            datetime: parsing.datetime_formats(),
        }

    for typed, fmt in zip(types, detected_fmts):
        assert fmt in fmts[typed] if fmt else True


####################
# Header detection #
####################

def test_header_mixed_data(umeta_header_file):
    """Validates the line number of the sniffed header for a file
    containing mixed data section types."""

    infile, delim, head = umeta_header_file
    sniffer = safe_sniff(infile, delim)
    if not all(typ == str for typ in sniffer.types(poll=10)[0]):
        # test files with mixed types only here, only string types require
        # repeating strings see test below
        sniffer.amount = 20
        aheader = sniffer.header()

        assert aheader.line == head.line

def test_header_stringed_data(umeta_header_rstring_file):
    """Validates the line number of the sniffed header for a file containing
    only string type in the data section."""

    infile, delim, head = umeta_header_rstring_file
    sniffer = safe_sniff(infile, delim)
    aheader = sniffer.header(poll=20)

    assert aheader.line == head.line


######################
# Metadata Detection #
######################

def test_metadata_mixed_types(smeta_file):
    """Validate the detected metadata lines for a file with no header and data
    of mixed type."""

    infile, delim, meta = smeta_file
    sniffer = safe_sniff(infile, delim)
    if not all(typ == str for typ in sniffer.types(poll=10)[0]):
        # test files with mixed types only here, only string types require
        # repeating strings see test below
        sniffer.amount = 20
        ameta = sniffer.metadata(header=None)
        assert ameta.lines == meta.lines


def test_metadata_string_type(smeta_rstring_file):
    """Test metadata detection when given a file of all strings and no header."""

    infile, delim, meta = smeta_rstring_file
    sniffer = safe_sniff(infile, delim)
    ameta = sniffer.metadata(header=None, poll=20)

    assert ameta.lines == meta.lines
