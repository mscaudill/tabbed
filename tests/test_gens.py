import itertools
import random
import pytest

@pytest.fixture
def rng():
    """Returns a python random state generator with seed 0."""

    return random.Random(1)





# Current Approach using redirection
@pytest.fixture
def agenerator(rng):
    """Builds an infinite generator of random integers with seed 1."""

    return (rng.randint(0, 1000) for _ in itertools.count())

def generate_n(generator, count):
    """Returns first count number of items from a generator.

    The current pull request is actually combining this with testing via the
    "assert_n_generated_values"
    """

    return itertools.islice(generator, 0, count)

def test_function_iseven0(agenerator):
    """Test if each value in a generator is even."""

    # notice the hard-coding of 100 count here
    # if the goal is to allow for generators of differing amounts then this
    # didn't really work
    for number in generate_n(agenerator, 100):
        assert number % 2 == 0




# Direct parameterization -- notice we are in-between hard coding the count and
# a real parameter its partially parameterizable
@pytest.fixture(params=[100])
def random_integers(rng, request):
    """Returns param count number of random integers."""

    return (rng.randint(0, 1000) for _ in range(request.param))

def test_function_iseven2(random_integers):
    """ """

    for num in random_integers:
        assert num % 2 == 0



# Indirect parameterization -- fully parameterizable
@pytest.fixture
def random_integers(rng, request):
    #Returns param count number of random integers.

    return [rng.randint(0, 1000) for _ in range(request.param)]

# ignore -- dont like
@pytest.fixture
def random100_integers(rng):
    """ """

    return [rng.randint(0, 1000) for _ in range(100)]

@pytest.fixture
def random_floats(rng, request):
    """Returns request param count number of floats."""

    a, b = -1000, 1000
    return [rng.uniform(a, b) for _ in range(request.param)]


# FAILS -- fixtures ignore marks so cannot except parameterizable fixtures
@pytest.fixture
@pytest.mark.parametrize("random_integers", [100], indirect=True)
@pytest.mark.parametrize("random_floats", [100], indirect=True)
def random_real(random_integers, random_floats):
    """First attempt at mixing parameterizable fixtures."""

    print(random_integers)
    print(random_floats)

    assert True

# We like this
# indirect allows the fixture to be parameterized dynamically -- when the test
# occurs not when the fixture is made
@pytest.mark.parametrize("random_integers", [100], indirect=True)
@pytest.mark.parametrize("random_floats", [100], indirect=True)
def test_function_iseven1(random_integers, random_floats):
    """ """

    print(random_integers)
    print(random_floats)

    assert True
