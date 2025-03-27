# FIXME Add a module string explaining that you will construct tables of
# different types

import tempfile
import string
import datetime
import pytest
import random

from tabbed.sniffing import Sniffer


@pytest.fixture
def rng():
    """Returns a Random instance with seed 1."""

    return Random(1)


@pytest.fixture(params=",;|\t")
def delimiter(request):
    """Returns tabbed compatible delimiters."""

    return request.param


@pytest.fixture
def valid_chars():
    """Returns a string of all valid characters.

    Invalid characters are a delimiters.
    """

    str_set = set(string.ascii_letters + string.digits + string.punctuation)
    str_set.difference_update(set((',', ';', '|', '\t')))

    return ''.join(str_set)


@pytest.fixture
def shuffle(rng):
    """A fixture that returns a function for shuffling a list."""

    def shuffler(ls):
        """Returns a shuffled copy of a list.

        Args:
            ls:
                A list containing Any type to be shuffled.

        Returns:
            A copy of the list shuffled.
        """

        return rng.sample(ls, len(ls))

   return shuffler


@pytest.fixture
def string_table(rng, valid_chars):
    """A fixture that returns a function for building a random but reproducible
    tables of valid string characters."""

    def make_table(rows, cols):
        """Returns a rows x cols table of strings of random lengths."""

        cnt = rows * cols
        lengths = [rng.randint(1, len(valid_chars)) for _ in range(cnt)]
        cells = [''.join(rng.choices(valid_chars, k=l)) for l in lengths]

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def integer_table(rng):
    """A fixture that returns a function for building a random but reproducible
    tables of stringed integer values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of integers between -1000 and 1000."""

        cnt = rows * cols
        cells = [str(rng.randint(-1000, 1000)) for _ in range(cnt)]

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def float_table(rng):
    """A fixture that returns a function for building a random but reproducible
    tables of stringed float values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [str(rng.uniform(-1000, 1000)) for _ in range(cnt)]

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def complex_table(rng):
    """A fixture that returns a function for building a random but reproducible
    tables of stringed complex values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of stringed complex values with real and
        imag parts in [-1000, 1000]."""

        # * 2 for real and complex parts
        cnt = rows * cols * 2
        parts = [rng.uniform(-1000, 1000) for _ in range(cnt)]
        cells = [str(complex(tup)) for tup in batched(parts, 2)]

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def enotation_table(rng):
    """A fixture that returns a function for building random but reproducible
    tables of stringed scientific notation float values."""

    def make_table(rows, cols):
        """Returns a rows x cols table of E notation floats in [-1000, 1000]."""

        cnt = rows * cols
        cells = [f'{rng.uniform(-1000, 1000):.2E}') for _ in range(cnt)]

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def time_table(rng, time_formats):
    """A fixture that returns a function for building random but reproducible
    tables of stringed times."""

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

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def date_table(rng, date_formats):
    """A fixture that returns a function for building random but reproducible
    tables of stringed dates."""

    def make_table(rows, cols):
        """Returns a rows x cols table of dates."""

        cnt = rows * col
        years = [rng.randint(1800, 2500) for _ in range(cnt)]
        months = [rng.randint(1, 12) for _ in range(cnt)]
        days = [rng.randint(1, 30) for _ in range(cnt)]
        dates = [datetime.date(y, m, d) for y, m, d in zip(years, months, days)]
        fmts = [rng.choice(date_formats) for _ in range(cnt)]
        cells = [date.strftime(fmt) for date, fmt in zip(dates, fmts)]

        return  list(batched(cells, cols))

    return make_table


@pytest.fixture
def datetime_table(rng, time_table, date_table):
    """A fixture that returns a function for building random but reproducible
    tables of stringed datetime instances."""

    def make_table(rows, cols):
        """Returns a rows x cols table of datetime strings."""

        timed_table = time_table(rows, cols)
        dated_table = date_table(rows, cols)

        cells = []
        for date_row, time_row in zip(dated_table, timed_table):
            cells.append([' '.join(d, t) for d, t in zip(date_row, time_row)])

        return list(batched(cells, cols))

    return make_table


@pytest.fixture
def table(
        rng,
        string_table,
        integer_table,
        float_table,
        enotation_table,
        time_table,
        date_table,
        datetime_table,
):
    """ """
    
    # here we may want to now start parameterization for rows and cols of each
    # table type, this could be direct or indirect

    pass












@pytest.fixture
def num_rows(request):
    """An integer number of rows for the data section of plain text file."""

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
def delimiter(request):
    return request.param

# TODO rename line_count
@pytest.fixture
def line_count(request):
    return request.param


# TODO why do we need this -- can we just us all delimiters
# also note spelling delimiter
@pytest.fixture
def num_metadata_delimeters(request):
    return request.param


# TODO rename num_columns
@pytest.fixture
def total_num_columns(
    num_str_columns,
    num_int_columns,
    num_float_columns,
    num_date_columns,
    num_datetime_columns,
    num_time_columns,
    num_sci_not_columns,
    num_complex_columns,
):
    """Returns the total number of columns in the table"""

    # FIXME use locals
    return sum(locals().values())

    return (
        num_str_columns
        + num_complex_columns
        + num_date_columns
        + num_datetime_columns
        + num_float_columns
        + num_int_columns
        + num_sci_not_columns
        + num_time_columns
    )



# Probably better to just use a simple function here for clarity
# def shuffle(rn_generator, ls):
#   """Shuffles elements of list using a random number generator.
#
#   Note:
#       Unlike Python's builtin in-place shuffle, this function returns a copy.
#   """
#
#   return rn_generator.sample(ls, len(ls))
@pytest.fixture
def random_column_positions(rn_generator, total_num_columns):
    """Returns a list of random column positions that will be used to shuffle the columns when the final table is made."""

    shuffled_positions = list(range(total_num_columns))

    rn_generator.shuffle(shuffled_positions)

    return shuffled_positions


# TODO rename to string_table
# we should consider just direct parameterization here and removing the
# num_str_columns fixture
#
# @pytest.fixture(params=[5])
# def string_table(rn_generator, num_rows):
#   """Returns a 5 by num_rows table of string values as a list of list."""
#
#   rows = [random_strings(rn_generator, request.param) for _ in range(num_rows)]
#
#
@pytest.fixture
def random_list_of_str_lists(rn_generator, num_data_rows, num_str_columns):
    """Returns a list of lists of strings with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_str_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""


    # TODO use the random_strings from the conftest module
    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.randint(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str

    return [
        [make_random_string() for _ in range(num_data_rows)]
        for _ in range(num_str_columns)
    ]


# TODO rename to integer_table
@pytest.fixture
def random_list_of_int_lists(rn_generator, num_data_rows, num_int_columns):
    """Returns a list of lists of ints with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_int_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

    def make_random_integer():
        return str(rn_generator.randint(-10000, 10000))

    return [
        [make_random_integer() for _ in range(num_data_rows)]
        for _ in range(num_int_columns)
    ]


# TODO rename to float_table
@pytest.fixture
def random_list_of_float_lists(rn_generator, num_data_rows, num_float_columns):
    """Returns a list of lists of floats with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_float_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

    def make_random_float():
        return str(rn_generator.uniform(-10000, 10000))

    return [
        [make_random_float() for _ in range(num_data_rows)]
        for _ in range(num_float_columns)
    ]


# TODO rename to complex_table
@pytest.fixture
def random_list_of_complex_lists(
    rn_generator, num_data_rows, num_complex_columns
):
    """Returns a list of lists of complex numbers with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_complex_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

    def make_random_complex_num():
        real_part = rn_generator.uniform(-10000, 10000)
        imag_part = rn_generator.uniform(-10000, 10000)
        num = complex(real_part, imag_part)

        return str(num)

    return [
        [make_random_complex_num() for _ in range(num_data_rows)]
        for _ in range(num_complex_columns)
    ]


# TODO rename to scinotation_table
@pytest.fixture
def random_list_of_scientific_notation_lists(
    rn_generator, num_data_rows, num_sci_not_columns
):
    """Returns a list of lists of scientific notation floats with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_sci_not_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

    def make_random_sci_not_float():
        significand = rn_generator.uniform(-10, 10)
        exponent = rn_generator.randint(-10, 10)
        if rn_generator.random() > 0.5:
            return str(significand) + "E" + str(exponent)
        else:
            return str(significand) + "e" + str(exponent)

    return [
        [make_random_sci_not_float() for _ in range(num_data_rows)]
        for _ in range(num_sci_not_columns)
    ]


# TODO rename to date_table
@pytest.fixture
def random_list_of_date_lists(
    rn_generator, date_formats, num_data_rows, num_date_columns
):
    """Returns a list of lists of dates with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_date_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

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

    return [
        [make_random_date() for _ in range(num_data_rows)]
        for _ in range(num_date_columns)
    ]


# TODO rename to time_table
@pytest.fixture
def random_list_of_time_lists(
    rn_generator, time_formats, num_data_rows, num_time_columns
):
    """Returns a list of lists of times with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_time_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

    def make_random_time():
        minute = rn_generator.randint(0, 59)
        second = rn_generator.randint(0, 59)
        microsecond = rn_generator.randint(0, 999999)
        hour = rn_generator.randint(1, 23)

        time = datetime.time(
            hour=hour, minute=minute, second=second, microsecond=microsecond
        )
        time_format = rn_generator.choice(time_formats)

        return time.strftime(time_format)

    return [
        [make_random_time() for _ in range(num_data_rows)]
        for _ in range(num_time_columns)
    ]


# TODO rename to datetime_table
@pytest.fixture
def random_list_of_datetime_lists(
    rn_generator,
    time_formats,
    date_formats,
    num_data_rows,
    num_datetime_columns,
):
    """Returns a list of lists of datetimes with each row corresponding to a column in future table to be generated.
    Number rows is specified by num_datetime_columns and number of items in each row specified by num_data_rows both
    by indirect parameterization."""

    def make_random_time():
        minute = rn_generator.randint(0, 59)
        second = rn_generator.randint(0, 59)
        microsecond = rn_generator.randint(0, 999999)
        hour = rn_generator.randint(1, 23)

        time = datetime.time(
            hour=hour, minute=minute, second=second, microsecond=microsecond
        )
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

    return [
        [
            f"{make_random_date()} {make_random_time()}"
            for _ in range(num_data_rows)
        ]
        for _ in range(num_datetime_columns)
    ]


@pytest.fixture
def column_types(
    num_str_columns,
    num_int_columns,
    num_float_columns,
    num_date_columns,
    num_datetime_columns,
    num_time_columns,
    num_sci_not_columns,
    num_complex_columns,
    random_column_positions,
):
    types_list = (
        [str] * num_str_columns
        + [int] * num_int_columns
        + [float] * num_float_columns
        + [float] * num_sci_not_columns
        + [datetime.datetime] * num_date_columns
        + [datetime.datetime] * num_time_columns
        + [datetime.datetime] * num_datetime_columns
        + [complex] * num_complex_columns
    )

    # TODO replace above with locals(), note random_column_indices disappear
    args = locals()
    dtime = datetime.datetime
    types = (str, int, float, float, dtime, dtime, dtime, complex)
    ordered = [amount * [typ] for amount, typ in zip(args.values(), types)]

    # TODO just shuffle ordered and return
    shuffled_types = [
        types_list[position] for position in random_column_positions
    ]

    return shuffled_types

# TODO rename table
@pytest.fixture
def sample_rows(
    random_list_of_str_lists,
    random_list_of_int_lists,
    random_list_of_float_lists,
    random_list_of_scientific_notation_lists,
    random_list_of_date_lists,
    random_list_of_time_lists,
    random_list_of_datetime_lists,
    random_list_of_complex_lists,
    total_num_columns,
    random_column_positions,
):
    """Returns a table where column types are randomly mixed between all 8 types. When using this fixture
    must use indirect parameterization to specify the number of columns of each type.
    """

    # TODO use locals to simplify the many extends below
    mixed_table = sum(locals().values(), start=[])

    #  total_num_columns won't be needed if shuffling above is implemented
    #  random_column_positions won't be needed if shuffling above is implemented

    mixture_table = []
    mixture_table.extend(random_list_of_str_lists)
    mixture_table.extend(random_list_of_int_lists)
    mixture_table.extend(random_list_of_float_lists)
    mixture_table.extend(random_list_of_scientific_notation_lists)
    mixture_table.extend(random_list_of_date_lists)
    mixture_table.extend(random_list_of_time_lists)
    mixture_table.extend(random_list_of_datetime_lists)
    mixture_table.extend(random_list_of_complex_lists)

    shuffled_mixture_table = [
        mixture_table[position] for position in random_column_positions
    ]

    return [list(row) for row in zip(*shuffled_mixture_table)]


# TODO I think we will need multiple headers
# 1. A properly formatted header like this one
# 2. A header with spaces in the names
# 3. A header with a mixture of string and integer values (should fail?)
# 4. A header with no properly formatted values... like all datetimes
# 5. others?
# Then test the header method against all these
@pytest.fixture
def sample_header(rn_generator, total_num_columns):
    """Creates a header with random strings, and whose length is the sum of all the column lengths"""

    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.randint(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str

    return [make_random_string() for _ in range(total_num_columns)]


@pytest.fixture
def sample_metadata(
    rn_generator, delimeter, num_metadata_newlines, num_metadata_delimeters
):
    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.randint(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str

    delimeters_and_newlines_list = ["\n"] * num_metadata_newlines + [
        delimeter
    ] * num_metadata_delimeters
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
    [(10, 10, 0, 0, 0, 0, 0, 0, 0, 10, 10)],
)
def test_line_count_strings(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the line count measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.line_count == num_total_newlines + 1


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 0, 0, 0, 0, 0, 0, 0, 10, 10)],
)
def test_start_strings(sample_file):
    """Test for making sure the start line measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    assert sniffer.start == 0


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 100, 0, 0, 0, 0, 0, 0, 0, 10, 10)],
)
def test_header_strings(sample_file, sample_header):
    sniffer = Sniffer(sample_file)

    assert sniffer.header().names == sample_header


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 0, 0, 0, 0, 0, 0, 0, 10, 10)],
)
def test_delimeter_strings(sample_file, delimeter):
    sniffer = Sniffer(sample_file)

    assert sniffer.dialect.delimiter == delimeter


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 0, 0, 0, 0, 0, 0, 0, 10, 10)],
)
def test_amount_strings(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the amount of lines measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.amount == min(100, num_total_newlines + 1)


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 0, 0, 0, 0, 0, 0, 0, 10, 10)],
)
def test_rows_strings(
    sample_file, sample_rows, sample_metadata, sample_header, delimeter
):
    sniffer = Sniffer(sample_file)

    all_rows = []
    metadata_as_rows = [
        single_line.split(delimeter)
        for single_line in sample_metadata.split("\n")
    ]
    all_rows.extend(metadata_as_rows)
    all_rows.append(sample_header)
    all_rows.extend(sample_rows)

    for row_idx in range(len(sniffer.rows())):

        sniffer_row = sniffer.rows()[row_idx]
        sample_row = all_rows[row_idx]

        assert sniffer_row == sample_row


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 10, 0, 0, 10, 0, 10, 10, 10, 10)],
)
def test_line_count_numerics(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the line count measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.line_count == num_total_newlines + 1


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 10, 0, 0, 10, 0, 10, 10, 10, 10)],
)
def test_start_numerics(sample_file):
    """Test for making sure the start line measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    assert sniffer.start == 0


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 100, 0, 0, 100, 0, 100, 100, 10, 10)],
)
def test_header_numerics(sample_file, sample_header):
    sniffer = Sniffer(sample_file)

    for expected, actual in zip(sample_header, sniffer.header().names):
        assert expected in actual, f"'{expected}' not in '{actual}'"


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 10, 0, 0, 10, 0, 10, 10, 10, 10)],
)
def test_delimeter_numerics(sample_file, delimeter):
    sniffer = Sniffer(sample_file)

    assert sniffer.dialect.delimiter == delimeter


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 10, 0, 0, 10, 0, 10, 10, 10, 10)],
)
def test_amount_numerics(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the amount of lines measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.amount == min(100, num_total_newlines + 1)


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 10, 0, 0, 10, 0, 10, 10, 10, 10)],
)
def test_rows_numerics(
    sample_file, sample_rows, sample_metadata, sample_header, delimeter
):
    sniffer = Sniffer(sample_file)

    all_rows = []
    metadata_as_rows = [
        single_line.split(delimeter)
        for single_line in sample_metadata.split("\n")
    ]
    all_rows.extend(metadata_as_rows)
    all_rows.append(sample_header)
    all_rows.extend(sample_rows)

    for row_idx in range(len(sniffer.rows())):

        sniffer_row = sniffer.rows()[row_idx]
        sample_row = all_rows[row_idx]

        assert sniffer_row == sample_row


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 0, 10, 10, 0, 10, 0, 0, 10, 10)],
)
def test_line_count_datetimes(
    sample_file, num_data_rows, num_metadata_newlines
):
    """Test for making sure the line count measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.line_count == num_total_newlines + 1


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 0, 10, 10, 0, 10, 0, 0, 10, 10)],
)
def test_start_datetimes(sample_file):
    """Test for making sure the start line measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    assert sniffer.start == 0


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 0, 10, 10, 0, 10, 0, 0, 10, 10)],
)
def test_header_datetimes(sample_file, sample_header):
    sniffer = Sniffer(sample_file)

    assert sniffer.header().names == sample_header


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 0, 10, 10, 0, 10, 0, 0, 10, 10)],
)
def test_delimeter_datetimes(sample_file, delimeter):
    sniffer = Sniffer(sample_file)

    assert sniffer.dialect.delimiter == delimeter


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 0, 10, 10, 0, 10, 0, 0, 10, 10)],
)
def test_amount_datetimes(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the amount of lines measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.amount == min(100, num_total_newlines + 1)


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 0, 0, 10, 10, 0, 10, 0, 0, 10, 10)],
)
def test_rows_datetimes(
    sample_file, sample_rows, sample_metadata, sample_header, delimeter
):
    sniffer = Sniffer(sample_file)

    all_rows = []
    metadata_as_rows = [
        single_line.split(delimeter)
        for single_line in sample_metadata.split("\n")
    ]
    all_rows.extend(metadata_as_rows)
    all_rows.append(sample_header)
    all_rows.extend(sample_rows)

    for row_idx in range(len(sniffer.rows())):

        sniffer_row = sniffer.rows()[row_idx]
        sample_row = all_rows[row_idx]

        assert sniffer_row == sample_row


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10)],
)
def test_line_count_mixture(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the line count measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.line_count == num_total_newlines + 1


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10)],
)
def test_start_mixture(sample_file):
    """Test for making sure the start line measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    assert sniffer.start == 0


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10)],
)
def test_amount_mixture(sample_file, num_data_rows, num_metadata_newlines):
    """Test for making sure the amount of lines measured by the sniffer is accurate"""

    sniffer = Sniffer(sample_file)
    num_total_newlines = num_metadata_newlines + (num_data_rows - 1) + 2
    assert sniffer.amount == min(100, num_total_newlines + 1)


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10)],
)
def test_header_mixture(sample_file, sample_header):
    sniffer = Sniffer(sample_file)

    for expected, actual in zip(sample_header, sniffer.header().names):
        assert expected in actual, f"'{expected}' not in '{actual}'"


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10)],
)
def test_delimeter_mixture(sample_file, delimeter):
    sniffer = Sniffer(sample_file)

    assert sniffer.dialect.delimiter == delimeter


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 100, 100, 100, 100, 100, 100, 100, 100, 10, 10)],
)
def test_types_mixture(sample_file, sample_types):
    sniffer = Sniffer(sample_file)

    assert sniffer.types() == sample_types


@pytest.mark.parametrize(
    "num_data_rows, num_str_columns, num_int_columns, num_date_columns, num_time_columns, num_sci_not_columns, num_datetime_columns, num_complex_columns, num_float_columns, num_metadata_newlines, num_metadata_delimeters",
    [(10, 30, 30, 30, 30, 30, 30, 30, 30, 30, 10)],
)
def test_rows_mixture(
    sample_file, sample_rows, sample_metadata, sample_header, delimeter
):
    sniffer = Sniffer(sample_file)

    all_rows = []
    metadata_as_rows = [
        single_line.split(delimeter)
        for single_line in sample_metadata.split("\n")
    ]
    all_rows.extend(metadata_as_rows)
    all_rows.append(sample_header)
    all_rows.extend(sample_rows)

    for row_idx in range(len(sniffer.rows())):

        sniffer_row = sniffer.rows()[row_idx]
        sample_row = all_rows[row_idx]

        assert sniffer_row == sample_row
