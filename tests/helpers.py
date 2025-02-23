from typing import TypeVar, Generator, Callable

T = TypeVar("T")
def assert_n_generated_values(gen:Generator[T, None, None], n:int, val_func: Callable[[T], bool]):
    """
    Calls next(gen) n times and applies test_fn(value) each time.
    Raises AssertionError if test_fn returns False for any value.

    Args:
        gen: A generator that yields strings.
        n: The number of values to generate and check.
        test_fn: A function that takes a string and returns True/False.

    Returns:
        Nothing
    """

    for _ in range(n):
        val = next(gen)
        assert val_func(val)