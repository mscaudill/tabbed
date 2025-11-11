<h1 align="center">
    <img src="https://github.com/mscaudill/tabbed/raw/master/docs/imgs/namedlogo.png"
    style="width:600px;height:auto;"/>
</h1>

## A Python package for reading variably structured text files at scale

[![status](
https://joss.theoj.org/papers/4c0ca4b9e42cf06da96fbc87c79d3ab1/status.svg)](
https://joss.theoj.org/papers/4c0ca4b9e42cf06da96fbc87c79d3ab1)
[![documentation](
https://img.shields.io/badge/github.io-Docs-seagreen)](
https://mscaudill.github.io/tabbed/
)
![python](https://img.shields.io/badge/Python-%3E%3D3.12-blue)
[![Code style: black](https://img.shields.io/badge/style-black-black.svg)](
https://github.com/psf/black
)
[![pytest](
https://github.com/mscaudill/tabbed/actions/workflows/testing.yml/badge.svg)](
https://github.com/mscaudill/tabbed/actions/workflows/testing.yml
)
[![coverage](
https://coveralls.io/repos/github/mscaudill/tabbed/badge.svg?branch=master)](
https://coveralls.io/github/mscaudill/tabbed?branch=master
)
![license](
https://img.shields.io/pypi/l/tabbed?color=darkmagenta
)

**Tabbed** is a Python library for reading variably structured text files. It
automatically deduces data start locations, data types and performs iterative
and value-based conditional reading of data rows.

[**Key Features**](#key-features)
| [**Usage**](#usage)
| [**Documentation**](#documentation)
| [**Dependencies**](#dependencies)
| [**Installation**](#installation)
| [**Contributing**](#contributing)
| [**Acknowledgments**](acknowledgements)

-----------------

## Key Features

- **Structural Inference:**  
A common variant of the
[standard](https://datatracker.ietf.org/doc/html/rfc4180) text file is one that
contains *metadata* prior to a header or data section. Tabbed can locate the
metadata, header and data locations in a file.

- **Type inference:**  
Tabbed can parse `int`, `float`, `complex`, `time`, `date` and `datetime`
instances at high-speed via a polling strategy.

- **Conditional Reading:**  
Tabbed can filter rows during reading with equality, membership, rich
comparison, regular expression matching and custom callables via simple keyword
arguments.

- **Partial and Iterative Reading:**  
Tabbed supports reading of large text files that consumes only as much memory as
you choose.


## Usage

Below is a sample file with a *Metadata* section and *Header* using the tab
character as the delimiter.

**annotations.txt**
```AsciiDoc
Experiment ID Experiment
Animal ID Animal
Researcher Test
Directory path 

Number Start Time End Time Time From Start Channel Annotation
0 02/09/22 09:17:38.948 02/09/22 09:17:38.948 0.0000 ALL Started Recording
1 02/09/22 09:37:00.000 02/09/22 09:37:00.000 1161.0520 ALL start
2 02/09/22 09:37:00.000 02/09/22 09:37:08.784 1161.0520 ALL exploring
3 02/09/22 09:37:08.784 02/09/22 09:37:13.897 1169.8360 ALL grooming
4 02/09/22 09:37:13.897 02/09/22 09:38:01.262 1174.9490 ALL exploring
5 02/09/22 09:38:01.262 02/09/22 09:38:07.909 1222.3140 ALL grooming
6 02/09/22 09:38:07.909 02/09/22 09:38:20.258 1228.9610 ALL exploring
7 02/09/22 09:38:20.258 02/09/22 09:38:25.435 1241.3100 ALL grooming
8 02/09/22 09:38:25.435 02/09/22 09:40:07.055 1246.4870 ALL exploring
9 02/09/22 09:40:07.055 02/09/22 09:40:22.334 1348.1070 ALL grooming
10 02/09/22 09:40:22.334 02/09/22 09:41:36.664 1363.3860 ALL exploring
```

**Dialect and Type Inference**

Tabbed can detect the dialect via [clevercsv](
https://clevercsv.readthedocs.io/en/latest/)  and infer the data types.

```python
from tabbed.reading import Reader
from tabbed.samples import paths

infile = open(paths.annotations, 'r')
reader = Reader(infile)
dialect = reader.sniffer.dialect
types, _ = reader.sniffer.types(poll=10)
    
print(dialect) # a clevercsv SimpleDialect
print('---')
print(types)
```

*Output*
```
SimpleDialect('\t', '"', None)
---
[<class 'int'>, <class 'datetime.datetime'>, <class 'datetime.datetime'>, <class 'float'>, <class 'str'>, <class 'str'>]
```

**Metadata and Header detection**

Tabbed can automatically locate the metadata, header and data rows.

```python
print(reader.header)
print('---')
print(reader.metadata())
```

*Output*
```
Header(line=6,
       names=['Number', 'Start_Time', 'End_Time', 'Time_From_Start', 'Channel', 'Annotation'],
       string='Number\tStart Time\tEnd Time\tTime From Start\tChannel\tAnnotation')
---
MetaData(lines=(0, 6),
         string='Experiment ID\tExperiment\nAnimal ID\tAnimal\nResearcher\tTest\nDirectory path\t\n\n')
```

**Filtered Reading with Tabs**

Tabbed supports row and column filtering with equality, membership, rich
comparison and regular expression matching. Its also fully iterative allowing
users to choose the amount of memory to consume during file reading.

```python
from itertools import chain

# tab rows whose Start_Time is between 9:38 and 9:40 and set reader to read
# only the Number and Start_Time columns
reader.tab(
    Start_Time='>= 2/09/2022 9:38:00 and <2/09/2022 9:40:00',
    columns=['Number', 'Start_Time']
)

# read the data to an iterator reading only 2 rows at a time
gen = reader.read(chunksize=2)

# convert to an in-memory list
data = list(chain.from_iterable(gen))
print(data)

# close the reader when done or open under context-management
reader.close()
```

*Output*
```
{'Number': 5, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 1, 262000)}
{'Number': 6, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 7, 909000)}
{'Number': 7, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 20, 258000)}
{'Number': 8, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 25, 435000)}
```

## Documentation
The official documentation is hosted on [github.io](https://mscaudill.github.io/tabbed/).


## Dependencies
Tabbed depends on the excellent [clevercsv](
https://clevercsv.readthedocs.io/en/latest/) package for dialect detection. The
rest is pure Python.


## Installation

Tabbed is hosted on [pypi](https://pypi.org/project/tabbed/) and can be
installed with pip into a virtual environment.

```bash
pip install tabbed
```

To get a development version of `Tabbed` from source start by cloning the
repository

```bash
git clone git@github.com:mscaudill/tabbed.git
```

Go to the directory you just cloned and create an *editable install* with pip.
```bash
pip install -e .[dev]
```

## Contributing

We're excited you want to contribute! Please check out our
[Contribution](
https://github.com/mscaudill/tabbed/blob/master/.github/CONTRIBUTING.md) guide.


## Acknowledgements

------

**We are grateful for the support of the Ting Tsung and Wei Fong Chao
Foundation and the Jan and Dan Duncan Neurological Research Institute at
Texas Children's that generously supports Tabbed.**

------
