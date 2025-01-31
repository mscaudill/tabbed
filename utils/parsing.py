"""A module of boolean test for parsing tabs passed as keyword arguments."""

from celltyping import CellType

def is_comparison(item: Any) -> bool:
    """Test if astring contains any rich comparisons.

    This method is susceptible to False positives since strings may contain rich
    comparison notation without an actual comparison intended.

    Args:
        astring:
            A string that possibly contains a rich comparison.

    Returns:
        True if astring contains no more than count rich comparisons.
    """

    # comparisons are always string type
    if not isinstance(item, str):
        return False

    # remove all spaces
    x = ''.join(item.split())
    found = [key for key in rich_comparisons() if key in x]

    return bool(found)

def is_regex(item: Any) -> bool:
    """Test if item is a compiled regular expression pattern.

    Args:
        item:
            Object to test if compiled regex.

    Returns:
        True if item is instance of re.Pattern and False otherwise.
    """

    return isinstance(item, re.Pattern)

def is_sequence(item: Any) -> bool:
    """Test if item is a Sequence.

    Args:
        item:
            Object to test if Sequence.

    Returns:
        True if item is Sequence and False otherwise.
    """

    return isinstance(item, Sequence)

def is_celltype(item: Any) -> bool:
    """Test if item is a Tabbed support CellType.

    Args:
        item:
            Object to test if CellType.

    Returns:
        True if item is CellType and False otherwise.
    """

    return isinstance(item, CellType)


