# import pytest
# from itertools import product, islice
# import re
# import random
# import string
# import datetime
# import tempfile
# from typing import List

# from tabbed import sniffing

# @pytest.fixture
# def blank_file():
#     """Creates a temporary empty file object."""
#     file = tempfile.TemporaryFile("w+")
    
#     return file

# @pytest.fixture
# def blank_file_sniffer(blank_file):
#     sniffer = sniffing.Sniffer(blank_file)

#     yield sniffer

#     blank_file.close()

# @pytest.fixture(params=[1, 2, 4, 8, 256, 512, 1024])
# def column_count(request):
#     """Returns a column count that is consistent across all generators of rows"""

#     return request.param

# @pytest.fixture
# def has_numeric_row_generator(column_count, string_generator, numeric_generator, rn_generator):
#     columns = column_count

#     def numeric_row_generator():
#         while True:
#             row = [val for val in islice(string_generator, columns-1)]
#             numeric_insert_pos = rn_generator.randint(0, columns)
#             numeric_val = next(numeric_generator)

#             row.insert(numeric_insert_pos, numeric_val)
#             yield row

#     return numeric_row_generator()

# @pytest.fixture
# def non_numeric_row_generator(column_count, non_numeric_generator):
#     columns = column_count

#     def non_numeric_row_generator():
#         while True:
#             row = [val for val in islice(non_numeric_generator, columns)]
#             yield row

#     return non_numeric_row_generator()


# @pytest.mark.parametrize("num_rows", [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
# def test_non_numeric(num_rows, has_numeric_row_generator, non_numeric_row_generator, rn_generator, blank_file_sniffer):
#     def rows_and_first_non_numeric() -> tuple[List[List[str]], int]:
#         last_non_numeric_index = None

#         rows = [None] * num_rows
#         for i in reversed(range(num_rows)):
#             if (rn_generator.random() > .5):
#                 new_row = next(has_numeric_row_generator)
#                 rows[i] = new_row
#             else:
#                 if not last_non_numeric_index:
#                     last_non_numeric_index = i
#                 rows[i] = next(non_numeric_row_generator)

        
#         return rows, last_non_numeric_index

#     for _ in range(10):
#         val = rows_and_first_non_numeric()
        
#         rows, first_idx = val
#         indices = list(range(len(rows)))

#         assert blank_file_sniffer._nonnumeric(rows, indices) == first_idx


    