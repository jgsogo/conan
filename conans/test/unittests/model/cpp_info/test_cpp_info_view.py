import unittest

import six

from conans.model.cpp_info.cpp_info import CppInfo
from conans.model.cpp_info.cpp_info_view import CppInfoView


class CppInfoViewBasicTestCase(unittest.TestCase):
    def test_not_assignable(self):
        cpp_info = CppInfo("name_init", "rootpath_value")
        cpp_info_view = CppInfoView(cpp_info, version="version_value", description="description")

        # Cannot assign to fields
        with six.assertRaisesRegex(self, AttributeError, "can't set attribute"):
            cpp_info_view.version = "1.2.3"
        with six.assertRaisesRegex(self, AttributeError, "can't set attribute"):
            cpp_info_view.libs = ["other libs"]

        # Can abuse python and modify returned object, but value doesn't change
        cpp_info_view.libdirs.append("aa")
        self.assertListEqual(cpp_info_view.libdirs, ["lib"])


class CppInfoViewWithConfigsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cpp_info = CppInfo("name_init", "rootpath_value")
        # Names
        cpp_info.name = "name_value"
        cpp_info.names["cmake"] = "cmake_name"
        cpp_info.names["cmake_find_package"] = "cmake_find_package_name"
        # Non path values
        cpp_info.libs = ["lib_value"]
        cpp_info.system_libs.append("system_lib_value")
        cpp_info.includedirs = ["includedirs_value"]
        cpp_info.libdirs.append("libdirs_value")

        # Assign config debug
        cpp_info.debug.libs = ["lib_debug_value"]
        cpp_info.debug.defines = ["defines_debug_value"]
        cpp_info.debug.includedirs = ["includedirs_debug_value"]
        cpp_info.debug.bindirs = ["bindirs_debug_value"]

        cls.cpp_info_view = CppInfoView(cpp_info, version="version_value", description="description")

    def test_names(self):
        # Names for the main object
        self.assertEqual(str(self.cpp_info_view), "name_init")
        self.assertEqual(self.cpp_info_view.get_name("cmake"), "cmake_name")
        self.assertEqual(self.cpp_info_view.get_name("cmake_find_package"),
                         "cmake_find_package_name")
        self.assertEqual(self.cpp_info_view.get_name("invalid"), "name_value")

        # Names for the config object
        self.assertEqual(str(self.cpp_info_view.debug), "name_init")
        self.assertEqual(self.cpp_info_view.debug.get_name("cmake"), "cmake_name")
        self.assertEqual(self.cpp_info_view.debug.get_name("cmake_find_package"),
                         "cmake_find_package_name")
        self.assertEqual(self.cpp_info_view.debug.get_name("invalid"), "name_value")

    def test_append_fields(self):
        self.assertEqual(self.cpp_info_view.libs, ["lib_value"])
        self.assertEqual(self.cpp_info_view.debug.libs, ["lib_value", "lib_debug_value"])

        self.assertEqual(self.cpp_info_view.system_libs, ["system_lib_value"])
        self.assertEqual(self.cpp_info_view.debug.system_libs, ["system_lib_value"])

        self.assertEqual(self.cpp_info_view.defines, [])
        self.assertEqual(self.cpp_info_view.debug.defines, ["defines_debug_value"])

    def test_path_fields(self):
        self.assertEqual(self.cpp_info_view.includedirs, ["includedirs_value"])
        self.assertEqual(self.cpp_info_view.debug.includedirs,
                         ["includedirs_value", "includedirs_debug_value"])

        self.assertEqual(self.cpp_info_view.libdirs, ["lib", "libdirs_value"])
        self.assertEqual(self.cpp_info_view.debug.libdirs, ["lib", "libdirs_value", "lib"])

        self.assertEqual(self.cpp_info_view.bindirs, ["bin"])
        self.assertEqual(self.cpp_info_view.debug.bindirs, ["bin", "bindirs_debug_value"])

    def test_abs_paths_fields(self):
        self.assertEqual(self.cpp_info_view.include_paths, ["rootpath_value/includedirs_value"])
        self.assertEqual(self.cpp_info_view.debug.include_paths,
                         ["rootpath_value/includedirs_value",
                          "rootpath_value/includedirs_debug_value"])

        self.assertEqual(self.cpp_info_view.lib_paths,
                         ["rootpath_value/lib", "rootpath_value/libdirs_value"])
        self.assertEqual(self.cpp_info_view.debug.lib_paths,
                         ["rootpath_value/lib", "rootpath_value/libdirs_value",
                          "rootpath_value/lib"])

        self.assertEqual(self.cpp_info_view.bin_paths, ["rootpath_value/bin"])
        self.assertEqual(self.cpp_info_view.debug.bin_paths,
                         ["rootpath_value/bin", "rootpath_value/bindirs_debug_value"])


class CppInfoViewWithComponentsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cpp_info = CppInfo("name_init", "rootpath_value")
        # Names
        cpp_info.name = "name_value"
        cpp_info.names["cmake"] = "cmake_name"

        # cmp1
        cpp_info.components["cmp1"].name = "cmp1_name_value"
        cpp_info.components["cmp1"].names["cmake"] = "cmp1_cmake_name"
        cpp_info.components["cmp1"].libs = ["cmp1", "core"]
        cpp_info.components["cmp1"].includedirs = ["cmp1/includes"]
        cpp_info.components["cmp1"].requires = ["zlib::zlib"]

        # cmp2
        cpp_info.components["cmp2"].libs = ["cmp2", "core"]
        cpp_info.components["cmp2"].includedirs = ["cmp2/includes"]
        cpp_info.components["cmp2"].requires = ["cmp1", "zlib::ssl"]

        cls.cpp_info_view = CppInfoView(cpp_info, version="version_value", description="description")

    def test_names(self):
        self.assertEqual(str(self.cpp_info_view), "name_init")
        self.assertEqual(str(self.cpp_info_view.components["cmp1"]), "name_init::cmp1")
        self.assertEqual(str(self.cpp_info_view.components["cmp2"]), "name_init::cmp2")

    def test_generator_names(self):
        # cmake
        self.assertEqual(self.cpp_info_view.get_name("cmake"), "cmake_name")
        self.assertEqual(self.cpp_info_view.components["cmp1"].get_name("cmake"),
                         "cmake_name::cmp1_cmake_name")
        self.assertEqual(self.cpp_info_view.components["cmp2"].get_name("cmake"), "cmake_name::cmp2")

        # other
        self.assertEqual(self.cpp_info_view.get_name("other"), "name_value")
        self.assertEqual(self.cpp_info_view.components["cmp1"].get_name("other"),
                         "name_value::cmp1_name_value")
        self.assertEqual(self.cpp_info_view.components["cmp2"].get_name("other"), "name_value::cmp2")

    def test_requires(self):
        self.assertListEqual(self.cpp_info_view.components["cmp1"].requires, ["zlib::zlib"])
        self.assertListEqual(self.cpp_info_view.components["cmp2"].requires,
                             ["name_init::cmp1", "zlib::ssl"])

    def test_libs(self):
        self.assertListEqual(self.cpp_info_view.libs, ["cmp2", "cmp1", "core"])
        self.assertListEqual(self.cpp_info_view.components["cmp1"].libs, ["cmp1", "core"])
        self.assertListEqual(self.cpp_info_view.components["cmp2"].libs, ["cmp2", "core"])

    def test_includedirs(self):
        self.assertListEqual(self.cpp_info_view.includedirs, ["cmp2/includes", "cmp1/includes"])
        self.assertListEqual(self.cpp_info_view.components["cmp1"].includedirs, ["cmp1/includes"])
        self.assertListEqual(self.cpp_info_view.components["cmp2"].includedirs, ["cmp2/includes"])

    def test_include_paths(self):
        self.assertListEqual(self.cpp_info_view.include_paths,
                             ['rootpath_value/cmp2/includes', 'rootpath_value/cmp1/includes'])
        self.assertListEqual(self.cpp_info_view.components["cmp1"].include_paths,
                             ["rootpath_value/cmp1/includes"])
        self.assertListEqual(self.cpp_info_view.components["cmp2"].include_paths,
                             ["rootpath_value/cmp2/includes"])
