import unittest

import six

from conans.model.cpp_info.cpp_info import CppInfo, CppInfoComponent, CppInfoConfig


class CppInfoBaseTestCase(object):

    def test_rootpath(self):
        self.assertEqual(self.cpp_info.rootpath, "rootpath")

    def test_default_field_values(self):
        # paths
        self.assertListEqual(self.cpp_info.includedirs, ["include"])
        self.assertListEqual(self.cpp_info.libdirs, ["lib"])
        self.assertListEqual(self.cpp_info.resdirs, ["res"])
        self.assertListEqual(self.cpp_info.bindirs, ["bin"])
        self.assertListEqual(self.cpp_info.builddirs, [""])
        self.assertListEqual(self.cpp_info.frameworkdirs, ["Frameworks"])
        self.assertListEqual(self.cpp_info.build_modules, [])
        # non paths
        self.assertListEqual(self.cpp_info.libs, [])
        self.assertListEqual(self.cpp_info.defines, [])
        self.assertListEqual(self.cpp_info.cflags, [])
        self.assertListEqual(self.cpp_info.cxxflags, [])
        self.assertListEqual(self.cpp_info.sharedlinkflags, [])
        self.assertListEqual(self.cpp_info.exelinkflags, [])
        self.assertListEqual(self.cpp_info.frameworks, [])
        self.assertListEqual(self.cpp_info.system_libs, [])

    def test_basic_functionality(self):
        self.cpp_info.libs = ["lib1", "lib2"]
        self.cpp_info.defines.append("DEFINE")
        self.cpp_info.system_libs.extend(["m", "pthread"])
        self.assertListEqual(self.cpp_info.libs, ["lib1", "lib2"])
        self.assertListEqual(self.cpp_info.defines, ["DEFINE"])
        self.assertListEqual(self.cpp_info.system_libs, ["m", "pthread"])

        self.cpp_info.bindirs = ["dir1", "dir2"]
        self.cpp_info.libdirs.append("dir1")
        self.cpp_info.includedirs.extend(["dir1", "dir2"])
        self.assertListEqual(self.cpp_info.bindirs, ["dir1", "dir2"])
        self.assertListEqual(self.cpp_info.libdirs, ["lib", "dir1"])
        self.assertListEqual(self.cpp_info.includedirs, ["include", "dir1", "dir2"])


class CppInfoTestCase(CppInfoBaseTestCase, unittest.TestCase):
    def setUp(self):
        self.cpp_info = CppInfo("default", "rootpath")

    def test_default_name(self):
        self.assertEqual(str(self.cpp_info), "default")
        self.assertEqual(self.cpp_info.name, "default")
        self.assertEqual(self.cpp_info.get_name("cmake"), "default")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default")

        self.cpp_info.name = "other"
        self.assertEqual(str(self.cpp_info), "default")
        self.assertEqual(self.cpp_info.name, "other")
        self.assertEqual(self.cpp_info.get_name("cmake"), "other")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "other")

    def test_names_generators(self):
        self.cpp_info.names["cmake"] = "cmake_name"
        self.assertEqual(self.cpp_info.name, "default")
        self.assertEqual(self.cpp_info.get_name("cmake"), "cmake_name")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default")

    def test_components(self):
        self.cpp_info.components["cmp1"].includedirs = ["include1"]
        self.cpp_info.components["cmp1"].bindirs.append("bin2")
        self.assertListEqual(self.cpp_info.components["cmp1"].includedirs, ["include1"])
        self.assertListEqual(self.cpp_info.components["cmp1"].bindirs, ["bin", "bin2"])

    def test_configs(self):
        self.cpp_info.release.includedirs.append("include2")
        self.assertListEqual(self.cpp_info.release.includedirs, ["include", "include2"])


class CppInfoComponentTestCase(CppInfoBaseTestCase, unittest.TestCase):
    def setUp(self):
        self.pkg_cpp_info = CppInfo("default", "rootpath")
        self.cpp_info = CppInfoComponent(self.pkg_cpp_info, "cmp")

    def test_default_name(self):
        self.assertEqual(str(self.cpp_info), "cmp")
        self.assertEqual(self.cpp_info.name, "cmp")
        self.assertEqual(self.cpp_info.get_name("cmake"), "default::cmp")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default::cmp")

        self.cpp_info.name = "other"
        self.assertEqual(str(self.cpp_info), "cmp")
        self.assertEqual(self.cpp_info.name, "other")
        self.assertEqual(self.cpp_info.get_name("cmake"), "default::other")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default::other")

        self.pkg_cpp_info.name = "pkg"
        self.assertEqual(str(self.cpp_info), "cmp")
        self.assertEqual(self.cpp_info.name, "other")
        self.assertEqual(self.cpp_info.get_name("cmake"), "pkg::other")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "pkg::other")

    def test_names_generators(self):
        self.cpp_info.names["cmake"] = "cmake_name"
        self.assertEqual(self.cpp_info.name, "cmp")
        self.assertEqual(self.cpp_info.get_name("cmake"), "default::cmake_name")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default::cmp")

        self.pkg_cpp_info.names["cmake"] = "cmake_name"
        self.assertEqual(self.cpp_info.get_name("cmake"), "cmake_name::cmake_name")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default::cmp")

    def test_field_requires(self):
        self.assertListEqual(self.cpp_info.requires, [])

    def test_no_nested_components(self):
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoComponent' object has no attribute 'components'"):
            self.cpp_info.components["other"].includedirs = ["more_includes"]

    def test_no_configs(self):
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoComponent' object has no attribute 'release'"):
            self.cpp_info.release.includedirs = ["more_includes"]


class CppInfoConfigTestCase(CppInfoBaseTestCase, unittest.TestCase):

    def setUp(self):
        self.pkg_cpp_info = CppInfo("default", "rootpath")
        self.cpp_info = CppInfoConfig(self.pkg_cpp_info)

    def test_default_name(self):
        self.assertEqual(str(self.cpp_info), "default")
        self.assertEqual(self.cpp_info.name, "default")
        self.assertEqual(self.cpp_info.get_name("cmake"), "default")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default")

        self.pkg_cpp_info.name = "other"
        self.assertEqual(str(self.cpp_info), "default")
        self.assertEqual(self.cpp_info.name, "other")
        self.assertEqual(self.cpp_info.get_name("cmake"), "other")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "other")

    def test_names_generators(self):
        self.pkg_cpp_info.names["cmake"] = "cmake_name"
        self.assertEqual(self.cpp_info.name, "default")
        self.assertEqual(self.cpp_info.get_name("cmake"), "cmake_name")
        self.assertEqual(self.cpp_info.get_name("pkg_config"), "default")

    def test_no_assign_names(self):
        with six.assertRaisesRegex(self, AttributeError, "can't set attribute"):
            self.cpp_info.name = "name_debug_value"

        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoConfig' object has no attribute 'names'"):
            self.cpp_info.names["cmake"] = "cmake_debug_name"

    def test_no_nested_components(self):
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoConfig' object has no attribute 'components'"):
            self.cpp_info.components["other"].includedirs = ["more_includes"]

    def test_no_configs(self):
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoConfig' object has no attribute 'release'"):
            self.cpp_info.release.includedirs = ["more_includes"]
