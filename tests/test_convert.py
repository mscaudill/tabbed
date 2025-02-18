import pytest
from itertools import product
import random
import string
from datetime import datetime

from tabbed.utils import celltyping

def test_convert():
    all_vals = ["2", 
                "2.535", 
                "5+6j", 
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime()]