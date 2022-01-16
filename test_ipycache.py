# -*- coding: utf-8 -*-
"""Tests for ipycache.
"""

import hashlib
import os
import pickle
import sys
import unittest

from ipycache import (save_vars, load_vars, clean_var, clean_vars, do_save,
                      cache, exec_, conditional_eval)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    from cStringIO import StringIO
else:
    from io import StringIO


def removeFile(path):
    """Remove a file which may or may not exist, without throwing exceptions."""
    # In Python 3, we can write:
    #
    #     with contextlib.suppress(FileNotFoundError):
    #         os.remove(path)
    #
    # but to be compatible with Python 2, we explicitly check + remove.
    if os.path.exists(path):
        os.remove(path)


class FunctionTests(unittest.TestCase):

    def test_conditional_eval(self):
        test_var = 'abc'
        self.assertEqual(conditional_eval('$test_var', locals()), 'abc')
        x, fun = 10, lambda x: x
        test_eval = 'abc_{"10" if x==10 else "not_10"}_{fun(10)}'
        expect = 'abc_10_10'
        self.assertEqual(conditional_eval(test_eval, locals()), expect)

    def test_clean_var(self):
        self.assertEqual(clean_var('abc'), 'abc')
        self.assertEqual(clean_var('abc '), 'abc')
        self.assertEqual(clean_var('abc,'), 'abc')
        self.assertEqual(clean_var(',abc'), 'abc')

    def test_clean_vars(self):
        self.assertEqual(clean_vars(['abc', 'abc,']), ['abc'] * 2)

    def test_do_save(self):
        path = 'myvars.pkl'

        # File exists.
        open(path, 'wb').close()
        self.assertRaises(ValueError, do_save, path, force=True, read=True)
        self.assertTrue(do_save(path, force=True, read=False))
        self.assertFalse(do_save(path, force=False, read=False))
        self.assertFalse(do_save(path, force=False, read=True))
        removeFile(path)

        # File does not exist.
        self.assertRaises(ValueError, do_save, path, force=True, read=True)
        self.assertTrue(do_save(path, force=True, read=False))
        self.assertTrue(do_save(path, force=False, read=False))
        self.assertFalse(do_save(path, force=False, read=True))

    def test_load_fail(self):
        path = 'myvars.pkl'
        self.assertRaises(IOError, load_vars, path, ['a', 'b'])

    def test_save_load(self):
        path = 'myvars.pkl'
        vars = {'a': 1, 'b': '2'}
        save_vars(path, vars)
        vars2 = load_vars(path, list(vars.keys()))
        self.assertEqual(vars, vars2)
        removeFile(path)


class CacheMagicTests(unittest.TestCase):
    def test_cache_1(self):
        path = 'myvars.pkl'
        cell = """a = 1"""

        user_ns = {}

        def ip_run_cell(cell):
            exec_(cell, {}, user_ns)

        def ip_push(vars):
            user_ns.update(vars)

        cache(cell, path, vars=['a'], force=False, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 1)

        # We modify the variable in the namespace,
        user_ns['a'] = 2
        # and execute the cell again. The value should be loaded from the pickle
        # file. Note how we did not change cell contents
        cache("""a = 1""", path, vars=['a'], force=False, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 1)

        # changing  the cell will trigger reload
        # file. Note how we did not change cell contents
        cache("""a = 2""", path, vars=['a'], force=False, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 2)

        # store 1 again
        user_ns['a'] = 1
        cache("""a = 1""", path, vars=['a'], force=False, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        # hack the md5 so code change does not retrigger
        with open(path, 'rb') as op:
            data = pickle.load(op)
        data['_cell_md5'] = hashlib.md5("""a = 2""".encode()).hexdigest()
        with open(path, 'wb') as op:
            pickle.dump(data, op)
        # ensure we don't rerun
        user_ns['a'] = 2
        # and execute the cell again. The value should be loaded from the pickle
        # file. Note how we did not change cell contents
        cache("""a = 1""", path, vars=['a'], force=False, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 1)

        # Now, we force the cell's execution.
        cache("""a = 2""", path, vars=['a'], force=True, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 2)

        # Now, we prevent the cell's execution.
        user_ns['a'] = 0
        cache("""a = 3""", path, vars=['a'], force=False, read=True,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 2)

        removeFile(path)

    def test_cache_exception(self):
        """Check that, if an exception is raised during the cell's execution,
        the pickle file is not written."""
        path = 'myvars.pkl'
        cell = """a = 1;b = 1/0"""

        user_ns = {}

        def ip_run_cell(cell):
            exec_(cell, {}, user_ns)

        def ip_push(vars):
            user_ns.update(vars)

        cache(cell, path, vars=['a'], force=False, read=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 1)

        self.assertFalse(os.path.exists(path))
        removeFile(path)

    def test_cache_outputs(self):
        """Test the capture of stdout."""
        path = 'myvars.pkl'
        cell = """a = 1;print(a+1)"""

        user_ns = {}

        def ip_run_cell(cell):
            exec_(cell, {}, user_ns)

        def ip_push(vars):
            user_ns.update(vars)

        cache(cell, path, vars=['a'], verbose=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 1)

        # Capture stdout.
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        user_ns = {}
        cache(cell, path, vars=['a'], verbose=False,
              ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
        self.assertEqual(user_ns['a'], 1)

        sys.stdout = old_stdout

        # Check that stdout contains the print statement of the cached cell.
        self.assertEqual(mystdout.getvalue(), '2\n')

        removeFile(path)

    def test_cache_fail_1(self):
        """Fails when saving nonexistent variables."""
        path = 'myvars.pkl'
        cell = """a = 1"""

        user_ns = {}

        def ip_run_cell(cell):
            exec_(cell, {}, user_ns)

        def ip_push(vars):
            user_ns.update(vars)

        self.assertRaises(ValueError, cache, cell, path, vars=['a', 'b'],
                          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)

        removeFile(path)
