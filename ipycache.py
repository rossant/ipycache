# -*- coding: utf-8 -*-
"""
Defines a %%cache cell magic in the notebook to persistent-cache results of 
long-lasting computations.
"""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

# Stdlib
import inspect, os, sys, textwrap, cPickle

# Our own
from IPython.config.configurable import Configurable
from IPython.core import magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic


#------------------------------------------------------------------------------
# Six utility functions for Python 2/3 compatibility
#------------------------------------------------------------------------------
# Author: "Benjamin Peterson <benjamin@python.org>"
    
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    _iteritems = "items"
else:
    _iteritems = "iteritems"
    
def iteritems(d, **kw):
    """Return an iterator over the (key, value) pairs of a dictionary."""
    return iter(getattr(d, _iteritems)(**kw))


#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def clean_var(var):
    """Clean variable name, removing accidental commas, etc."""
    return var.strip().replace(',', '')

def clean_vars(vars):
    """Clean variable names, removing accidental commas, etc."""
    return sorted(map(clean_var, vars))

def load_vars(path, vars):
    """Load variables from a cPickle file.
    
    Arguments:
    
      * path: the path to the pickle file.
      * vars: a list of variable names.
    
    Returns:
    
      * cache: a dictionary {var_name: var_value}.
    
    """
    with open(path, 'rb') as f:
        # Load the variables from the cache.
        cache = cPickle.load(f)
        
        # Check that all requested variables could be loaded successfully
        # from the cache.
        missing_vars = list(set(vars) - set(cache.keys()))
        if missing_vars:
            raise ValueError(("The following variables could not be loaded "
                "from the cache: {0:s}").format(', '.join(missing_vars)))
        
        return cache

def save_vars(path, vars_d):
    """Save variables into a cPickle file.
    
    Arguments:
    
      * path: the path to the pickle file.
      * vars_d: a dictionary {var_name: var_value}.
    
    """
    with open(path, 'wb') as f:
        cPickle.dump(vars_d, f)
    

#------------------------------------------------------------------------------
# Magics class
#------------------------------------------------------------------------------
@magics_class
class CacheMagics(Magics, Configurable):
    """Variable caching.

    Provides the %cache magic."""
    
    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        'to', nargs=1, type=str,
        help="Path to the file containing the cached variables."
    )
    @magic_arguments.argument(
        'vars', nargs='*', type=str,
        help="Variables to save."
    )
    @magic_arguments.argument(
        '-v', '--verbose', action='store_true', default=True,
        help="Display information when loading/saving variables."
    )
    @magic_arguments.argument(
        '-f', '--force', action='store_true', default=False,
        help="Force the cell's execution and save the variables."
    )
    @cell_magic
    def cache(self, line, cell):
        """Cache user variables in a file, and skip the cell if the cached
        variables exist.
        
        Usage::
        
            %%cache myfile.pkl var1 var2
            # If myfile.pkl doesn't exist, this cell is executed and 
            # var1 and var2 are saved in this file.
            # Otherwise, the cell is skipped and these variables are
            # injected from the file to the interactive namespace.
            var1 = ...
            var2 = ...
        
        """
        ip = self.shell
        args = magic_arguments.parse_argstring(self.cache, line)
        code = cell if cell.endswith('\n') else cell+'\n'
        path = args.to[0]
        verbose = args.verbose
        vars = clean_vars(args.vars)
        
        if not path:
            raise ValueError("The path needs to be specified as a first argument.")
            
        # If the cache file exists, and no --force mode, load the requested 
        # variables from the specified file into the interactive namespace.
        if os.path.exists(path) and not args.force:
            if verbose:
                print(("Skipping the cell's code and loading variables {0:s} "
                       "from file '{1:s}'.").format(', '.join(vars), path))
            # Load the variables from cache in inject them in the namespace.
            ip.push(load_vars(path, vars))
            
        # Otherwise, execute the cell and save the variables.
        else:
            ip.run_cell(cell)
            # Create the cache from the namespace.
            try:
                cache = {var: ip.user_ns[var] for var in vars}
            except KeyError:
                raise ValueError(("Variable '{0:s}' could not be found in the "
                                  "interactive namespace").format(var))
            # Save the cache in the pickle file.
            save_vars(path, cache)
            if verbose:
                print("Saved variables {0:s} to file '{1:s}'.".format(
                    ', '.join(vars), path))

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(CacheMagics)
    
