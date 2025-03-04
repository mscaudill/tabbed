import pytest
import random
import string
from typing import Callable, Generator, TypeVar
import re

import helpers

# Fixture for returning a random number generator
@pytest.fixture
def rn_generator():
    """Returns a random number generator with the seed 1"""

    return random.Random(1)

# Numeric-related Fixtures
@pytest.fixture
def random_integers(rn_generator, request):
    """This returns a list of n random integers. n is passed in through indirect parameterization"""

    return [helpers.make_random_integer(rn_generator) for _ in range(request.param)]
    


@pytest.fixture
def random_floats(rn_generator, request):
    """This returns a list of n random floats. n is passed in through indirect parameterization"""

    return [helpers.make_random_float(rn_generator) for _ in range(request.param)]

@pytest.fixture
def random_complex_numbers(rn_generator, request):
    """This returns a list of n random complex numbers. n is passed in through indirect parameterization"""
    
    return [helpers.make_random_complex_num(rn_generator) for _ in range(request.param)]

@pytest.fixture
def random_scientific_notation_floats(rn_generator, request):
    """Returns a list of n scientific notation floats. n is passed in through indirect parameterization"""

    return [helpers.make_random_sci_not_float(rn_generator) for _ in range(request.param)]

@pytest.fixture
def random_numerics(rn_generator, request):
    """Returns a list of n numerics. n is passed in through indirect parameterization"""

    return [helpers.make_random_numeric(rn_generator) for _ in range(request.param)]

@pytest.fixture
def random_non_numerics(rn_generator, request):
    """Returns a generator of random non-numeric strings"""

    return [helpers.make_random_non_numeric(rn_generator) for _ in range(request.param)]

@pytest.fixture
def random_strings(rn_generator, request):
    """Returns a generator of random strings"""

    return [helpers.make_random_string(rn_generator) for _ in range(request.param)]
