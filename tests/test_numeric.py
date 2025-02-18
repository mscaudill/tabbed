import pytest
from itertools import product
import random
import string

from src.tabbed.utils import celltyping

# Fixture for returning a random number generator
@pytest.fixture
def rn_generator():
    """Returns a random number generator with the seed 1"""

    return random.Random(1)

@pytest.fixture(params=range(100)) # Now will call this fixture 100 times, each returning random integer
def valid_integer(request, rn_generator):
    """Returns valid integer as a string"""

    return str(rn_generator.randint(-100000, 100000))

@pytest.fixture(params=range(100))
def valid_float(request, rn_generator):
    """Returns valid float as a string"""

    return str(rn_generator.uniform(-100000, 100000))

@pytest.fixture(params=range(100))
def valid_scientific_notation_float(request, rn_generator):
    """Returns a valid float with scientific notation as a string"""

    significand = rn_generator.uniform(-10, 10)
    exponent = rn_generator.randint(-100, 100)
    if (request.param > 50):
        return str(significand) + "E" + str(exponent)
    else:
        return str(significand) + "e" + str(exponent)


@pytest.fixture(params=range(100))
def valid_complex(request, rn_generator):
    """Returns valid complex number as a string"""

    real_part = rn_generator.uniform(-100000, 100000)
    imag_part = rn_generator.uniform(-100000, 100000)

    if (imag_part < 0):
        add_plus = False
    else:
        add_plus = True

    real_part_str = str(real_part)
    imag_part_str = str(imag_part) + "j"

    if add_plus:
        return real_part_str + "+" + imag_part_str
    else:
        return real_part_str + imag_part_str

@pytest.fixture(params=range(100))
def non_numeric(request, rn_generator):
    """Returns a random non-numeric string"""

    length = rn_generator.randint(1, 20)
    all_chars = string.printable.strip()

    rand_str = "".join(rn_generator.choices(all_chars, k=length))

    non_numeric_insert_pos = rn_generator.randint(0, length+1)
    non_numeric_char = rn_generator.choice(string.ascii_letters + string.punctuation)

    # Inserting a non-numeric character always ensures the whole string is non-numeric
    rand_non_numeric = rand_str[:non_numeric_insert_pos] + non_numeric_char + rand_str[non_numeric_insert_pos:]

    return rand_non_numeric

# is_numeric tests

def test_classify_valid_integer(valid_integer):
    """Test that is_numeric returns true for a valid integer"""

    assert celltyping.is_numeric(valid_integer)

def test_classify_valid_float(valid_float):
    """Test that is_numeric returns true for a valid float"""

    assert celltyping.is_numeric(valid_float)

def test_classify_valid_float_scientific(valid_scientific_notation_float):
    """Test that is_numeric returns true for valid scientific notation float"""

    assert celltyping.is_numeric(valid_scientific_notation_float)

def test_classify_valid_complex(valid_complex):
    """Test that is_numeric returns true for a valid complex number"""

    assert celltyping.is_numeric(valid_complex)

@pytest.mark.xfail
def test_classify_non_numeric(non_numeric):
    """Test that is_numeric returns false for a non numeric value"""

    assert celltyping.is_numeric(non_numeric)

# as_numeric tests

def test_as_numeric_valid_integer(valid_integer):
    """Test that as_numeric does not return a string for valid integer (indicating failure)"""

    assert isinstance(celltyping.as_numeric(valid_integer), int)

def test_as_numeric_valid_float(valid_float):
    """Test that as_numeric does not return a string for valid float (indicating failure)"""

    assert isinstance(celltyping.as_numeric(valid_float), float)

def test_as_numeric_valid_complex(valid_complex):
    """Test that as_numeric does not return a string for a valid complex number (indicating failure)"""

    assert isinstance(celltyping.as_numeric(valid_complex), complex)

def test_as_numeric_valid_float_scientific(valid_scientific_notation_float):
    """Test that as_numeric does not return a string for valid scientific notation float (indicating failure)"""

    assert isinstance(celltyping.as_numeric(valid_scientific_notation_float), float)

@pytest.mark.xfail
def test_as_numeric_non_numeric(non_numeric):
    """Test that as_numeric returns a string (failure) for a non-numeric value"""

    assert not isinstance(celltyping.as_numeric(non_numeric))

# Convert tests with valid numeric values

def test_convert_valid_integer(valid_integer):
    """Test that convert does not return a string for a valid integer (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_integer), int)

def test_convert_valid_float(valid_float):
    """Test that convert does not return a string for a valid float (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_float), float)

def test_convert_valid_complex(valid_complex):
    """Test that convert does not return a string for a valid complex number (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_complex), complex)

def test_convert_valid_float_scientific(valid_scientific_notation_float):
    """Test that convert does not return a string for a valid scientific notation float (which indicates failure)"""

    assert isinstance(celltyping.convert(valid_scientific_notation_float), float)