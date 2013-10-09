# -*- coding: utf-8 -*-
"""
Tests for ipycache.
"""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import os
from nose.tools import raises, assert_raises
from ipycache import (save_vars, load_vars, clean_var, clean_vars, do_save, 
    cache)

#------------------------------------------------------------------------------
# Tests
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
    

