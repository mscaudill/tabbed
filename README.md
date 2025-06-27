<h1 align="center">
    <img src="https://github.com/mscaudill/tabbed/blob/master/docs/imgs/namedlogo.png" 
    style="width:600px;height:auto;"/>
</h1>


# Selective and Scalable Reading of Irregular Text Files 


[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![PyPI - License](https://img.shields.io/pypi/l/openseize?color=teal)

**Tabbed** is a Python library for reading variably structured text files. It
automatically deduces data start locations, data types and performs iterative
and value-based conditional reading of data rows.

[**Key Features**](#key-features)
| [**Usage**](#usage)
| [**Documentation**](#documentation)
| [**Installation**](#installation)
| [**Dependencies**](#dependencies)
| [**Acknowledgments**](acknowledgements)
| [**Contributing**](#contributing)

-----------------

## Key Features

- **Structural Inference:**  
A common variant of the [standard]() text file is one that contains *metadata*
prior to a header or data section. Tabbed can locate the metadata, header and
data locations in a file.

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

Examples of how to use the project.

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

```python
from tabbed.reading import Reader

infile = open('annotations.txt', 'r')
reader = Reader(infile)
    
dialect = reader.dialect
types, _ = reader.sniffer.types()
    
print(dialect) # a clevercsv SimpleDialect
print('---')
print(types)
```

**Output**
```
SimpleDialect('\t', '"', None)
---
[<class 'int'>, <class 'datetime.datetime'>, <class 'datetime.datetime'>, <class 'float'>, <class 'str'>, <class 'str'>]
```

**Metadata and Header detection**

```python
print(reader.header)
print('---')
print(reader.metadata)
```

**Output**
```
Header(line=6,
       names=['Number', 'Start_Time', 'End_Time', 'Time_From_Start', 'Channel', 'Annotation'],
       string='Number\tStart Time\tEnd Time\tTime From Start\tChannel\tAnnotation')
---
MetaData(lines=(0, 6),
         string='Experiment ID\tExperiment\nAnimal ID\tAnimal\nResearcher\tTest\nDirectory path\t\n\n')
```

**Filtered Reading with Tabs**

```python
from itertools import chain

# tab rows whose Start_Time is between 9:38 and 9:40 and set reader to read
# only the Number and Start_Time columns
reader.tab(Start_Time='<2/09/2022 9:40:00', columns=['Number', 'Start_Time')

# read the data to an iterator reading only 2 rows at a time
gen = reader.read(chunksize=2)

# convert to an in-memory list
data = chain.from_iterable(gen)
print(data)
```

**Output**
```
{'Number': 5, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 1, 262000)}
{'Number': 6, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 7, 909000)}
{'Number': 7, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 20, 258000)}
{'Number': 8, 'Start_Time': datetime.datetime(2022, 2, 9, 9, 38, 25, 435000)}
```

## Installation

Detailed instructions on how to install the project.


## Dependencies


## Contributing

Guidelines for contributing to the project.


## Funding Acknowlegements


## License

[License information]


