import unittest

import six

from conans.errors import ConanException
from conans.model.cpp_info.cpp_info import CppInfo, CppInfoComponent


class CppInfoBaseTestCase(object):

    def test_default_name(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        self.assertEqual(str(cpp_info), "default")
        self.assertEqual(cpp_info.name, "default")
        self.assertEqual(cpp_info.get_name("cmake"), "default")
        self.assertEqual(cpp_info.get_name("pkg_config"), "default")

        cpp_info.name = "other"
        self.assertEqual(str(cpp_info), "default")
        self.assertEqual(cpp_info.name, "other")
        self.assertEqual(cpp_info.get_name("cmake"), "other")
        self.assertEqual(cpp_info.get_name("pkg_config"), "other")

    def test_names_generators(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        cpp_info.names["cmake"] = "cmake_name"
        self.assertEqual(cpp_info.name, "default")
        self.assertEqual(cpp_info.get_name("cmake"), "cmake_name")
        self.assertEqual(cpp_info.get_name("pkg_config"), "default")

    def test_rootpath(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        self.assertEqual(cpp_info.rootpath, "rootpath")

    def test_default_field_values(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        # paths
        self.assertListEqual(cpp_info.includedirs, ["include"])
        self.assertListEqual(cpp_info.libdirs, ["lib"])
        self.assertListEqual(cpp_info.resdirs, ["res"])
        self.assertListEqual(cpp_info.bindirs, ["bin"])
        self.assertListEqual(cpp_info.builddirs, [""])
        self.assertListEqual(cpp_info.frameworkdirs, ["Frameworks"])
        self.assertListEqual(cpp_info.build_modules, [])
        # non paths
        self.assertListEqual(cpp_info.libs, [])
        self.assertListEqual(cpp_info.defines, [])
        self.assertListEqual(cpp_info.cflags, [])
        self.assertListEqual(cpp_info.cxxflags, [])
        self.assertListEqual(cpp_info.sharedlinkflags, [])
        self.assertListEqual(cpp_info.exelinkflags, [])
        self.assertListEqual(cpp_info.frameworks, [])
        self.assertListEqual(cpp_info.system_libs, [])

    def test_basic_functionality(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        cpp_info.libs = ["lib1", "lib2"]
        cpp_info.defines.append("DEFINE")
        cpp_info.system_libs.extend(["m", "pthread"])
        self.assertListEqual(cpp_info.libs, ["lib1", "lib2"])
        self.assertListEqual(cpp_info.defines, ["DEFINE"])
        self.assertListEqual(cpp_info.system_libs, ["m", "pthread"])

        cpp_info.bindirs = ["dir1", "dir2"]
        cpp_info.libdirs.append("dir1")
        cpp_info.includedirs.extend(["dir1", "dir2"])
        self.assertListEqual(cpp_info.bindirs, ["dir1", "dir2"])
        self.assertListEqual(cpp_info.libdirs, ["lib", "dir1"])
        self.assertListEqual(cpp_info.includedirs, ["include", "dir1", "dir2"])


class CppInfoTestCase(CppInfoBaseTestCase, unittest.TestCase):
    cpp_info_class = CppInfo

    def test_components(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        cpp_info.components["cmp1"].includedirs = ["include1"]
        cpp_info.components["cmp1"].bindirs.append("bin2")
        self.assertListEqual(cpp_info.components["cmp1"].includedirs, ["include1"])
        self.assertListEqual(cpp_info.components["cmp1"].bindirs, ["bin", "bin2"])

    def test_configs(self):
        cpp_info = self.cpp_info_class("default", "rootpath")
        cpp_info.release.includedirs.append("include2")
        self.assertListEqual(cpp_info.release.includedirs, ["include", "include2"])


class CppInfoComponentTestCase(CppInfoBaseTestCase, unittest.TestCase):
    cpp_info_class = CppInfoComponent

    def test_field_requires(self):
        cmp_info = self.cpp_info_class("default", "rootpath")
        self.assertListEqual(cmp_info.requires, [])

    def test_no_nested_components(self):
        cmp_info = self.cpp_info_class("default", "rootpath")
        with six.assertRaisesRegex(self, ConanException,
                                   "Components cannot define components inside"):
            cmp_info.components["other"].includedirs = ["more_includes"]

    def test_no_configs(self):
        cmp_info = self.cpp_info_class("default", "rootpath")
        with six.assertRaisesRegex(self, AttributeError, "Invalid attribute 'release'"):
            cmp_info.release.includedirs = ["more_includes"]
