# Installation

Tabbed is available on [pypi](https://pypi.org/project/tabbed/) and can be
installed into a virtual environment with `pip`. If your new to python package
installation and need help creating a virtual environment you'll want to check
out python's builtin [venv](https://docs.python.org/3/library/venv.html) OR [
miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main).

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

## Dependencies
Tabbed relies on [clevercsv](https://clevercsv.readthedocs.io/en/latest/) and
Python >= 3.11. `pip` will fetch these dependencies for you automatically.
