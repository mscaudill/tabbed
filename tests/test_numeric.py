from itertools import product
import random
import string

import pytest

from tabbed.utils import celltyping

# is_numeric tests


@pytest.mark.parametrize("random_integers", [100], indirect=True)
def test_classify_valid_integer(random_integers):
    """Tests that each of the 100 random integers are classified as numeric by
    celltyping's is_numeric"""

    for int_val in random_integers:
        assert celltyping.is_numeric(int_val)


@pytest.mark.parametrize("random_floats", [100], indirect=True)
def test_classify_valid_float(random_floats):
    """Tests that each of the 100 random floats are classified as numeric by celltyping's is_numeric"""

    for float_val in random_floats:
        assert celltyping.is_numeric(float_val)


@pytest.mark.parametrize(
    "random_scientific_notation_floats", [100], indirect=True
)
def test_classify_valid_float_scientific(random_scientific_notation_floats):
    """Tests that each of the 100 random scientific notation floats are classified as numeric by celltyping's is_numeric"""

    for float_val in random_scientific_notation_floats:
        assert celltyping.is_numeric(float_val)


@pytest.mark.parametrize("random_complex_numbers", [100], indirect=True)
def test_classify_valid_complex(random_complex_numbers):
    """Tests that each of the 100 random complex numbers are classified as numeric by celltyping's is_numeric"""

    for complex_num in random_complex_numbers:
        assert celltyping.is_numeric(complex_num)


@pytest.mark.xfail
@pytest.mark.parametrize("random_non_numerics", [100], indirect=True)
def test_classify_non_numeric(random_non_numerics):
    """Tests that each of the 100 random non-numerics are not classified as numerics"""

    for non_numeric_val in random_non_numerics:
        assert celltyping.is_numeric(non_numeric_val)


# as_numeric tests
@pytest.mark.parametrize("random_integers", [100], indirect=True)
def test_as_numeric_valid_integer(random_integers):
    """Tests that each of the 100 random integers are converted to integers"""

    for integer_val in random_integers:
        assert isinstance(celltyping.as_numeric(integer_val), int)


@pytest.mark.parametrize("random_floats", [100], indirect=True)
def test_as_numeric_valid_float(random_floats):
    """Tests that each of the 100 random floats are converted to floats"""

    for float_val in random_floats:
        assert isinstance(celltyping.as_numeric(float_val), float)


@pytest.mark.parametrize("random_complex_numbers", [100], indirect=True)
def test_as_numeric_valid_complex(random_complex_numbers):
    """Tests that each of the 100 random complex numbers are converted to complex numbers"""

    for complex_val in random_complex_numbers:
        assert isinstance(celltyping.as_numeric(complex_val), complex)


@pytest.mark.parametrize(
    "random_scientific_notation_floats", [100], indirect=True
)
def test_as_numeric_valid_float_scientific(random_scientific_notation_floats):
    """Tests that each of the 100 random scientific notation floats are converted to floats"""

    for float_val in random_scientific_notation_floats:
        assert isinstance(celltyping.as_numeric(float_val), float)


# Convert tests with valid numeric values


@pytest.mark.parametrize("random_integers", [100], indirect=True)
def test_convert_valid_integer(random_integers):
    """Test that convert does not return a string for a valid integer (which indicates failure)"""

    for int_val in random_integers:
        assert isinstance(celltyping.convert(int_val), int)


@pytest.mark.parametrize("random_floats", [100], indirect=True)
def test_convert_valid_float(random_floats):
    """Test that convert does not return a string for a valid float (which indicates failure)"""

    for float_val in random_floats:
        assert isinstance(celltyping.convert(float_val), float)


@pytest.mark.parametrize("random_complex_numbers", [100], indirect=True)
def test_convert_valid_complex(random_complex_numbers):
    """Test that convert does not return a string for a valid complex number (which indicates failure)"""

    for complex_val in random_complex_numbers:
        assert isinstance(celltyping.convert(complex_val), complex)


@pytest.mark.parametrize(
    "random_scientific_notation_floats", [100], indirect=True
)
def test_convert_valid_float_scientific(random_scientific_notation_floats):
    """Test that convert does not return a string for a valid scientific notation float (which indicates failure)"""

    for float_val in random_scientific_notation_floats:
        assert isinstance(celltyping.convert(float_val), float)
