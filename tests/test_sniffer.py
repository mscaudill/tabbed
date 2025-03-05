import random
import tempfile

import pytest

from tabbed.sniffing import Sniffer
import shared_helper


def create_column_types(rn_generator, size):
    return rn_generator.choices(shared_helper.cell_types(), k=size)

def create_random_column(rn_generator, size, type):
    if (type == "str"):
        return [shared_helper.make_random_string(rn_generator) for _ in range(size)]
    elif (type == "int"):
        return [shared_helper.make_random_integer(rn_generator) for _ in range(size)]
    elif (type == "float"):
        return [shared_helper.make_random_float(rn_generator) for _ in range(size)]
    elif (type == "complex"):
        return [shared_helper.make_random_complex_num(rn_generator) for _ in range(size)]
    elif (type == "date"):
        return [shared_helper.make_random_date(rn_generator) for _ in range(size)]
    elif (type == "time"):
        return [shared_helper.make_random_time(rn_generator) for _ in range(size)]
    elif (type == "datetime"):
        return [shared_helper.make_random_datetime(rn_generator) for _ in range(size)]
    

# Indirect parameters to multiple fixtures
@pytest.fixture
def num_columns(request):
    return request.param

@pytest.fixture
def num_rows(request):
    return request.param

@pytest.fixture
def delimeter(request):
    return request.param

@pytest.fixture
def sample_rows(rn_generator, num_rows, num_columns):
    column_types = create_column_types(rn_generator, num_columns)

    columns = [create_random_column(rn_generator, num_rows, col_type) for col_type in column_types]
    rows = [list(column) for column in zip(*columns)]
    return rows

@pytest.fixture
def sample_header(rn_generator, num_columns):
    return [shared_helper.make_random_string(rn_generator, rn_generator.randint(1, 30)) for _ in range(num_columns)]

@pytest.fixture
def delimeters():
    return ",;|\t"

@pytest.fixture
def sample_metadata(rn_generator, delimeter):
    delimeter_and_newline_positions = sorted(rn_generator.choices(range(200, 1000), rn_generator.randint(0, 40)))

    metadata = shared_helper.make_random_string(rn_generator, delimeter_and_newline_positions[0])

    for i in range(1, len(delimeter_and_newline_positions)):
        pos = delimeter_and_newline_positions[i]

        if (rn_generator.random() < .5):
            metadata += "\n"
        else:
            metadata += delimeter
            
        num_chars = pos - delimeter_and_newline_positions[i-1]

        metadata += shared_helper.make_random_string(rn_generator, num_chars)

    return metadata


@pytest.fixture
def sample_file(sample_metadata, sample_header, sample_rows, delimeter):
    """Sets up and tears down a sample delimited text file."""

    # TODO Notice we should vary separators too
    stringed_header = delimeter.join(sample_header)
    stringed_data = '\n'.join([delimeter.join(row) for row in sample_rows])
    string = '\n'.join([sample_metadata, stringed_header, stringed_data])

    for idx, row in enumerate(string.splitlines()):
        print(idx, row)

    outfile = tempfile.TemporaryFile(mode='w+')
    _ = outfile.write(string)
    yield outfile

    print('Closing file resource')
    outfile.close()

def test_line_count(sample_file):
    """ """

    sniffer = Sniffer(sample_file)
    assert sniffer.line_count == 204


