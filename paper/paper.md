---
title: "Tabbed: A Python package for reading variably structured text files at
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
bibliography: paper.bib
---

# Summary
Delimiter separated value (DSV) text files are ubiquitous for representing
tabular data. For example, a search of Github.com for comma separated value
files, a subset of the DSV format, returns 75 million matches. They are simple
to create, easy to share and can represent many data formats. Despite their
broad use, variability in the formatting and structure of DSV files has
frustrated their automated parsing for decades. The *clevercsv* package
[@vandenBurg2019] made significant progress on this problem with consistency
measures that accurately detect a file's dialect: delimiter, quote character and
escape character. The structure of a DSV introduces another source of
variability. DSVs may contain a metadata section that offsets the header and
start row. Tabbed uses row length and type consistency measures to automatically
detect metadata, header and data sections of a DSV. Furthermore, Tabbed provides
a value-based conditional reader for reading these irregular DSV files at
scale.

# Statement of need
To the best of our knowledge, no parser of DSV files exist that can locate the
start of the data section irrespective of the presence of metadata and/or
a header. Further, we found no reader of DSV files that can conditionally read
rows from the data section based on a row's type casted values. We here define
a set of desiderata for parsing irregular text files that optionally contain
metadata, header and ragged data rows. To motivate this set, we consider
the DSV shown in Figure 1.

![The first 12 lines of a delimiter separated file named *sample.txt* with
metadata on lines 1-4 and a header on line 7. The metadata contains both
semicolon delimited and undelimited strings. Notice the data section uses
a different delimiter than the metadta and contains mixed data types.
\label{fig: figure1}]( sample_dsv.png){width=900}

### Structural Detection
A header line (line 7 of \autoref{fig: figure1}) marks the boundary between the
metadata and data sections of a file.  Detection of this line is critical for
correct automated parsing. Tabbed can locate a header line using string
inconsistencies or type inconsistencies depending on the data types represented
in the data section of the file.  Importantly, some irregular DSV files do not
have a header. In this case tabbed  generates a header based on the number of
data columns it measures from a sample of the file.

### Type Casting
Strings in the data section of the file shown in \autoref{fig: figure1}
represent mixed types that need to be type casted. Tabbed supports conversion to
`int`, `float`, `complex`, `time`, `date` and `datetime` instances. These
conversions are graceful; they return strings on failure and log the conversion
problem to an error log for post reading introspection. 

### Value-based Filtering
Selectively reading rows from a DSV file based on type casted content is
extremely useful for selecting subsets of the data. For example, in the sample
file of \autoref{fig: figure1}, users may want to only read data rows where the
column named *Annotation* has a string value of *exploring*. Tabbed supports
both column selection and row filtering with equality, membership, rich
comparison, regular expression matching and custom callables. To support an
intuitive interface for creating these filters, tabbed uses simple keyword
arguments passed to a method called `tab' of the Reader class. Below we
illustrate the simplicity of constructing these filters for the sample file
shown in \autoref{fig: figure1}.

```python
from tabbed.reading import Reader

with open('sample.txt', 'r') as infile:
    reader = Reader(infile)
    # Tell the reader to only read these Tabbed rows
    reader.tab(Start_Time ='>=2/09/2022 9:37:00', Annotation = 'exploring')
    result = reader.read()
```

### Iterative Reading
DSV files have no file size limits making it essential that readers support file
streaming. Tabbed's reader returns an iterator whose per-iteration memory
consumption is tuneable. For speed, this feature is implemented using
a first-in-first-out (FIFO) data structure with O(1) time complexity allowing
Tabbed to linearly scale to large files. 

# Comparison

Tablib [@tablib], comma, and pandas are popular alternative packages to Tabbed.

| **Software** | **Structural Detection** | **Casting** | **Value-based Filtering** | **Iterative** |
|:------------:|:------------------------:|:-----------:|:-------------------------:|:-------------:|
|  **tablib**  |           -              |    +        |       equality only       |     -     |
|   **comma**  |           -              |   limited   |           -               |     -     |
|  **pandas**  |           -              |    +        |        columns only       |     +     |
|  **tabbed**  |           +              |    +        |           +               |     +     |

Table: Comparison of features for four common open-source software packages for
reading DSV files. Plus (+) and minus (-) indicates package support or lack of support respectively.


![Comparison of number of cells type casted per second between Tabbed and Pandas
for DSVs composed of floats (left) or mixed types (right). The conversion engine
for Pandas was chosen to be "python" for a fair comparison with Tabbed's python
implementation. Black circles and error bars are the mean and standard deviation
across 30 trials.\label{fig: speeds}](read_speeds.png)

# Conclusion

# Acknowlegements
We thank Brad Sheppard for constructive discussions about testing Tabbed and
Claudia Tischler for her thoughtful reading of the manuscript.

We are grateful for the support of the Ting Tsung and Wei Fong Chao Foundation
and the Jan and Dan Duncan Neurological Research Institute at Texas Children's
that generously supports Tabbed.

# References
