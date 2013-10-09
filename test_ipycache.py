# -*- coding: utf-8 -*-
"""
Tests for ipycache.
"""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import os
from nose.tools import raises
from ipycache import save_vars, load_vars, clean_var, clean_vars

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
    
