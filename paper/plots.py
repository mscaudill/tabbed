import csv
import datetime
from itertools import batched
from itertools import chain
import pathlib
import random
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import tabbed

ROWS=100e3
COLS=10

def write_floatcsv(path=None, name='floatcsv.txt', seed=0, rows=ROWS, cols=COLS):
    """Writes a text file of stringed float values to path.

    Args:
        path:
            A string or path instance to a directory where this float csv will
            be written to.
        name:
            The name of the file to write.
        seed:
            A seed for Python's random number generator.
        columns:
            The number of columns to write.
        rows:
            The number of data rows to write.
    """

    # header & data generation
    header = [f'Column_{i}' for i in range(cols)]
    rgen = random.Random()
    rgen.seed(seed)
    data = [rgen.random() for _ in range(int(rows * cols))]
    data = batched(data, cols)
    # create path and write
    path = pathlib.Path.cwd() if not path else Path(path)
    fp = path / name
    with open(fp, 'w+') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        for idx, row in enumerate(data):
            print(f'Writing float data: {idx/rows * 100:.0f}% complete',
                  end='\r', flush=True)
            writer.writerow(row)

    print('write complete')


def write_mixedcsv(path=None, name='mixedcsv.txt', seed=0, rows=ROWS, cols=COLS):
    """Writes a text file to path containing floats and datetimes.

    Args:
        path:
            A string or path instance to a directory where this mixed csv will
            be written to.
        name:
            The name of the file to write.
        seed:
            A seed for Python's random number generator.
        columns:
            The number of columns to write.
        rows:
            The number of data rows to write.
    """

    # header & data generation
    header = [f'Column_{i}' for i in range(cols)]
    rgen = random.Random()
    rgen.seed(seed)
    data = [rgen.random() for _ in range(int(rows * cols))]
    data = [list(tup) for tup in batched(data, cols)]

    # set the second column to be a date
    for row in data:
        row[2] = '9/22/2023'

    # create path and write
    path = pathlib.Path.cwd() if not path else Path(path)
    fp = path / name
    with open(fp, 'w+') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        for idx, row in enumerate(data):
            print(f'Writing mixed data: {idx/rows * 100:.0f}% complete',
                  end='\r', flush=True)
            writer.writerow(row)

    print('write complete')


def time_tabbed(fp, trials):
    """Computes the number of cells per second tabbed reads for each trial in
    trials.

    Args:
        fp:
            Path to a text file to read and parse.
        trials:
            Number of times to read the file

    Returns:
        A list of speeds in cells per sec units one per trial in trials.
    """

    speeds = []
    for trial in range(trials):
        infile = open(fp, 'r')
        reader = tabbed.reading.Reader(infile)
        gen = reader.read(chunksize=int(10e3))
        t0 = time.perf_counter()
        data = list(chain.from_iterable(gen))
        elapsed = time.perf_counter() - t0
        speeds.append((ROWS * COLS)/elapsed)

        infile.close()

    return speeds


def time_pandas(fp, trials, **kwargs):
    """Computes the number of cells per second that pandas reads for each trial
    in trials.

    Args:
        fp:
            Path to a text file to read and parse.
        trials:
            Number of times to read the file

    Returns:
        A list of speeds in cells per sec units one per trial in trials.
    """

    speeds = []
    for trial in range(trials):
        infile = open(fp, 'r')
        reader = pd.read_csv(
                infile,
                chunksize=int(10e3),
                engine='python',
                **kwargs,
        )
        t0 = time.perf_counter()
        data = [chunk.to_dict(orient='records') for chunk in reader]
        data = list(chain.from_iterable(data))
        elapsed = time.perf_counter() - t0
        speeds.append((ROWS * COLS) / elapsed)
        infile.close()

    return speeds


def time_filtering(fp, trials, maxtab=8):
    """Compares the time to read cells with and without Tab filters."""


    ntabs = range(maxtab+1)
    speeds = {tab: [] for tab in ntabs}
    infile = open(fp, 'r')
    reader = tabbed.reading.Reader(infile)
    for ntabbed in ntabs:
        print(f'Computing speeds with {ntabbed} tabs')
        tabs = [tabbed.tabbing.Comparison(f'Column_{i}', '> 0.1') for i in
                range(ntabbed)]
        reader.tabulator = tabbed.tabbing.Tabulator(reader.header, tabs=tabs)

        for trial in range(trials):
            gen = reader.read(chunksize=int(10e3))
            t0 = time.perf_counter()
            data = list(chain.from_iterable(gen))
            elapsed = time.perf_counter() - t0
            speeds[ntabbed].append((ROWS * COLS)/elapsed)

    infile.close()

    return speeds


def scatterplot_speed_compare(data, jitter, ax=None):
    """Scatterplot values in data dictionary using keys as labels.

    Args:
        data:
            Dataset containing named arrays to scatterplot.
        jitter:
            The maximum x-displacement per sequence in data's values

    Returns:
        A matplotlib axes instance.
    """

    if ax is None:
        fig, ax = plt.subplots()

    groups = list(data.keys())
    for idx, values in enumerate(data.values(), 1):
        locs = np.random.uniform(-jitter, jitter, len(values)) + idx
        if idx % 2 == 1:
            color = 'tab:orange'
        else:
            color = 'tab:gray'
        ax.scatter(locs, values, color=color, s=150)
        ax.scatter(idx, np.mean(values), c='k', s=150)
        ax.errorbar(idx, np.mean(values), yerr=np.std(values), color='k')
        ax.spines[['right', 'top']].set_visible(False)
        ax.set_xticks([1.5, 3.5], labels=['Float Type', 'Mixed Type'])
        ax.set_yticks(list(np.arange(4e5, 15e5, 2e5)))

    return ax


def scatterplot_tab_compare(data, jitter, ax=None):
    """Scatterplot values in data dictionary using keys as labels.

    Args:
        data:
            Dataset containing named arrays to scatterplot.
        jitter:
            The maximum x-displacement per sequence in data's values

    Returns:
        A matplotlib axes instance.
    """

    if ax is None:
        fig, ax = plt.subplots()

    groups = list(data.keys())
    for idx, values in enumerate(data.values()):
        locs = np.random.uniform(-jitter, jitter, len(values)) + idx
        ax.scatter(locs, values, color='tab:orange', s=150)
        ax.scatter(idx, np.mean(values), c='k', s=150)
        ax.errorbar(idx, np.mean(values), yerr=np.std(values), color='k')
        ax.spines[['right', 'top']].set_visible(False)

    return ax


def software_comparison(trials):
    """Plots the speed of Tabbed vs Pandas on numeric and mixed data type
    files.

    Args:
        trials:
            The integer number of trials to test speeds.
    """

    results = {}
    results['tabbed_numeric'] = time_tabbed('floatcsv.txt', trials=trials)
    results['pandas_numeric'] = time_pandas('floatcsv.txt', trials=trials)

    results['tabbed_mixed'] = time_tabbed('mixedcsv.txt', trials=trials)
    results['pandas_mixed'] = time_pandas('mixedcsv.txt', trials=trials,
                                          parse_dates=[2])

    scatterplot_speed_compare(results, jitter=0.1)
    plt.show()


def filtering_comparison(trials, maxtabs=8):
    """Plots the speeds in millions of cells per sec as a function of the number
    of comparison tabs applied during reading.

    Args:
        trials:
            The number of times to compute the speeds.
        maxtabs:
            The max value of the tabs to apply. This will range from 0 to
            maxtabs inclusively.
    """

    speeds = time_filtering('floatcsv.txt', trials, maxtabs)
    scatterplot_tab_compare(speeds, jitter=0.1)
    plt.show()

if __name__ == '__main__':

    #write_floatcsv()
    #write_mixedcsv()

    #tabbed_speeds = time_tabbed('mixedcsv.txt', trials=5)
    #panda_speeds, pdata = time_pandas('mixedcsv.txt')

    #software_comparison(30)
    filtering_comparison(30)
