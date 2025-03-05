import string
import re
import datetime
import itertools

def cell_types():
    return ["str", "int", "float", "complex", "date", "time", "datetime"]

def make_random_string(rn_generator, length):
    """Generates a random string that can contain either numbers or letters."""

    all_chars = string.ascii_letters + string.digits
    rand_str = "".join(rn_generator.choices(all_chars, k=length))

    return rand_str

def make_random_non_numeric(rn_generator):
    """Generates a random non-numeric value which can contain both letters and numbers, 
    but will contain at least one letter. Takes a random number generator as input."""

    length = rn_generator.randint(1, 20)
    all_chars = string.digits + string.ascii_letters

    rand_str = "".join(rn_generator.choices(all_chars, k=length))

    non_numeric_insert_pos = rn_generator.randint(0, length+1)

    non_numeric_ascii = re.sub(r"[jJeE]", "", string.ascii_letters)
    non_numeric_char = rn_generator.choice(non_numeric_ascii)

    # Inserting a non-numeric character always ensures the whole string is non-numeric
    rand_non_numeric = rand_str[:non_numeric_insert_pos] + non_numeric_char + rand_str[non_numeric_insert_pos:]

    return rand_non_numeric

def make_random_numeric(rn_generator):
    """Generates a random numeric value and takes a random number generator as input"""

    rand_num = rn_generator.random()
    if (rand_num < 1.0/4):
        return make_random_integer(rn_generator)
    elif (rand_num < 2.0/4):
        return make_random_float(rn_generator)
    elif (rand_num < 3.0/4):
        return make_random_complex_num(rn_generator)
    else:
        return make_random_sci_not_float(rn_generator)
    
def make_random_sci_not_float(rn_generator):
    """Generates a random scientific notation float and takes a random number generator as input"""

    significand = rn_generator.uniform(-10, 10)
    exponent = rn_generator.randint(-100, 100)
    if (rn_generator.random() > .5):
        return str(significand) + "E" + str(exponent)
    else:
        return str(significand) + "e" + str(exponent)
    
def make_random_complex_num(rn_generator):
    """Generates a random complex numbers and takes a random number generator as input"""

    real_part = rn_generator.uniform(-100000, 100000)
    imag_part = rn_generator.uniform(-100000, 100000)
    num = complex(real_part, imag_part)

    return str(num)


def make_random_integer(rn_generator):
    """Generates a random integer and takes a random number generator as input"""
    
    return str(rn_generator.randint(-100000, 100000))

def make_random_float(rn_generator):
    """Generates a random float and takes a random number generator as input"""
    
    return str(rn_generator.uniform(-100000, 100000))

def date_formats():
    """Creates commonly used date format specifiers.

    This function returns many common date formats but not all. As new formats
    are encountered this function should be modified to detect more.

    Returns:
        A list of date formats specifiers for datetime's strptime method.
    """

    months, separators, years = 'mbB', ' /-.', 'Yy'
    fmts = []
    for mth, sep, yr in itertools.product(months, separators, years):
        # build month and day first fmts
        x = [f'%{mth}{sep}%d{sep}%{yr}', f'%d{sep}%{mth}{sep}%{yr}']
        fmts.extend(x)

    return fmts


def make_random_date(rn_generator):
    """Generates a random date in a random format"""

    start_year = rn_generator.randint(1990, 2025)
    end_year = rn_generator(start_year, 2025)

    start_date = datetime.datetime(start_year, 1, 1)
    end_date = datetime.datetime(end_year, 12, 31)
    time_difference = end_date - start_date
    intermediate_num_days = rn_generator.randint(time_difference.days)
    date = start_date + datetime.timedelta(days=intermediate_num_days)

    all_date_formats = date_formats()

    date_format = rn_generator.choice(all_date_formats)

    return date.strftime(date_format)


def time_formats():
    """Creates commonly used time format specifiers.

    This function returns many common time formats but not all. As new formats
    are encountered this function should be modified.

    Returns:
        A list of time format specifiers for datetime's strptime method.
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

def make_random_time(rn_generator):
    """Generates a random time in a random format"""

    is_military = rn_generator.choice([True, False])

    minute = rn_generator.randint(0, 59)
    second = rn_generator.randint(0, 59)
    microsecond = rn_generator.randint(0, 999999)
    hour = rn_generator.randint(1, 23)

    time = datetime.time(hour=hour, minute=minute, second=second, microsecond=microsecond)
    all_time_formats = time_formats()
    time_format = rn_generator.choice(all_time_formats)

    return time.strftime(time_format)

def make_random_datetime(rn_generator):
    random_date = make_random_date(rn_generator)
    random_time = make_random_time(rn_generator)

    return f"{random_date} {random_time}"