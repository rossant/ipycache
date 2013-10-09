# -*- coding: utf-8 -*-
"""Tests for ipycache.
"""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import os
from nose.tools import raises, assert_raises
from ipycache import (save_vars, load_vars, clean_var, clean_vars, do_save, 
    cache, exec_)


#------------------------------------------------------------------------------
# Functions tests
#------------------------------------------------------------------------------
def test_clean_var():
    assert clean_var('abc') == 'abc'
    assert clean_var('abc ') == 'abc'
    assert clean_var('abc,') == 'abc'
    assert clean_var(',abc') == 'abc'
    
def test_clean_vars():
    assert clean_vars(['abc', 'abc,']) == ['abc'] * 2

def test_do_save():
    path = 'myvars.pkl'
    
    # File exists.
    open(path, 'wb').close()
    assert_raises(ValueError, do_save, path, force=True, read=True)
    assert do_save(path, force=True, read=False)
    assert not do_save(path, force=False, read=False)
    assert not do_save(path, force=False, read=True)
    os.remove(path)
    
    # File does not exist.
    assert_raises(ValueError, do_save, path, force=True, read=True)
    assert do_save(path, force=True, read=False)
    assert do_save(path, force=False, read=False)
    assert not do_save(path, force=False, read=True)
    
@raises(IOError)
def test_load_fail():
    path = 'myvars.pkl'
    load_vars(path, ['a', 'b'])

def test_save_load():
    path = 'myvars.pkl'
    vars = {'a': 1, 'b': '2'}
    save_vars(path, vars)
    vars2 = load_vars(path, list(vars.keys()))
    assert vars == vars2
    
    os.remove(path)
    

#------------------------------------------------------------------------------
# Cache magic tests
#------------------------------------------------------------------------------
def test_cache_1():
    path = 'myvars.pkl'
    cell = """a = 1"""
    
    user_ns = {}
    def ip_run_cell(cell):
        exec_(cell, {}, user_ns)
    
    def ip_push(vars):
        user_ns.update(vars)
    
    cache(cell, path, vars=['a'], force=False, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    # We modify the variable in the namespace,
    user_ns['a'] = 2
    # and execute the cell again. The value should be loaded from the pickle
    # file.
    cache("""a = 2""", path, vars=['a'], force=False, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    # Now, we force the cell's execution.
    cache("""a = 2""", path, vars=['a'], force=True, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 2
    
    # Now, we prevent the cell's execution.
    user_ns['a'] = 0
    cache("""a = 3""", path, vars=['a'], force=False, read=True,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 2
    
    os.remove(path)
    
    