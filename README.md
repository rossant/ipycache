# ipycache

[![Build Status][github-ci-badge]][github-ci-url]
[![Latest PyPI version][pypi-badge]][pypi-url]

[github-ci-badge]: https://github.com/rossant/ipycache/actions/workflows/master.yml/badge.svg
[github-ci-url]: https://github.com/rossant/ipycache/actions/workflows/master.yml
[pypi-badge]: https://img.shields.io/pypi/v/ipycache.svg
[pypi-url]: https://pypi.org/project/ipycache/

Defines a `%%cache` cell magic in the IPython notebook to cache results and
outputs of long-lasting computations in a persistent pickle file. Useful when
some computations in a notebook are long and you want to easily save the results
in a file.

## Examples

* [Sample usage](examples/example.ipynb)
* [Example with output](examples/example_outputs.ipynb)
* [Simultaneously printing and capturing output](examples/capture_output.ipynb)

## Installation

Latest PyPI release:

    pip install ipycache

Latest development version:

    pip install git+https://github.com/rossant/ipycache.git

## Usage
  
In IPython, execute the following:

    %load_ext ipycache

Then, create a cell with:

    %%cache mycache.pkl var1 var2
    var1 = 1
    var2 = 2

When you execute this cell the first time, the code is executed, and the
variables `var1` and `var2` are saved in `mycache.pkl` in the current directory
along with the outputs. Rich display outputs are only saved if you use the
development version of IPython. When you execute this cell again, the code is
skipped, the variables are loaded from the file and injected into the namespace,
and the outputs are restored in the notebook.

Alternatively use `$file_name` instead of `mycache.pkl`, where `file_name` is a
variable holding the path to the file used for caching.

Use the `--force` or `-f` option to force the cell's execution and overwrite the
file.

Use the `--read` or `-r` option to prevent the cell's execution and always load
the variables from the cache. An exception is raised if the file does not exist.

Use the `--cachedir` or `-d` option to specify the cache directory. You can
specify a default directory in the IPython configuration file in your profile
(typically in `~\.ipython\profile_default\ipython_config.py`) by adding the
following line:

    c.CacheMagics.cachedir = "/path/to/mycache"

If both a default cache directory and the `--cachedir` option are given, the
latter is used.
