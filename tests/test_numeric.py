import pytest
from itertools import product
import random
import string
from helpers import assert_n_generated_values

from src.tabbed.utils import celltyping

@pytest.fixture
def valid_integer_gen(integer_generator):
    """Returns a generator of valid integers as strings"""

    def valid_integer_gen():
        while True:
            int_val = next(integer_generator)
            yield str(int_val)

    return valid_integer_gen()

@pytest.fixture
def valid_float_gen(float_generator):
    """Returns generator of valid float as a string"""

    def valid_float_gen():
        while True:
            float_val = next(float_generator)
            yield str(float_val)

    return valid_float_gen()

@pytest.fixture
def valid_scientific_notation_float_gen(rn_generator):
    """Returns generator of valid float with scientific notation as a string"""

    def sci_not_float_gen():
        while True:
            significand = rn_generator.uniform(-10, 10)
            exponent = rn_generator.randint(-100, 100)
            if (rn_generator.random() > .5):
                yield str(significand) + "E" + str(exponent)
            else:
                yield str(significand) + "e" + str(exponent)
            
    return sci_not_float_gen()
    

@pytest.fixture
def valid_complex_gen(complex_generator):
    """Returns generator of valid complex number as a string"""

    def valid_complex_gen():
        while True:
            complex_val = next(complex_generator)
            yield repr(complex_val)

    return valid_complex_gen()

@pytest.fixture
def non_numeric_gen(non_numeric_generator):
    """Returns generator of random non-numeric string"""

    def non_numeric_gen():
        while True:
            non_numeric_val = next(non_numeric_generator)
            yield str(non_numeric_val)

    return non_numeric_gen()

# is_numeric tests

def test_classify_valid_integer(valid_integer_gen):
    """Test that is_numeric returns true for a valid integer"""

    assert_n_generated_values(valid_integer_gen, 100, celltyping.is_numeric)


def test_classify_valid_float(valid_float_gen):
    """Test that is_numeric returns true for a valid float"""

    assert_n_generated_values(valid_float_gen, 100, celltyping.is_numeric)

def test_classify_valid_float_scientific(valid_scientific_notation_float_gen):
    """Test that is_numeric returns true for valid scientific notation float"""

    assert_n_generated_values(valid_scientific_notation_float_gen, 100, celltyping.is_numeric)

def test_classify_valid_complex(valid_complex_gen):
    """Test that is_numeric returns true for a valid complex number"""

    assert_n_generated_values(valid_complex_gen, 100, celltyping.is_numeric)

@pytest.mark.xfail
def test_classify_non_numeric(non_numeric_generator):
    """Test that is_numeric returns false for a non numeric value"""

    assert_n_generated_values(non_numeric_generator, 100, celltyping.is_numeric)

# as_numeric tests

def test_as_numeric_valid_integer(valid_integer_gen):
    """Test that as_numeric does not return a string for valid integer (indicating failure)"""

    test_func = lambda val: isinstance(celltyping.as_numeric(val), int)
    assert_n_generated_values(valid_integer_gen, 100, test_func)

def test_as_numeric_valid_float(valid_float_gen):
    """Test that as_numeric does not return a string for valid float (indicating failure)"""

    test_func = lambda val: isinstance(celltyping.as_numeric(val), float)
    assert_n_generated_values(valid_float_gen, 100, test_func)

def test_as_numeric_valid_complex(valid_complex_gen):
    """Test that as_numeric does not return a string for a valid complex number (indicating failure)"""
    
    test_func = lambda val: isinstance(celltyping.as_numeric(val), complex)
    assert_n_generated_values(valid_complex_gen, 100, test_func)

def test_as_numeric_valid_float_scientific(valid_scientific_notation_float_gen):
    """Test that as_numeric does not return a string for valid scientific notation float (indicating failure)"""

    test_func = lambda val: isinstance(celltyping.as_numeric(val), float)
    assert_n_generated_values(valid_scientific_notation_float_gen, 100, test_func)

# Convert tests with valid numeric values

def test_convert_valid_integer(valid_integer_gen):
    """Test that convert does not return a string for a valid integer (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), int)
    assert_n_generated_values(valid_integer_gen, 100, test_func)

def test_convert_valid_float(valid_float_gen):
    """Test that convert does not return a string for a valid float (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), float)
    assert_n_generated_values(valid_float_gen, 100, test_func)

def test_convert_valid_complex(valid_complex_gen):
    """Test that convert does not return a string for a valid complex number (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), complex)
    assert_n_generated_values(valid_complex_gen, 100, test_func)

def test_convert_valid_float_scientific(valid_scientific_notation_float_gen):
    """Test that convert does not return a string for a valid scientific notation float (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), float)
    assert_n_generated_values(valid_scientific_notation_float_gen, 100, test_func)