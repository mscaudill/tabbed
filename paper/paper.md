---
title: "Tabbed: A Python package for parsing variably structured text files at
scale."
tags:
    - Python
    - Data Science
    - File Parsing
    - Text Processing
authors:
  - name: Matthew S. Caudill 
    orcid: 0000-0002-3656-9261 
    affiliation: "1, 2" # (multiple affiliations must be quoted) 
affiliations:
  - name: Department of Neuroscience, Baylor College of Medicine, Houston,
      TX, United States of America
    index: 1
  - name: Jan and Dan Duncan Neurological Research Institute at Texas
      Childrens Hospital, Houston, TX, United States of America 
    index: 2 
date: 7 July 2025

---

# Summary
Delimiter separated value (DSV) text files are ubiquitous for representing
tabular data. For example, a search of Github.com for comma separated value
files, a subset of the DSV format, returns 75 million matches. They are simple
to create, easy to share and can represent many data formats. Despite their
broad use, variability in the formatting and structure of DSV files has
frustrated their automated parsing for decades. The *clevercsv* package
@vandenBurg2019 made significant progress on this problem with consistency
measures that accurately detect a file's dialect: delimiter, quote character and
escape character. The structure of a DSV introduces another source of
variability. DSVs may contain a *metadata* section that offsets the header and
start row. Tabbed uses row length and type consistency measures to automatically
locate metadata, header and data sections of a DSV. Furthermore, Tabbed provides
a value-based conditional reader for reading these irregular DSV files at
scale.

# Statement of need
To the best of our knowledge, no parser of DSV files exist that can locate the
start of the data section irrespective of the presence of metadata and/or
a header. Further, we found no reader of DSV files that can conditionally read
rows from the data section based on a row's type casted values. We here define
a set of desiderata for parsing irregular text files that optionally contain
metadata, header and ragged data rows. To motivate this set we consider
the DSV shown in Figure 1.

![The first 12 lines of '|' delimiter separated file with metadata and header.
Metadata lines 1-3 use a ';' delimiter while line 4 is an undelimited
string.\label{fig: sample}](sample_dsv.png){width=300}

### Structural Detection
The header located on line 7 marks the boundary between the metadata
and data section of the file. Automated detection of this line is critical for
correct parsing of the file. Tabbed auto-locates this line using either type
inconsistencies or string value inconsistencies without user input.

### Type Casting
The strings in the data section of the file represent mixed types that need to
be type casted. Tabbed supports conversion to ints, floats, complex,
time, date and datetime instances. These conversions are graceful in that they
return strings on failures while logging the conversion error.

### Value-based Filtering
Selective reading from DSV files based on cell content is extremely useful for
selecting subsets of the data. Tabbed supports both column selection and row
filtering with equality, membership, rich comparison, regular expression
matching and custom callables. These may be supplied via keyword arguments to
the `tab` method of Tabbed's `Reader` class.

```python
from tabbed.reading import Reader

with open('sample.txt', 'r') as infile:
    reader = Reader(infile)
    # Tell the reader to only read these Tabbed rows
    reader.tab(Start_Time ='>=2/09/2022 9:37:00', Annotation = 'exploring')
    result = reader.read()
```

### Iterative Reading
Given that there is no hard-limit on the size of a DSV file, it is
essential that readers support file streaming. Tabbed's reader returns an
iterator whose per-iteration memory consumption is tuneable. For speed, this
feature is implemented using a first-in-first-out (FIFO) data structure with
O(1) time complexity allowing Tabbed to linearly scale to large files. 

# Comparison
Tablib @tablib, comma @comma, and pandas @pandas are popular alternative packages to Tabbed. 

| **Software** | **Structural Detection** | **Casting** | **Value-based Filtering** | **Iterative** |
|:------------:|:------------------------:|:-----------:|:-------------------------:|:-------------:|
|  **tablib**  |           **-**          |    **+**    |       equality only       |     **-**     |
|   **comma**  |           **-**          |   limited   |           **-**           |     **-**     |
|  **pandas**  |           **-**          |    **+**    |        columns only       |     **+**     |
|  **tabbed**  |           **+**          |    **+**    |           **+**           |     **+**     |

Table: Comparison of features for four common open-source software packages for
reading DSV files. Plus (+) indicates full support, (-) indicates no support.

# Conclusion

# Acknowlegements
We thank Brad Sheppard for constructive discussions about testing Tabbed and
Claudia Tischler for her thoughtful reading of the manuscript.

We are grateful for the support of the Ting Tsung and Wei Fong Chao Foundation
and the Jan and Dan Duncan Neurological Research Institute at Texas Children's
that generously supports Tabbed.

# References
