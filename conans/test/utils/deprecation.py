# coding=utf-8

import warnings
from contextlib import contextmanager


@contextmanager
def catch_deprecation_warning(test_suite, n=1, cls=DeprecationWarning):
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings("always", module="(.*\.)?conans\..*")
        yield
        test_suite.assertEqual(len(w), n)
        test_suite.assertTrue(issubclass(w[0].category, cls))
