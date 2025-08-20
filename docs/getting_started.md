---
execute: true
---

## **__Introduction__**
This guide walks you through reading a text file that contains metadata,
a header row and mixed data types with `Tabbed`.

<div class="grid cards" markdown>
- :material-numeric-1-box-outline: [Sample File](#sample-file)
- :material-numeric-2-box-outline: [Tabbed Wish List](#tabbed-wish-list)
- :material-numeric-3-box-outline: [The Tabbed Reader](#the-tabbed-reader)
- :material-numeric-4-box-outline: [Data Filtering](#data-filtering)
- :material-numeric-5-box-outline: [Reading](#reading)
- :material-numeric-6-box-outline: [When Something Goes Wrong](#when-something-goes-wrong)
</div>

[comment]: # (pymdownx block which allows line nums but does not execute)

```py title="Imports" linenums="1"
import os
import tempfile
import random
from datetime import datetime, timedelta

from tabbed import samples
from tabbed.reading import Reader
```

[comment]: # (an mkdocs-execute block does not allow line nums but executes)

```python tags=['hide-input']
import os
import tempfile
import random
from datetime import datetime, timedelta
from itertools import chain

from tabbed import samples
from tabbed.reading import Reader
```

## **__Sample File__**
Tabbed comes preloaded with a sample text file called *annotations.txt*. Below we
open this file to see what it looks like and **develop a list of operations we
would like Tabbed to handle automatically for us.**

``` py title="Preview Sample Data"
fp = samples.paths.annotations
with open(fp, 'r') as infile:
    for line in infile:
        print(line, end='')
```

??? example "View Sample Data"
``` python tags=['hide-input']
fp = samples.paths.annotations
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

    :material-numeric-1-box: __Header Detection__

    This sample file contains a **metadata section** prior to the **header** on
    line 7. Metadata can be unstructured like a paragraph or structured into
    columns separated by a delimiter. We want `Tabbed` to automatically detect
    the Metadata section and Header line of *any* file.

=== "Type Inference"

    :material-numeric-2-box: __Type Inference__
    
    The string cells in the sample file are encoding 4 different data types;
    *integers, datetimes, floats and strings.* We want `Tabbed` to perform
     **Type inference**.

=== "Data Filtering"
    
    :material-numeric-3-box: __Data Filtering__

    We want `Tabbed` to support simple value based row and column filtering.
    For example, in this file we might want only rows at which the `Start Time`
    column is less than `#!python datetime(2022, 2, 9, 9, 37, 13)` or where the
    `Annotation` column has a string value of `#!python 'exploring'` or both
    conditions.

=== "Partial & Iterative Reading"

    :material-numeric-4-box: __Partial & Iterative Reading__

    Text files can be large. `Tabbed` should support partial and iterative
    reading.

=== "Flexibility"

    :material-numeric-5-box: __Flexibility__

    Tabbed should be flexible. It should be able to `start` reading at any file
    position, `skip` reading of 'bad' rows, and allow users to choose how much
     memory to consume during iterative reading of large files. 


## **__The Tabbed Reader__**
Tabbed's `Reader` reads rows of an infile to dictionaries just like
Python's built-in `csv.DictReader`. However, Tabbed's `Reader` embeds
a sophisticated file `Sniffer` that can detect metadata, header & data sections
of a file automatically (for details see
[Sniffer](reference/sniffing/#sniffing.md)). The detected metadata, header and
datatypes are available to the reader as properties. In this section, we will
**build a reader** and see how to access the file's **dialect**, **metadata**,
**header**, and **inferred datatypes**.

[comment]: # (Building a reader)

``` py title="Building a Reader"
fp = samples.paths.annotations
infile = open(fp, 'r')
# like Python's csv.DictReader, we pass an open file instance
reader = Reader(infile)
```

``` python tags=['hide-input']
fp = samples.paths.annotations
infile = open(fp, 'r')
reader = Reader(infile)
```

[comment]: # (Dialect)

``` py title="Accessing Dialect"
fp = samples.paths.annotations
infile = open(fp, 'r')
# like Python's csv.DictReader, we pass an open file instance
reader = Reader(infile)
print(reader.sniffer.dialect)
```

!!! example "Dialect"
``` python tags=['hide-input']
fp = samples.paths.annotations
infile = open(fp, 'r')
reader = Reader(infile)
print(reader.sniffer.dialect)
```

The output dialect is a SimpleDialect instance of the 
[clevercsv](https://clevercsv.readthedocs.io/en/latest/) package.

[comment]: # (Metadata and Header)

``` py title="Metadata & Header Detection"
# the reader's header and metadata properties call the sniffer
print(reader.header)
print('---')
print(reader.metadata())
```

!!! example "Metadata and Header Detection"
``` python tags=['hide-input']
print(reader.header)
print('***')
print(reader.metadata())
```

The Header was detected on line 6 and has 6 column names. The metadata string
spans from line 0 upto line 6. The embedded `Sniffer` instance samples the file
when the reader is created.

[comment]: # (Type Inference)

``` py title="Type Inference"
# request the sniffed types by polling the last 10 rows of the sniffed sample
# consistent is a `bool` indicating if types are consistent across sample rows
types, consistent = reader.sniffer.types(poll=10)
print(types)
```

!!! example "Type Inference"
``` python tags=['hide-input']
types, consistent = reader.sniffer.types(poll=10)
s = str(types)
# escape all special characters
s = f'`{s}`'
print(s)
```

Our deep testing on randomly generated text files indicates that Tabbed's
`Reader` will detect dialect, metadata, header, and types correctly in most
cases. Should you encounter a problem, you can change the sample the Sniffer
uses to measure these properties. The `Sniffer`'s `start`,`amount`, & `skips`
alter the sniffing sample. You can also change what sample rows are used for
type polling via the `poll` and `exclude` arguments of the Reader initializer.
All these arguments can help in the auto-detection of the header and metadata
sections of a text file.  For help understanding these parameters type `#!python
help(reader.sniffer)` or see [Sniffer](reference/sniffing/#sniffing.md). Below,
we show the sniffer and it's default parameters used in this example.

[comment]: # (Sniffer)

``` py title="Default Sniffer"
#print the current sniffer used by the reader
print(reader.sniffer)
```

``` python tags=["hide-input"]
print(reader.sniffer)
```

```py title="Default Reader"
#print the poll and exlude default arguments.
print(reader.poll, reader.exclude)
```

``` python tags=["hide-input"]
print(reader.poll, reader.exclude)
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

Again, focus on the highlihted line (2) where we tab the rows in the
*Start_Time* column whose value is between `#!python '9:38:00'` and `#!python
'9:42:00'` and request the reader to only read the *Number* and *Start_Time*
columns using column indexing.  Notice the output row dictionaries consist of
rows that match this Tabbing. For more details on `Comparison` tabbing please
see the [Comparison Tab](reference/tabbing.md#tabbed.tabbing.Comparison) 


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
request the reader to only read the *Number* and *Start_Time* columns using
column indexing.  Notice the output row dictionaries consist of rows that match
this Tabbing. For more details on `Regex` tabbing please see the: [Regex
Tab](reference/tabbing.md#tabbed.tabbing.Regex) 

### Custom Tabbing ###
Tabbed also supports construction of `Calling` Tabs that allow you to provide
your own custom logic for row filtering. For details see the [Calling
Tab](reference/tabbing.md#tabbed.tabbing.Calling) in the reference manual.


## **__Reading__** ##

The `Reader.read` method returns an iterator of lists. Each *yielded* list
contains row dictionaries from the data section. The values in each `dict` are
the type casted and tab filtered rows. The `chunksize` parameter of the `read`
method determines how many row dictionaries to yield per iteration. Let's take
a look at the `read` method with our sample file.  

[comment]: # (read returns an Iterator)

``` py title="Return Type"
# for ease of reading just get the Number & Annotation columns
reader.tab(columns=['Number', 'Annotation'])
# calling read creates an iterator
gen = reader.read(chunksize=5)
print(type(gen))
```

!!! example "Return Type"
``` python tags=['hide-input']
reader.tab(columns=['Number', 'Annotation'])
# calling read creates an iterator
gen = reader.read(chunksize=5)
s = f'`{type(gen)}`'
print(s)
```

[comment]: # (chunksize)

```py title="Chunksize"
for idx, chunk in enumerate(reader.read(chunksize=2)):
    print(f'chunk {idx}: {chunk}')
```

??? example "chunksize"
```python tags=['hide-input']
for idx, chunk in enumerate(reader.read(chunksize=2)):
    print(f'**chunk {idx}:** `{chunk}`', end='<br>')
```

Each `yield` of the read iterator gave us 2 rows from the data section. You can
set the `chunksize` to any `#!python int` value. The default is 200,000 rows per
yield. Read has several parameters for controlling what rows will be yielded.
These include;  `start`, `skips` and `indices`. Details on these parameters can
be found using `#!python help(Reader.read)` or
[read's](reference/reading.md#tabbed.reading.Reader.read) documentation. 

The `read` method always returns an iterator but for small files you may want to
read the file in completely. This is simple using python's `itertools` module.
Below is a recipe for converting read's iterator to an in-memory list. 

``` py title="As in-memory list"
from itertools import chain
data = list(chain.from_iterable(reader.read(chunksize=2)))
print(*data, sep='\n')
```

??? example "Reading to an in-memory list"
``` python tags=['hide-input']
data = chain.from_iterable(reader.read(chunksize=5))
for row in data:
    print(f'`{row}`', end='<br>')
```

## When Something Goes Wrong ##

In most cases, we think `Tabbed` will work *out-of-the-box* on your text files
but the variability in dialects and structures means we can't guarantee it.
`Tabbed` provides several fallbacks to help you read files when something has
gone wrong. Specifically there are two problems you may encounter:

!!! tip "Incorrect Start Row"
    If tab fails to detect the file's structure, the start row for the read will
    be incorrect. You have 2 options to deal with this.
    
    - Adjust the `start`, `amount`, or `skips`attributes of the sniffer or the
      exclude parameter of the header and metadata sniffer methods.  These
      control the sample the sniffer uses to detect the header and metadata if
      they exist. You can use `Reader.peek` to help you determine good values
      for these parameters.
    - Adjust the default `poll` and `exclude` arguments of a Reader instance. In
      particular, the `exclude` argument can be used to ignore missing values
      for better type inference.
    - During Read, set the `start` parameter to force reading to begin at
      a specific row.  This will also require you to manually set the reader's
      header by setting `reader.header` to a list of header string names. This
      method should always work when structure (metadata, header, etc) isn't
      being detected.

!!! tip "Wonky Data Values"
    Tabbed supports reading `#!python ints`, `#!python floats`,
    `#!python complex`, `#!python time`, `#!python date` and `#!python datetime`
    types.  It further assumes that these types are consistent across rows
    within a column in the data section. If Tabbed encounters a type 
    conversion error, it gracefully returns the value as a string type and 
    logs the error to the `Reader.errors` attribute. You can use this log to
    figure out what rows had problems and skip them or change the values using
    your own callable after they have been read by Tabbed.
