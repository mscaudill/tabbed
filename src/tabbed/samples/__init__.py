"""Adds a SimpleNamespace called 'paths' to the sample modules namespace for
'.' attribute access of the sample '.txt' files."""

from pathlib import Path
from types import SimpleNamespace

from tabbed import samples  # pylint: disable=import-self

paths = SimpleNamespace(
    **{
        p.stem: p
        for p in Path(samples.__file__).parent.iterdir()
        if p.name.endswith('txt')
    }
)
