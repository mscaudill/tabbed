import pytest
from itertools import product
import random
import string
from helpers import assert_n_generated_values

from src.tabbed.utils import celltyping

# is_numeric tests

def test_classify_valid_integer(integer_generator):
    """Test that is_numeric returns true for a valid integer"""

    assert_n_generated_values(integer_generator, 100, celltyping.is_numeric)


def test_classify_valid_float(float_generator):
    """Test that is_numeric returns true for a valid float"""

    assert_n_generated_values(float_generator, 100, celltyping.is_numeric)

def test_classify_valid_float_scientific(scientific_notation_float_generator):
    """Test that is_numeric returns true for valid scientific notation float"""

    assert_n_generated_values(scientific_notation_float_generator, 100, celltyping.is_numeric)

def test_classify_valid_complex(complex_generator):
    """Test that is_numeric returns true for a valid complex number"""

    assert_n_generated_values(complex_generator, 100, celltyping.is_numeric)

@pytest.mark.xfail
def test_classify_non_numeric(non_numeric_generator):
    """Test that is_numeric returns false for a non numeric value"""

    assert_n_generated_values(non_numeric_generator, 100, celltyping.is_numeric)

# as_numeric tests

def test_as_numeric_valid_integer(integer_generator):
    """Test that as_numeric does not return a string for valid integer (indicating failure)"""

    test_func = lambda val: isinstance(celltyping.as_numeric(val), int)
    assert_n_generated_values(integer_generator, 100, test_func)

def test_as_numeric_valid_float(float_generator):
    """Test that as_numeric does not return a string for valid float (indicating failure)"""

    test_func = lambda val: isinstance(celltyping.as_numeric(val), float)
    assert_n_generated_values(float_generator, 100, test_func)

def test_as_numeric_valid_complex(complex_generator):
    """Test that as_numeric does not return a string for a valid complex number (indicating failure)"""
    
    test_func = lambda val: isinstance(celltyping.as_numeric(val), complex)
    assert_n_generated_values(complex_generator, 100, test_func)

def test_as_numeric_valid_float_scientific(scientific_notation_float_generator):
    """Test that as_numeric does not return a string for valid scientific notation float (indicating failure)"""

    test_func = lambda val: isinstance(celltyping.as_numeric(val), float)
    assert_n_generated_values(scientific_notation_float_generator, 100, test_func)

# Convert tests with valid numeric values

def test_convert_valid_integer(integer_generator):
    """Test that convert does not return a string for a valid integer (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), int)
    assert_n_generated_values(integer_generator, 100, test_func)

def test_convert_valid_float(float_generator):
    """Test that convert does not return a string for a valid float (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), float)
    assert_n_generated_values(float_generator, 100, test_func)

def test_convert_valid_complex(complex_generator):
    """Test that convert does not return a string for a valid complex number (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), complex)
    assert_n_generated_values(complex_generator, 100, test_func)

def test_convert_valid_float_scientific(scientific_notation_float_generator):
    """Test that convert does not return a string for a valid scientific notation float (which indicates failure)"""

    test_func = lambda val: isinstance(celltyping.convert(val), float)
    assert_n_generated_values(scientific_notation_float_generator, 100, test_func)