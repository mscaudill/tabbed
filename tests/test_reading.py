"""A pytest module for testing Tabbed's reader and associated utilities. Thi
module builds temporary text files containing mixtures of Tabbed's supported
types.
"""

from datetime import time, date, datetime, timedelta
import random
from string import ascii_letters
from tempfile import TemporaryFile

import pytest

from tabbed.reading import Reader


# testing of other delimiters is carried out in test_sniffing
@pytest.fixture(params = [','])
def delimiter(request):
    """Returns a delimiter."""

    return request.param


@pytest.fixture
def metastring():
    """Returns a multiline metadata string."""

    lines = ("There were two cats of Killkeney who thought there was 1 cat too "
    "many. So they fought and they fit. And they scratched and the bit. Until "
    "instead of two cats there weren't any. \nA diner in Crue found a mouse in"
    " his stew. Said the waiter don't shout and wave it about.Or others will"
    "be wanting one too").split('. ')

    # return the metadata with an empty last line
    return '\n'.join(lines) + '\n'


@pytest.fixture
def headerstring(delimiter):
    """Returns a comma delimited header string for Tabbed's 7 supported data
    types."""

    names = 'integers floats complexes strings times dates datetimes'.split()
    return delimiter.join(names)


# For reader test we need s single example data file for deeper test using files
# with many type variants see test_sniffing.
@pytest.fixture()
def datastring(delimiter):
    """Returns a 100 line data string encoding each of Tabbed's supported
    data types."""

    cnt = 100
    random.seed(0)

    ints = [str(x) for x in range(cnt)]
    floats = [str(x + 0.1) for x in range(cnt)]
    complexes = [str(complex(x, x+1)) for x in range(cnt)]
    strings = [''.join(random.choices(ascii_letters, k=4)) for _ in range(cnt)]
    start_time = datetime.combine(date.today(), time(0,0))
    times = [(start_time + timedelta(seconds=x)).time() for x in range(cnt)]
    dates = [date(2000, 1, 1) + timedelta(hours=x*24) for x in range(cnt)]
    datetimes = [str(datetime.combine(d, t)) for d, t in zip(dates, times)]
    # convert times and dates to strings now
    times = [str(v) for v in times]
    dates = [str(v) for v in dates]

    data = list(zip(ints, floats, complexes, strings, times, dates, datetimes))
    row_strings = [delimiter.join(row) for row in data]

    return '\n'.join(row_strings)


@pytest.fixture
def metadata_header_data_file(metastring, headerstring, datastring):
    """Returns a temporary file withe metadata, header and data sections."""

    text = '\n'.join([metastring, headerstring, datastring])
    outfile = TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)

    yield outfile
    outfile.close()


@pytest.fixture
def metadata_data_file(metastring, datastring):
    """Returns a temporary file with metadata and data sections."""

    text = '\n'.join([metastring, datastring])
    outfile = TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)

    yield outfile
    outfile.close()


@pytest.fixture
def header_data_file(headerstring, datastring):
    """Returns a temporary file with header and data sections."""

    text = '\n'.join([headerstring, datastring])
    outfile = TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)

    yield outfile
    outfile.close()


@pytest.fixture
def data_file(datastring):
    """Returns a temporary file with only a data section."""

    text = datastring
    outfile = TemporaryFile(mode='w+')
    outfile.write(text)
    outfile.seek(0)

    yield outfile
    outfile.close()


############
# __init__ #
############

# These init tests are redundant as more intense test are in test_sniffing
def test_init_header_0(metadata_header_data_file, headerstring):
    """Test reader's init correctly identifies the header."""

    reader = Reader(metadata_header_data_file)
    delimiter = reader.sniffer.dialect.delimiter
    assert reader.header.names == headerstring.split(delimiter)


def test_init_header_1(header_data_file, headerstring):
    """Test reader init correctly identifies the header when no metadata."""

    reader = Reader(header_data_file)
    delimiter = reader.sniffer.dialect.delimiter
    assert reader.header.names == headerstring.split(delimiter)


def test_init_header_2(data_file):
    """Test reader init correctly identifies no header when no header and no
    metadata."""

    reader = Reader(data_file)
    assert reader.header.names == [f'Column_{i}' for i in range(7)]


def test_init_header_3(metadata_data_file):
    """Test reader init correctly identifies header when metadata and no header
    is present."""

    reader = Reader(metadata_data_file)
    assert reader.header.names == [f'Column_{i}' for i in range(7)]


def test_init_tabulator(metadata_header_data_file, headerstring):
    """Ensure tabulator instance is correctly initialized."""

    reader = Reader(metadata_header_data_file)
    delimiter = reader.sniffer.dialect.delimiter
    assert reader.header.names == headerstring.split(delimiter)


###########################
# Sniffer property change #
###########################

def test_sniffer_change_sniffer(metadata_header_data_file):
    """Test that a change to the sniffer changes the reader stored sniffer."""

    reader = Reader(metadata_header_data_file)
    reader.sniffer.start = 2

    assert reader._sniffer.start == 2


def test_sniffer_change_header(metadata_header_data_file):
    """Test that a change to the sniffer changes the header reference."""

    reader = Reader(metadata_header_data_file)
    x = reader.header
    reader.sniffer.amount = 40
    y = reader.header

    assert x is not y


def test_sniffer_change_tabulator(metadata_header_data_file):
    """Test that a change to the sniffer changes the tabulator."""

    reader = Reader(metadata_header_data_file)
    x = reader.tabulator
    reader.sniffer.amount = 40
    y = reader.tabulator

    assert x is not y


def test_sniffer_change_header_fixed(metadata_header_data_file):
    """Test that a change to the sniffer when the header is not measured from
    the file remains the same."""

    reader = Reader(metadata_header_data_file)
    reader.header = ['a'] * 7
    reader.sniffer.amount = 89

    assert reader.header.names == [f'a_{i}' for i in range(7)]


##########################
# Header property change #
##########################

def test_header_change_int(metadata_header_data_file):
    """Validate that selecting a header row with unexpected length raises
    a ValueError."""

    reader = Reader(metadata_header_data_file)
    with pytest.raises(ValueError):
        reader.header = 0


def test_header_change_list(metadata_header_data_file):
    """Validate that an incorrectly lengthed header list rasise a ValueError."""

    reader = Reader(metadata_header_data_file)
    with pytest.raises(ValueError):
        reader.header = ['a'] * 5


def test_header_change_dict(metadata_header_data_file):
    """Validate that providing kwargs to header creates a new sniffer header."""

    reader = Reader(metadata_header_data_file)
    x = reader.header
    reader.header = {'poll': 10}
    y = reader.header

    assert x is not y


def test_header_unexpected_type(metadata_header_data_file):
    """Validate that setting header to any type that is not int, seq or dict
    raises a ValueError."""

    reader = Reader(metadata_header_data_file)
    with pytest.raises(ValueError):
        reader.header = 3.4


##################
# ragged logging #
##################

def test_raggedness_0(metadata_header_data_file):
    """Validate that a dict with a None key logs an error."""


    reader = Reader(metadata_header_data_file)
    row = {'apples': 3, 'peaches': 4.2, 'kind': 'fruit', None: 'x'}
    reader._log_ragged(0, row, raise_error=False)

    assert bool(reader.errors.ragged)

def test_raggedness_1(metadata_header_data_file):
    """Validate that a row with a None value logs an error."""


    reader = Reader(metadata_header_data_file)
    row = {'apples': 3, 'peaches': 4.2, 'kind': 'fruit', 'x': None}
    reader._log_ragged(0, row, raise_error=False)

    assert bool(reader.errors.ragged)


###########
# Priming #
###########

def test_priming_autostart_0(metadata_header_data_file):
    """Test autostart when no header is present"""

    reader = Reader(metadata_header_data_file)
    _, start = reader._prime()
    assert start == reader.header.line + 1


def test_priming_autostart_1(metadata_data_file):
    """Test autostart when no header is present"""

    reader = Reader(metadata_data_file)
    _, start = reader._prime()
    assert start == reader.sniffer.metadata(None).lines[-1] + 1


def test_priming_autostart_1(data_file):
    """Test autostart when no header and no metadata is present"""

    reader = Reader(data_file)
    _, start = reader._prime()
    assert start == 0


def test_priming_start_0(metadata_header_data_file):
    """Test that starting at line in the data section gives the correct start
    row if a header is provided."""

    reader = Reader(metadata_header_data_file)
    start = reader.header.line + 1 + 10
    _, line = reader._prime(start)

    assert start == line


def test_priming_start_1(metadata_header_data_file, datastring):
    """Test that starting at line in the data section gives the correct data if
    a header is provided."""

    reader = Reader(metadata_header_data_file)
    start = reader.header.line + 1 + 10
    row_iter, _ = reader._prime(start)

    rowstrings = [','.join(row.values()) for row in row_iter]
    assert rowstrings == datastring.splitlines()[10:]


def test_priming_start_2(metadata_data_file, datastring):
    """Test that starting at line in the data section gives the correct data if
    no header is provided."""

    reader = Reader(metadata_data_file)
    start = reader.sniffer.metadata(None).lines[-1] + 1 + 10
    row_iter, _ = reader._prime(start)

    rowstrings = [','.join(row.values()) for row in row_iter]
    assert rowstrings == datastring.splitlines()[10:]


def test_priming_start_3(data_file, datastring):
    """Test that starting at line in the data section gives the correct data if
    no header and no metadata is provided."""

    reader = Reader(data_file)
    start = 10
    row_iter, _ = reader._prime(start)

    rowstrings = [','.join(row.values()) for row in row_iter]
    assert rowstrings == datastring.splitlines()[10:]


def test_priming_indices_start_0(metadata_header_data_file):
    """Test that start from indices is correct if a header is present."""

    reader = Reader(metadata_header_data_file)
    row_iter, start = reader._prime(indices=range(10, 20))

    assert start == 10

# TEST FAILING
def test_priming_indices_start_1(metadata_header_data_file, datastring):
    """Test that data from indices is correct if a header is present."""

    reader = Reader(metadata_header_data_file)
    row_iter, _ = reader._prime(indices=range(10, 20))

    rowstrings = [','.join(row.values()) for row in row_iter]
    print(rowstrings)
    print(datastring.splitlines()[10:20])
    assert rowstrings == datastring.splitlines()[10:20]


