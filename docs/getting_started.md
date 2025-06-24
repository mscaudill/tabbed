---
execute: true
---

## **__Introduction__**
This guide walks you through using Tabbed to read a text file containing
metadata and a header row that would be a challenge for many other text file
readers.

<div class="grid cards" markdown>
- [Sample Data](#sample-data)
- [Tabbed Wish List](#tabbed-wish-list)
- [Building a Tabbed Reader](#building-a-reader)
- [Row & Column Filtering](#row-&-column-filtering)
- [Reading](#reading)
- [When something goes wrong](#when-something-goes-wrong)
</div>

[comment]: # (pymdownx block which allows line nums but does not execute)

```py title="Imports" linenums="1"
import os
import tempfile
import random
from datetime import datetime, timedelta
```

[comment]: # (an mkdocs-execute block does not allow line nums but executes)

```python tags=['hide-input']
import os
import tempfile
import random
from datetime import datetime, timedelta

from tabbed.reading import Reader
```

## **__Sample Data__**
The documentation for Tabbed comes preloaded with a sample text file. Below we
open this file to see what it looks like and **develop a list of operations we
would like Tabbed to handle automatically for us.**

```py title="Preview Sample Data, linenums="0"
fp = './sample/annotations.txt'
# read the first 12 lines of the file
with open(fp, 'r') as infile:
    for line in infile.readlines()[:12]:
        print(line, end='')

```

```python tags=['hide-input']
fp = './samples/annotations.txt'
# read the first 12 lines of the file
with open(fp, 'r') as infile:
    for line in infile.readlines()[:12]:
        print(line, end='')
```

## **__Tabbed Wish List__**
To read files like this, we desire Tabbed to support the following:

=== "Header Detection"

    ### :material-numeric-1-box: __Header Detection__

    This sample file contains a **metadata section** prior to the **header** on
    line 7. Metadata can be unstructured like a paragraph or structured into
    columns separated by a delimiter. We want `Tabbed` to automatically detect
    the Metadata section and Header line of *any* file.

=== "Type Inference"

    ### :material-numeric-2-box: __Type Inference__
    
    The string cells in the sample file are encoding 4 different data types;
    *integers, datetimes, floats and strings.* We want `Tabbed` to perform
     **Type inference**.

=== "Row & Column Filtering"
    
    ### :material-numeric-3-box: __Row & Column Filtering__

    We want `Tabbed` to support simple value based row and column filtering.
    For example, in this file we might want only rows at which the `Start Time`
    column is less than `#!python datetime(2022, 2, 9, 9, 37, 13)` or where the
    `Annotation` column has a string value of `#!python 'exploring'` or both
    conditions.

=== "Partial & Iterative Reading"

    ### :material-numeric-4-box: __Partial & Iterative Reading__

    Text files can be large. `Tabbed` should support partial and iterative
    reading.

=== "Flexibility"

    ### :material-numeric-5-box: __Flexibility__

    Tabbed should be flexible. It should be able to `start` reading at any file
    position, `skip` reading of 'bad' rows,  allow for customizable filters, and
    allow users to choose how much memory to consume during iterative reading of
    large files. 


## **__Building a Tabbed Reader__**
`Tabbed's` Reader like Python's csv.Reader takes an `open` file instance. Here
we will build a reader and look at its properties, attributes and methods. At
any point you can use the help function to understand the Reader.

```py title="Build a Reader"
fp = './samples/annotations.txt'
infile = open(fp, 'r')
reader = Reader(infile)
```

```python tags=['hide-input']
fp = './samples/annotations.txt'
infile = open(fp, 'r')
reader = Reader(infile)
```

```py title="The Header and Metadata properties"
# print the Header and Metadata instances determined by this reader's sniffer
print(reader.header)
print(reader.metadata())
```

```python tags=['hide-input']
# print the header and metadata instances
print('Header instance\n', reader.header)

print('Metadata instance\n', reader.metadata())
```

```py title="Type Inference"
# print the types
types, consistent = reader.sniffer.types()
print(types)
```

```python tags=['hide-input']
# print the sniffer detected types
types, consistent = reader.sniffer.types()
print(types)
```
The dialect, metadata, header, and types are all determined by a reader's
`sniffer` instance property. The `sniffer` object samples the infile to measure
these properties. The lines it will sample can be changed using it's
`start`,`amount`,`skips` properties. This object performs the magic of
auto-detection for `Tabbed` readers.

```py title="sniffer property >>> help(sniffer) for more details."
#print the current sniffer used by the reader
print(reader.sniffer)
```

```python tags=["hide-input"]
#print the current sniffer used by the reader
print(reader.sniffer)
```

## **__Row & Column Filtering__**
`Tabbed` provides a powerful mechanism for value-based filtering of rows and
columns. 
