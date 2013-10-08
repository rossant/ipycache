%%cache cell magic
==================

Defines a %%cache cell magic in the IPython notebook to cache results of long-lasting computations in a persistent pickle file. Useful when some computations in a notebook are long and you want to easily save the results in a file.

Example
-------

  * [Example notebook](http://nbviewer.ipython.org/urls/raw.github.com/rossant/ipycache/master/test.ipynb).


Installation
------------

  * `pip install ipycache`
  
  
Usage
-----
  
  * In IPython:
  
        %load_ext ipycache
  
  * Then, create a cell with:
  
        %%cache var1 var2 --to=mycache.pkl
        var1 = 1
        var2 = 2

  * When you execute this cell the first time, the code is executed, and the variables `var1` and `var2` are saved in `mycache.pkl` in the current directory. When you execute this cell again, the code is skipped and the variables are loaded from the file. Use the `--force` or `-f` option to force the cell's execution and overwrite the file.



