import tempfile
import string
import datetime
import pytest
import random

from tabbed.sniffing import Sniffer

@pytest.fixture
def num_data_rows(request):
    return request.param

@pytest.fixture
def num_str_columns(request):
    return request.param

@pytest.fixture
def num_int_columns(request):
    return request.param

@pytest.fixture
def num_float_columns(request):
    return request.param

@pytest.fixture
def num_sci_not_columns(request):
    return request.param

@pytest.fixture
def num_complex_columns(request):
    return request.param

@pytest.fixture
def num_date_columns(request):
    return request.param

@pytest.fixture
def num_time_columns(request):
    return request.param

@pytest.fixture
def num_datetime_columns(request):
    return request.param

@pytest.fixture(params=",;|\t")
def delimeter(request):
    return request.param

@pytest.fixture
def num_metadata_newlines(request):
    return request.param

@pytest.fixture
def num_metadata_delimeters(request):
    return request.param

@pytest.fixture
def random_str_table(rn_generator, num_data_rows, num_str_columns):
    """Returns a table of strings that is num_columns by num_data_rows where the number of columns is 
    specified through indirect parameterization"""

    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.randint(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str
    
    return [[make_random_string() for _ in range(num_data_rows)] for _ in range(num_str_columns)]

@pytest.fixture
def random_int_table(rn_generator, num_data_rows, num_int_columns):
    """Returns a table of ints that is num_columns by num_data_rows where the number of columns is 
    specified through indirect parameterization"""

    def make_random_integer():
        return str(rn_generator.randint(-100000, 100000))
    
    return [[make_random_integer() for _ in range(num_data_rows)] for _ in range(num_int_columns)]

@pytest.fixture
def random_float_table(rn_generator, num_data_rows, num_float_columns):
    """Returns a table of floats that is num_columns by num_data_rows where the number of columns is 
    specified through indirect parameterization"""

    def make_random_float():
        return str(rn_generator.uniform(-100000, 100000))
    
    return [[make_random_float() for _ in range(num_data_rows)] for _ in range(num_float_columns)]

@pytest.fixture
def random_complex_table(rn_generator, num_data_rows, num_complex_columns):
    """Returns a table of complex numbers that is num_columns by num_data_rows where the number of columns is 
    specified through indirect parameterization"""

    def make_random_complex_num():
        real_part = rn_generator.uniform(-100000, 100000)
        imag_part = rn_generator.uniform(-100000, 100000)
        num = complex(real_part, imag_part)

        return str(num)
    
    return [[make_random_complex_num() for _ in range(num_data_rows)] for _ in range(num_complex_columns)]

@pytest.fixture
def random_scientific_notation_table(rn_generator, num_data_rows, num_sci_not_columns):
    """Returns a table of scientific notation floats that is num_columns by num_data_rows where the number of columns is 
    specified through indirect parameterization"""

    def make_random_sci_not_float():
        significand = rn_generator.uniform(-10, 10)
        exponent = rn_generator.randint(-100, 100)
        if (rn_generator.random() > .5):
            return str(significand) + "E" + str(exponent)
        else:
            return str(significand) + "e" + str(exponent)
        
    return [[make_random_sci_not_float() for _ in range(num_data_rows)] for _ in range(num_sci_not_columns)]

@pytest.fixture
def random_date_table(rn_generator, date_formats, num_data_rows, num_date_columns):
    """Returns a table of dates that is num_columns by num_data_rows where the number of columns is specified
    through indirect parameterization"""

    def make_random_date():
        start_year = rn_generator.randint(1990, 2025)
        end_year = rn_generator.randint(start_year, 2025)

        start_date = datetime.datetime(start_year, 1, 1)
        end_date = datetime.datetime(end_year, 12, 31)
        time_difference = end_date - start_date
        intermediate_num_days = rn_generator.randint(0, time_difference.days)
        date = start_date + datetime.timedelta(days=intermediate_num_days)

        date_format = rn_generator.choice(date_formats)

        return date.strftime(date_format)

    return [[make_random_date() for _ in range(num_data_rows)] for _ in range(num_date_columns)]

@pytest.fixture
def random_time_table(rn_generator, time_formats, num_data_rows, num_time_columns):
    """Returns a table of times that is num_columns by num_data_rows where the number of columns is specified
    through indirect parameterization"""

    def make_random_time():
        minute = rn_generator.randint(0, 59)
        second = rn_generator.randint(0, 59)
        microsecond = rn_generator.randint(0, 999999)
        hour = rn_generator.randint(1, 23)

        time = datetime.time(hour=hour, minute=minute, second=second, microsecond=microsecond)
        time_format = rn_generator.choice(time_formats)

        return time.strftime(time_format)

    return [[make_random_time() for _ in range(num_data_rows)] for _ in range(num_time_columns)]

@pytest.fixture
def random_datetime_table(rn_generator, time_formats, date_formats, num_data_rows, num_datetime_columns):
    """Returns a table of datetimes that is num_columns by num_data_rows where the number of columns is specified
    through indirect parameterization"""

    def make_random_time():
        minute = rn_generator.randint(0, 59)
        second = rn_generator.randint(0, 59)
        microsecond = rn_generator.randint(0, 999999)
        hour = rn_generator.randint(1, 23)

        time = datetime.time(hour=hour, minute=minute, second=second, microsecond=microsecond)
        time_format = rn_generator.choice(time_formats)

        return time.strftime(time_format)
    
    def make_random_date():
        start_year = rn_generator.randint(1990, 2025)
        end_year = rn_generator.randint(start_year, 2025)

        start_date = datetime.datetime(start_year, 1, 1)
        end_date = datetime.datetime(end_year, 12, 31)
        time_difference = end_date - start_date
        intermediate_num_days = rn_generator.randint(0, time_difference.days)
        date = start_date + datetime.timedelta(days=intermediate_num_days)

        date_format = rn_generator.choice(date_formats)

        return date.strftime(date_format)
    
    return [[f"{make_random_date()} {make_random_time()}" for _ in range(num_data_rows)] for _ in range(num_datetime_columns)]

@pytest.fixture
def sample_rows(random_str_table, random_int_table, random_float_table, random_scientific_notation_table,
                         random_date_table, random_time_table, random_datetime_table, random_complex_table):
    """Returns a table where column types are randomly mixed between all 8 types. When using this fixture
    must use indirect parameterization to specify the number of columns of each type."""

    mixture_table = []
    mixture_table.extend(random_str_table)
    mixture_table.extend(random_int_table)
    mixture_table.extend(random_float_table)
    mixture_table.extend(random_scientific_notation_table)
    mixture_table.extend(random_date_table)
    mixture_table.extend(random_time_table)
    mixture_table.extend(random_datetime_table)
    mixture_table.extend(random_complex_table)
    random.shuffle(mixture_table)

    return list(zip(*mixture_table))

@pytest.fixture
def sample_header(rn_generator, num_str_columns, num_complex_columns, num_date_columns, num_datetime_columns, num_float_columns, num_int_columns, num_sci_not_columns, num_time_columns):
    """Creates a header with random strings, and whose length is the sum of all the column lengths"""

    total_num_columns = num_str_columns + num_complex_columns + num_date_columns + num_datetime_columns + num_float_columns + num_int_columns + num_sci_not_columns + num_time_columns
    
    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.randint(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str

    return [make_random_string() for _ in range(total_num_columns)]



@pytest.fixture
def sample_metadata(rn_generator, delimeter, num_metadata_newlines, num_metadata_delimeters):
    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.randint(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str

    delimeters_and_newlines_list = ["\n"] * num_metadata_newlines + [delimeter] * num_metadata_delimeters
    random.shuffle(delimeters_and_newlines_list)

    metadata_str = ""

    for entry in delimeters_and_newlines_list:
        metadata_str += make_random_string() + entry

    metadata_str += make_random_string()

    return metadata_str


@pytest.fixture
def sample_file(sample_metadata, sample_header, sample_rows, delimeter):
    """Sets up and tears down a sample delimited text file."""

    # TODO Notice we should vary separators too
    stringed_header = delimeter.join(sample_header)
    stringed_data = '\n'.join([delimeter.join(row) for row in sample_rows])
    string = '\n'.join([sample_metadata, stringed_header, stringed_data])

    # for idx, row in enumerate(string.splitlines()):
    #     print(idx, row)

    outfile = tempfile.TemporaryFile(mode='w+')
    _ = outfile.write(string)
    yield outfile

    print('Closing file resource')
    outfile.close()

@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(100, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10)]
)
def test_line_count(sample_file, num_data_rows, num_metadata_newlines):
    """ """

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.line_count == num_total_newlines + 1


