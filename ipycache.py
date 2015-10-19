# -*- coding: utf-8 -*-
"""Defines a %%cache cell magic in the notebook to persistent-cache results of 
long-lasting computations.
"""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

# Stdlib
import inspect, os, sys, textwrap, re

# Our own
from IPython.config.configurable import Configurable
from IPython.core import magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.utils.traitlets import Unicode
from IPython.utils.io import CapturedIO, capture_output
from IPython.display import clear_output
import hashlib


#------------------------------------------------------------------------------
# Six utility functions for Python 2/3 compatibility
#------------------------------------------------------------------------------
# Author: "Benjamin Peterson <benjamin@python.org>"
    
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    import pickle, builtins
    from io import StringIO
    _iteritems = "items"
    
    exec_ = getattr(builtins, "exec")
else:
    import cPickle as pickle
    from StringIO import StringIO        
    _iteritems = "iteritems"

    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")
    
def iteritems(d, **kw):
    """Return an iterator over the (key, value) pairs of a dictionary."""
    return iter(getattr(d, _iteritems)(**kw))

#------------------------------------------------------------------------------
# cloudpickle 
#------------------------------------------------------------------------------

try:
   import cloudpickle
   dump = cloudpickle.dump
except ImportError:
   dump = pickle.dump

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def conditional_eval(var, variables):
    """
    Evaluates the variable string if it starts with $.
    If the variable string contains one or several {code} statements, the code
    is executed and the result stringified (wrapped in str()) into the rest of
    the string.
    """
    if var[0] == '$':
        return variables.get(var[1:], var)
    def evalfun(x):
        code=x.group(0)[1:-1]
        return str(eval(code, variables))
    return re.sub(r'{.*?}', evalfun, var, flags=re.DOTALL)

def clean_var(var):
    """Clean variable name, removing accidental commas, etc."""
    return var.strip().replace(',', '')

def clean_vars(vars):
    """Clean variable names, removing accidental commas, etc."""
    return sorted(map(clean_var, vars))

def do_save(path, force=False, read=False):
    """Return True or False whether the variables need to be saved or not."""
    if force and read:
        raise ValueError(("The 'force' and 'read' options are "
                          "mutually exclusive."))
         
    # Execute the cell and save the variables.
    return force or (not read and not os.path.exists(path))
    
def load_vars(path, vars):
    """Load variables from a pickle file.
    
    Arguments:
    
      * path: the path to the pickle file.
      * vars: a list of variable names.
    
    Returns:
    
      * cache: a dictionary {var_name: var_value}.
    
    """
    with open(path, 'rb') as f:
        # Load the variables from the cache.
        try:
            cache = pickle.load(f)
        except EOFError as e:
            cache={}
            #raise IOError(str(e))
        
        # Check that all requested variables could be loaded successfully
        # from the cache.
        missing_vars = sorted(set(vars) - set(cache.keys()))
        if missing_vars:
            raise ValueError(("The following variables could not be loaded "
                "from the cache: {0:s}").format(
                ', '.join(["'{0:s}'".format(var) for var in missing_vars])))
        additional_vars = sorted(set(cache.keys()) - set(vars))
        for hidden_variable in '_captured_io', '_cell_md5':
            try:
                additional_vars.remove(hidden_variable)
            except ValueError:
                pass
        if additional_vars:
            raise ValueError("The following variables were present in the cache, "
                    "but removed from the storage request: {0:s}".format(
                ', '.join(["'{0:s}'".format(var) for var in additional_vars])))
        
        return cache

def save_vars(path, vars_d):
    """Save variables into a pickle file.
    
    Arguments:
    
      * path: the path to the pickle file.
      * vars_d: a dictionary {var_name: var_value}.
    
    """
    with open(path, 'wb') as f:
        dump(vars_d, f)
    
    
#------------------------------------------------------------------------------
# CapturedIO
#------------------------------------------------------------------------------
def save_captured_io(io):
    return dict(
            stdout=StringIO(io._stdout.getvalue()),
            stderr=StringIO(io._stderr.getvalue()),
            outputs=getattr(io, '_outputs', []), # Only IPython master has this
        )
        
def load_captured_io(captured_io):
    try:
        return CapturedIO(captured_io.get('stdout', None),
                          captured_io.get('stderr', None),
                          outputs=captured_io.get('outputs', []),
                          )
    except TypeError:
        return CapturedIO(captured_io.get('stdout', None),
                          captured_io.get('stderr', None),
                          )
                            
class myStringIO(StringIO):
    """class to simultaneously capture and output"""
    def __init__(self, out=None, buf=""):
        self._out=out
        StringIO.__init__(self,buf)
    def write(self,s):
        self._out.write(s)
        StringIO.write(self,s)

import IPython.utils.io
class capture_output_and_print(object):
    """
    Taken from IPython.utils.io and modified to use myStringIO.
    context manager for capturing stdout/err
    """
    stdout = True
    stderr = True
    display = True
    
    def __init__(self, stdout=True, stderr=True, display=True):
        self.stdout = stdout
        self.stderr = stderr
        self.display = display
        self.shell = None
    
    def __enter__(self):
        from IPython.core.getipython import get_ipython
        from IPython.core.displaypub import CapturingDisplayPublisher
        
        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr
        
        if self.display:
            self.shell = get_ipython()
            if self.shell is None:
                self.save_display_pub = None
                self.display = False
        
        stdout = stderr = outputs = None
        if self.stdout:
            #stdout = sys.stdout = StringIO()
            stdout = sys.stdout = myStringIO(out=IPython.utils.io.stdout)
        if self.stderr:
            #stderr = sys.stderr = StringIO()
            stderr = sys.stderr = myStringIO(out=self.sys_stderr)            
        if self.display:
            self.save_display_pub = self.shell.display_pub
            self.shell.display_pub = CapturingDisplayPublisher()
            outputs = self.shell.display_pub.outputs

        return CapturedIO(stdout, stderr, outputs)
    
    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr
        if self.display and self.shell:
            self.shell.display_pub = self.save_display_pub
            
#-----------------------------------------------------------------------------
# %%cache Magics
#------------------------------------------------------------------------------
def cache(cell, path, vars=[],
          # HACK: this function implementing the magic's logic is testable
          # without IPython, by giving mock functions here instead of IPython
          # methods.
          ip_user_ns={}, ip_run_cell=None, ip_push=None, ip_clear_output=lambda : None,
          force=False, read=False, verbose=True):
    
    if not path:
        raise ValueError("The path needs to be specified as a first argument.")
    
    path = os.path.abspath(path)
    cell_md5 = hashlib.md5(cell.encode()).hexdigest()
        
    if do_save(path, force=force, read=read):
        # Capture the outputs of the cell.
        with capture_output_and_print() as io:
            try:
                ip_run_cell(cell)
            except:
                # Display input/output.
                io()
                return
        # Create the cache from the namespace.
        try:
            cached = {var: ip_user_ns[var] for var in vars}
        except KeyError:
            vars_missing = set(vars) - set(ip_user_ns.keys())
            vars_missing_str = ', '.join(["'{0:s}'".format(_) 
                for _ in vars_missing])
            raise ValueError(("Variable(s) {0:s} could not be found in the "
                              "interactive namespace").format(vars_missing_str))
        # Save the outputs in the cache.
        cached['_captured_io'] = save_captured_io(io)
        cached['_cell_md5'] = cell_md5
        # Save the cache in the pickle file.
        save_vars(path, cached)
        ip_clear_output() # clear away the temporary output and replace with the saved output (ideal?)
        if verbose:
            print("[Saved variables '{0:s}' to file '{1:s}'.]".format(
                ', '.join(vars), path))
        
    # If the cache file exists, and no --force mode, load the requested 
    # variables from the specified file into the interactive namespace.
    else:
        # Load the variables from cache in inject them in the namespace.
        force_recalc = False
        try:
            cached = load_vars(path, vars)
        except ValueError as e:
            if 'The following variables' in str(e):
                if read:
                    raise
                force_recalc = True
            else:
                raise
            cached = {}
        if not '_cell_md5' in cached or cell_md5 != cached['_cell_md5']:
            force_recalc = True
        if force_recalc and not read:
            return cache(cell, path, vars, ip_user_ns, ip_run_cell, ip_push, ip_clear_output, True, read, verbose)
        # Handle the outputs separately.
        io = load_captured_io(cached.get('_captured_io', {}))
        # Push the remaining variables in the namespace.
        ip_push(cached)
        if verbose:
            print(("[Skipped the cell's code and loaded variables {0:s} "
                   "from file '{1:s}'.]").format(', '.join(vars), path))

    # Display the outputs, whether they come from the cell's execution
    # or the pickle file.
    io() # output is only printed when loading file    

        
    
@magics_class
class CacheMagics(Magics, Configurable):
    """Variable caching.

    Provides the %cache magic."""
    
    cachedir = Unicode('', config=True)
    
    def __init__(self, shell=None):
        Magics.__init__(self, shell)
        Configurable.__init__(self, config=shell.config)
     
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
        '-s', '--silent', action='store_true', default=False,
        help="Do not display information when loading/saving variables."
    )
    @magic_arguments.argument(
        '-d', '--cachedir',
        help="Cache directory as an absolute or relative path."
    )
    @magic_arguments.argument(
        '-f', '--force', action='store_true', default=False,
        help="Force the cell's execution and save the variables."
    )
    @magic_arguments.argument(
        '-r', '--read', action='store_true', default=False,
        help=("Always read from the file and prevent the cell's execution, "
              "raising an error if the file does not exist.")
    )
    @cell_magic
    def cache(self, line, cell):
        """Cache user variables in a file, and skip the cell if the cached
        variables exist.
        
        Usage:
        
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
        vars = clean_vars(args.vars)
        path = conditional_eval(args.to[0], ip.user_ns)
        cachedir_from_path = os.path.split(path)[0]
        # The cachedir can be specified with --cachedir or inferred from the
        # path or in ipython_config.py
        cachedir = args.cachedir or cachedir_from_path or self.cachedir
        # If path is relative, use the user-specified cache cachedir.
        if not os.path.isabs(path) and cachedir:
            # Try to create the cachedir if it does not already exist.
            if not os.path.exists(cachedir):
                try:
                    os.mkdir(cachedir)
                    print("[Created cachedir '{0:s}'.]".format(cachedir))
                except:
                    pass
            path = os.path.join(cachedir, path)
        cache(cell, path, vars=vars, 
              force=args.force, verbose=not args.silent, read=args.read,
              # IPython methods
              ip_user_ns=ip.user_ns, 
              ip_run_cell=ip.run_cell,
              ip_push=ip.push,
              ip_clear_output=clear_output
              )

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(CacheMagics)
    
