# coding=utf-8

import unittest

from conans.model.build_info import _CppInfo
from conans.test.utils.deprecation import catch_deprecation_warning


class CppFlagsTest(unittest.TestCase):
    """ Test that deprecated 'cppflags' still works (keep backwards compatibility) """

    def test_use_cxxflags(self):
        """ Changes in cxxflags get reflected in cppflags """

        with catch_deprecation_warning(self, n=4):
            cpp_info = _CppInfo()
            cpp_info.cxxflags = "flags"
            self.assertEqual(cpp_info.cppflags, "flags")
            self.assertEqual(cpp_info.cxxflags, cpp_info.cppflags)

            cpp_info.cxxflags = None
            self.assertEqual(cpp_info.cppflags, None)
            self.assertEqual(cpp_info.cxxflags, cpp_info.cppflags)

    def test_use_cppflags(self):
        """ Changes in cppflags get reflected in cxxflags """

        with catch_deprecation_warning(self, n=4):
            cpp_info = _CppInfo()

            cpp_info.cppflags = "flags"
            self.assertEqual(cpp_info.cxxflags, "flags")
            self.assertEqual(cpp_info.cxxflags, cpp_info.cppflags)

            cpp_info.cppflags = None
            self.assertEqual(cpp_info.cxxflags, None)
            self.assertEqual(cpp_info.cxxflags, cpp_info.cppflags)
