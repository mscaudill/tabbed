import pytest
from itertools import product
import re
import random
import string
import datetime
import tempfile

from tabbed import sniffing

@pytest.fixture
def blank_file():
    return tempfile.TemporaryFile()

