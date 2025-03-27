import pytest
from itertools import product
import random
import string
import datetime

from tabbed.utils import celltyping


# TODO docstring
def test_convert():
    all_vals = [
        "Hello",
        "2",
        "2.535",
        "5+6j",
        datetime.datetime.now().strftime("%m-%d-%Y"),
        datetime.datetime.now().strftime("%H:%M:%S"),
        datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S"),
    ]

    expected_types = [
        str,
        int,
        float,
        complex,
        datetime.date,
        datetime.time,
        datetime.datetime,
    ]

    for i in range(len(all_vals)):
        converted_val = celltyping.convert(all_vals[i])
        expected_type = expected_types[i]
        if expected_type == datetime.date:
            assert isinstance(converted_val, datetime.datetime)
            assert isinstance(converted_val.date(), datetime.date)
        elif expected_type == datetime.time:
            assert isinstance(converted_val, datetime.datetime)
            assert isinstance(converted_val.time(), datetime.time)
        else:
            assert type(converted_val) == expected_type
