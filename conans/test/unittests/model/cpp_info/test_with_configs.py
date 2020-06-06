import unittest

from conans.model.cpp_info import CppInfo, DepsCppInfo, GeneratorCppInfo


class BasicCppInfoTestCase(unittest.TestCase):
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
        # Path values
        cpp_info.includedirs = ["includedirs_value"]
        cpp_info.libdirs.append("libdirs_value")
        # Assign config debug
        cpp_info.debug.libs = ["lib_debug_value"]
        cpp_info.debug.includedirs = ["includedirs_debug_value"]
        cpp_info.debug.name = "name_debug_value"
        cpp_info.debug.names["cmake"] = "cmake_debug_name"

        cls.cpp_info = cpp_info
        cls.deps_cpp_info = DepsCppInfo("version_value", cls.cpp_info)
        cls.generator_cpp_info = GeneratorCppInfo(cls.deps_cpp_info)
        cls.deps_cpp_info_debug = cls.deps_cpp_info.debug
        cls.generator_cpp_info_debug = cls.generator_cpp_info.debug

    def test_names(self):
        self.assertEqual(str(self.cpp_info), "name_init")
        self.assertEqual(str(self.deps_cpp_info), "name_init")
        self.assertEqual(str(self.generator_cpp_info), "name_init")
        self.assertEqual(str(self.deps_cpp_info_debug), "name_init")
        self.assertEqual(str(self.generator_cpp_info_debug), "name_init")

    def test_name_generators(self):
        self.assertEqual(self.cpp_info.get_name("cmake"), "cmake_name")
        self.assertEqual(self.deps_cpp_info.get_name("cmake"), "cmake_name")
        self.assertEqual(self.generator_cpp_info.get_name("cmake"), "cmake_name")
        self.assertEqual(self.deps_cpp_info_debug.get_name("cmake"), "cmake_debug_name")
        self.assertEqual(self.generator_cpp_info_debug.get_name("cmake"), "cmake_debug_name")

        self.assertEqual(self.cpp_info.get_name("cmake_find_package"), "cmake_find_package_name")
        self.assertEqual(self.deps_cpp_info.get_name("cmake_find_package"), "cmake_find_package_name")
        self.assertEqual(self.generator_cpp_info.get_name("cmake_find_package"), "cmake_find_package_name")
        self.assertEqual(self.deps_cpp_info_debug.get_name("cmake_find_package"), "cmake_find_package_name")
        self.assertEqual(self.generator_cpp_info_debug.get_name("cmake_find_package"), "cmake_find_package_name")

        self.assertEqual(self.cpp_info.get_name("not-used"), "name_value")
        self.assertEqual(self.deps_cpp_info.get_name("not-used"), "name_value")
        self.assertEqual(self.generator_cpp_info.get_name("not-used"), "name_value")
        self.assertEqual(self.deps_cpp_info_debug.get_name("not-used"), "name_value")
        self.assertEqual(self.generator_cpp_info_debug.get_name("not-used"), "name_value")

