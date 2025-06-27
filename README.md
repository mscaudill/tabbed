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


## Installation

Detailed instructions on how to install the project.


## Dependencies


## Contributing

Guidelines for contributing to the project.


## Funding Acknowlegements


## License

[License information]


