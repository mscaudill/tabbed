---
execute: true
---

## **__Introduction__**
This guide walks you through using Tabbed to read a text file containing
metadata and a header row that would be a challenge for many other text file
readers.

<div class="grid cards" markdown>
- :material-numeric-1-box-outline: [Sample Data](#sample-data)
- :material-numeric-2-box-outline: [Tabbed Wish List](#tabbed-wish-list)
- :material-numeric-3-box-outline: [Building a Tabbed Reader](#building-a-reader)
- :material-numeric-4-box-outline: [File Sniffing](#file-sniffing)
- :material-numeric-5-box-outline: [Data Filtering](#data-filtering)
- :material-numeric-6-box-outline: [Reading](#reading)
- :material-numeric-7-box-outline: [When something goes wrong](#when-something-goes-wrong)
</div>

[comment]: # (pymdownx block which allows line nums but does not execute)

```py title="Imports" linenums="1"
import os
import tempfile
import random
from datetime import datetime, timedelta
from itertools import chain

from tabbed.reading import Reader
```

[comment]: # (an mkdocs-execute block does not allow line nums but executes)

```python tags=['hide-input']
import os
import tempfile
import random
from datetime import datetime, timedelta
from itertools import chain

from tabbed.reading import Reader
```

## **__Sample Data__**
The documentation for Tabbed comes preloaded with a sample text file. Below we
open this file to see what it looks like and **develop a list of operations we
would like Tabbed to handle automatically for us.**

``` py title="Preview Sample Data"
fp = './sample/annotations.txt'
with open(fp, 'r') as infile:
    for line in infile:
        print(line, end='')
```

??? example "View Sample Data"
``` python tags=['hide-input']
fp = './samples/annotations.txt'
with open(fp, 'r') as infile:
    for line in infile:
        # split on tabs and join on markdown tab
        line = line.split('\t')
        line = '&emsp;'.join(line)
        # replace newline with markdown newline
        line = line.replace('\n', '  ')
        print(line)
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

=== "Data Filtering"
    
    ### :material-numeric-3-box: __Data Filtering__

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
    position, `skip` reading of 'bad' rows, and allow users to choose how much
     memory to consume during iterative reading of large files. 


## **__Building a Tabbed Reader__**
`Tabbed's` Reader like Python's csv.Reader takes an `open` file instance. Here
we will build a reader and look at its properties, attributes and methods. At
any point you can use the help function to understand the Reader.

``` py title="Build a Reader"
fp = './samples/annotations.txt'
infile = open(fp, 'r')
reader = Reader(infile)
```

``` python tags=['hide-input']
fp = './samples/annotations.txt'
infile = open(fp, 'r')
reader = Reader(infile)
```

## **__File Sniffing__**
`Tabbed's` reader has an embedded `Sniffer` instance. It is similar to Python's
builtin `csv.Sniffer` but it is capable of detecting the metadata, header and
data types in a file. It does this by sampling the file. The sample the sniffer
uses can be modified by its `start`,`amount`, & `skips` properties.  In most
cases the default values for these parameters will correctly detect the file
structure and data types for type conversion.

``` py title="Header and Metadata"
# the reader's header and metadata properties call the sniffer
print('Header instance (0-based indexing)\n', reader.header)
print('---')
print('Metadata instance\n', reader.metadata())
```

``` python tags=['hide-input']
print('Header instance (0-based indexing)\n', reader.header)
print('---')
print('Metadata instance\n', reader.metadata())
```

``` py title="Type Inference"
# the types are not a reader property but can be requested from the sniffer
# consistent is a `bool` indicating if types are consistent across sample rows
types, consistent = reader.sniffer.types()
print(types)
```

``` python tags=['hide-input']
types, consistent = reader.sniffer.types()
print(types)
```

``` py title="Changing the sniffer"
#print the current sniffer used by the reader
print(reader.sniffer)
```

The `start`,`amount`, & `skips` properties of the sniffer can be changed if the
default values fail to detect the metadata and header.  For details on these
parameters and their default values, ask for help:
 `#!python help(reader.sniffer)`

``` python tags=["hide-input"]
print(reader.sniffer)
```

## **__Data Filtering__**
`Tabbed` provides a powerful mechanism for value-based filtering of rows and
columns. These filters are called **Tabs** in `Tabbed` and support equality,
membership, rich comparison, regular expression, and custom filtering of data.
The `reader.tab` method provides a simple way to construct `Tabs` with keyword
arguments.

### Equality Tabbing ###
``` py title="Equality Tabbing Example", hl_lines="1"
reader.tab(Annotation='exploring', columns=['Number', 'Annotation'])
for row in chain.from_iterable(reader.read()):
    print(row)
```

``` python tags=['hide-input']
reader.tab(Annotation='exploring', columns=['Number', 'Annotation'])
for row in chain.from_iterable(reader.read()):
    print(row)
```

For now ignore the `chain.from_iterable(reader.read())` and focus on the
highlihted line (1) where we tab the rows in the *Annotation* column whose value
equals *exploring* and request the reader to only read the *Number* and
*Annotation* columns. Notice the output row dictionaries consist of rows that
match this Tabbing. For
more details on `Equality` tabbing please see the 
[Equality Tab](reference/tabbing.md#tabbed.tabbing.Equality) 


### Membership Tabbing ###
``` py title="Membership Tabbing Example", hl_lines="1"
reader.tab(Annotation=['exploring', 'resting'], columns=[0, 5])
for row in chain.from_iterable(reader.read()):
    print(row)
```

``` python tags=['hide-input']
reader.tab(Annotation=['exploring', 'resting'], columns=[0, 5])
for row in chain.from_iterable(reader.read()):
    print(row)
```

Focus on the highlihted line (1) where we tab the rows in the *Annotation*
column whose value is in `#!python ['exploring', 'resting']` and request the
reader to only read the *Number* and *Annotation* columns using column indexing.
Notice the output row dictionaries consist of rows that match this Tabbing. For
more details on `Membership` tabbing please see the
[Membership Tab](reference/tabbing.md#tabbed.tabbing.Membership) 


### Comparison Tabbing ###
``` py title="Rich Comparison Tabbing Example", hl_lines="2"
# get all the annotations between 9:38:00 and 9:42:00
reader.tab(Start_Time='> 9/2/2022 9:38:00 and < 9/2/2022 9:42:00', columns=[0, 1])
for row in chain.from_iterable(reader.read()):
    print(row)

```

``` python tags=['hide-input']
# get all the annotations between 9:38:00 and 9:50:00
reader.tab(Start_Time='> 2/9/2022 9:38:00 and < 2/9/2022 9:42:00', columns=[0, 1])
for row in chain.from_iterable(reader.read()):
    print(row)
```

Again, focus on the highlihted line (2) where we tab the rows in the *Start_Time*
column whose value is between `#!python '9:38:00'` and `#!python '9:42:00'` and
request the reader to only read the *Number* and *Start_Time* columns using column indexing.
Notice the output row dictionaries consist of rows that match this Tabbing. For
more details on `Comparison` tabbing please see the
[Comparison Tab](reference/tabbing.md#tabbed.tabbing.Comparison) 


### Regular Expression Tabbing ###
``` py title="Regular Expression Tabbing Example", hl_lines="3"
import re
# get all the annotations that contain start with 'g' or 'r'
reader.tab(Annotation=re.compile(r'^[g|r]'), columns=[0, 1])
for row in chain.from_iterable(reader.read()):
    print(row)
```

``` python tags=['hide-input']
import re
# get all the annotations that contain start with 'g' or 'r'
reader.tab(Annotation=re.compile(r'^[g|r]'), columns=[0, 5])
for row in chain.from_iterable(reader.read()):
    print(row)
```

Focus on the highlihted line (3) where we tab the rows in the *Start_Time*
column whose value is between `#!python '9:38:00'` and `#!python '9:42:00'` and
request the reader to only read the *Number* and *Start_Time* columns using column indexing.
Notice the output row dictionaries consist of rows that match this Tabbing. For
more details on `Regex` tabbing please see the: 
[Regex Tab](reference/tabbing.md#tabbed.tabbing.Regex) 

### Custom Tabbing ###
Tabbed also supports construction of `Calling` Tabs that allow you to provide
your own custom logic for row filtering. For details see the
[Calling Tab](reference/tabbing.md#tabbed.tabbing.Calling) in the reference manual.

## **__Reading__** ##
The `Reader.read` method returns an iterator of list of dictionaries
representing chunk number of read, type casted and filtered rows from a file. It
has several important parameters you can use to control the rows that will be
read. These parameters include: `start`, `skips`, `indices`, and `chunksize`.
We'll take a look at these parameters. You can find all parameters of the read
 method [here](reference/reading.md#tabbed.reading.Reader.read).


### Iterative Read ###

``` py title="Reader.read returns an Iterator"
# call read to create the iterator
gen = reader.read(chunksize=5)
#print the first chunk and its size
print(f'Chunk 0 contains {len(next(chunk_iter))} row dictionaries')
```

``` python tags=['hide-input']
reader.tab()
chunk_iter = reader.read(chunksize=5)
print(f'Chunk 0 contains {len(next(chunk_iter))} row dictionaries')
```

This feature allows Tabbed to stream very large text files. Lets print the
cumulative data rows read during iteration.

``` py title="Iterative Reading"
rows_read = 0 # a counter of the rows we've read
for idx, chunk in enumerate(reader.read(chunksize=5)):
    rows_read += len(chunk)
    print(f'Chunk number= {idx}, rows read = {rows_read}')
```
    
``` python tags=['hide-input']
rows_read = 0
for idx, chunk in enumerate(reader.read(chunksize=5)):
    rows_read += len(chunk)
    print(f'Chunk number= {idx}, rows read = {rows_read}')
```

For large files, you will want to set the chunksize much larger, the default is
200,000 rows per chunk. `Reader.read` always returns an iterator. If you need an
in-memory list just use `itertools.chain.from_iterable` like so

``` py title="As in-memory list"
data = list(chain.from_iterable(reader.read(chunksize=5)))
# print first 10 lines of data
print(*data[:10], sep='\n')
```

``` python tags=['hide-input']
data = list(chain.from_iterable(reader.read(chunksize=5)))
print(*data[:10], sep='\n')
```

### Start of Read ###

If you would like to start reading at a location other than the detected data
start location you can give a start relative to the file start.

``` py title="Reading Start"
# start reading at line 10 (0-based index)
gen = reader.read(start=10, chunksize=5)
print(f'{next(gen)}')
```

``` python tags=['hide-input']
gen = reader.read(start=10, chunksize=5)
print(f'{next(gen)}')
```

### Skipping Read ###

Skipping lines during reading can help you handle problematic rows of
a file. You can pass a list of line integers or a range instance of lines to
skip during reading.

### Partial Read ###


