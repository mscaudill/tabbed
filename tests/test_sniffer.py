import random
import tempfile

import pytest

from tabbed.sniffing import Sniffer

@pytest.fixture
def sample_file():
    """Sets up and tears down a sample delimited text file."""

    # TODO would be great if I were a fixture
    metadata = ('This is a long unstructured metadata string\n'
                'That is useful for testing unstructured metadata\n'
                'delimited text files.')

    # TODO would be great to make me a fixture
    header = ['apples', 'oranges', 'pears', 'peaches']

    # TODO would be great if we were a fixture too!
    gen = random.Random(0)
    data = [[str(gen.randint(-100, 100)) for _ in range(len(header))] for _ in
            range(200)]

    # TODO Notice we should vary separators too
    stringed_header = ','.join(header)
    stringed_data = '\n'.join([','.join(row) for row in data])
    string = '\n'.join([metadata, stringed_header, stringed_data])

    for idx, row in enumerate(string.splitlines()):
        print(idx, row)

    outfile = tempfile.TemporaryFile(mode='w+')
    _ = outfile.write(string)
    yield outfile

    print('Closing file resource')
    outfile.close()

def test_line_count(sample_file):
    """ """

    sniffer = Sniffer(sample_file)
    assert sniffer.line_count == 204


