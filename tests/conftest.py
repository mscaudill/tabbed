import pytest
import random
import string
import re
import datetime
import itertools

@pytest.fixture
def cell_types():
    return ["str", "int", "float", "complex", "date", "time", "datetime"]

# Fixture for returning a random number generator
@pytest.fixture
def rn_generator():
    """Returns a random number generator with the seed 1"""

    return random.Random(1)


# Numeric-related Fixtures
@pytest.fixture
def random_integers(rn_generator, request):
    """This returns a list of n random integers. n is passed in through indirect parameterization"""

    def make_random_integer():
        return str(rn_generator.randint(-100000, 100000))

    return [make_random_integer() for _ in range(request.param)]
    


@pytest.fixture
def random_floats(rn_generator, request):
    """This returns a list of n random floats. n is passed in through indirect parameterization"""

    def make_random_float():
        return str(rn_generator.uniform(-100000, 100000))

    return [make_random_float() for _ in range(request.param)]



@pytest.fixture
def random_complex_numbers(rn_generator, request):
    """This returns a list of n random complex numbers. n is passed in through indirect parameterization"""

        
    def make_random_complex_num(rn_generator):
        """Generates a random complex numbers and takes a random number generator as input"""

        real_part = rn_generator.uniform(-100000, 100000)
        imag_part = rn_generator.uniform(-100000, 100000)
        num = complex(real_part, imag_part)

        return str(num)

    return [make_random_complex_num() for _ in range(request.param)]



@pytest.fixture
def random_scientific_notation_floats(rn_generator, request):
    """Returns a list of n scientific notation floats. n is passed in through indirect parameterization"""

    def make_random_sci_not_float():
        significand = rn_generator.uniform(-10, 10)
        exponent = rn_generator.randint(-100, 100)
        if (rn_generator.random() > .5):
            return str(significand) + "E" + str(exponent)
        else:
            return str(significand) + "e" + str(exponent)

    return [make_random_sci_not_float() for _ in range(request.param)]



@pytest.fixture
def random_numerics(random_integers, random_floats, random_complex_numbers, random_scientific_notation_floats):
    """Returns a list of numerics. MUST specify the number of each of the counts of the fixtures it relies on via
    indirect parameterization before using this fixture"""

    mixed_numerics = []
    mixed_numerics.extend(random_integers)
    mixed_numerics.extend(random_floats)
    mixed_numerics.extend(random_complex_numbers)
    mixed_numerics.extend(random_scientific_notation_floats)
    random.shuffle(mixed_numerics)
    return mixed_numerics



@pytest.fixture
def random_non_numerics(rn_generator, request):
    """Returns a list of n non-numerics. n is specified is an indirect parameter"""

    def make_random_non_numeric():
        length = rn_generator.randint(1, 20)
        all_chars = string.digits + string.ascii_letters

        rand_str = "".join(rn_generator.choices(all_chars, k=length))

        non_numeric_insert_pos = rn_generator.randint(0, length+1)

        non_numeric_ascii = re.sub(r"[jJeE]", "", string.ascii_letters)
        non_numeric_char = rn_generator.choice(non_numeric_ascii)

        # Inserting a non-numeric character always ensures the whole string is non-numeric
        rand_non_numeric = rand_str[:non_numeric_insert_pos] + non_numeric_char + rand_str[non_numeric_insert_pos:]

        return rand_non_numeric

    return [make_random_non_numeric() for _ in range(request.param)]


@pytest.fixture
def random_strings(rn_generator, request):
    """Returns a list of n random strings. n is specified as an indirect parameter"""

    def make_random_string():
        all_chars = string.ascii_letters + string.digits
        random_length = rn_generator.rand_int(1, 30)
        rand_str = "".join(rn_generator.choices(all_chars, k=random_length))

        return rand_str

    return [make_random_string() for _ in range(request.param)]

@pytest.fixture
def date_formats():
    """Creates commonly used date format specifiers to be used for strftime"""

    months, separators, years = 'mbB', ' /-.', 'Yy'
    fmts = []
    for mth, sep, yr in itertools.product(months, separators, years):
        # build month and day first fmts
        x = [f'%{mth}{sep}%d{sep}%{yr}', f'%d{sep}%{mth}{sep}%{yr}']
        fmts.extend(x)

    return fmts

@pytest.fixture
def random_dates(rn_generator, date_formats, request):
    """Returns a list of n random dates. n is specified by an indirect parameter"""

    def make_random_date():
        start_year = rn_generator.randint(1990, 2025)
        end_year = rn_generator(start_year, 2025)

        start_date = datetime.datetime(start_year, 1, 1)
        end_date = datetime.datetime(end_year, 12, 31)
        time_difference = end_date - start_date
        intermediate_num_days = rn_generator.randint(time_difference.days)
        date = start_date + datetime.timedelta(days=intermediate_num_days)

        date_format = rn_generator.choice(date_formats)

        return date.strftime(date_format)
    
    return [make_random_date() for _ in range(request.param)]

@pytest.fixture
def time_formats():
    """Creates commonly used time format specifiers to be used for strftime
    """

    fmts = []
    hours, microsecs = ['I', 'H'], ['', ':%f', '.%f']
    # Issue: now time formats is generating invalid format where you can have military
    # time but also have a diurnal. Also allowing 12 hour format to be given without a diurnal
    # which is problematic.
    # Proposed Change:
    for hrs, micro in itertools.product(hours, microsecs):
        if hrs == "I":
            diurnal = " %p"
        else:
            diurnal = ''
        fmts.append(f'%{hrs}:%M:%S{micro}{diurnal}')

    return fmts

@pytest.fixture
def random_times(rn_generator, time_formats, request):
    """Generates a random time in a random format"""

    def make_random_time():
        minute = rn_generator.randint(0, 59)
        second = rn_generator.randint(0, 59)
        microsecond = rn_generator.randint(0, 999999)
        hour = rn_generator.randint(1, 23)

        time = datetime.time(hour=hour, minute=minute, second=second, microsecond=microsecond)
        time_format = rn_generator.choice(time_formats)

        return time.strftime(time_format)
    
    return [make_random_time() for _ in range(request.param)]
