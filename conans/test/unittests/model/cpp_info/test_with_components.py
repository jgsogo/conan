import unittest

from conans.model.cpp_info import CppInfo, DepsCppInfo, GeneratorCppInfo


class CppInfoWithComponentsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cpp_info = CppInfo("name_init", "rootpath_value")
        # Names
        cpp_info.name = "name_value"
        cpp_info.names["cmake"] = "cmake_name"

        # cmp1
        cpp_info.components["cmp1"].name = "cmp1_name_value"
        cpp_info.components["cmp1"].names["cmake"] = "cmp1_cmake_name"
        cpp_info.components["cmp1"].libs = ["cmp1"]
        cpp_info.components["cmp1"].includedirs = ["cmp1/includes"]

        # cmp2
        cpp_info.components["cmp2"].libs = ["cmp2"]
        cpp_info.components["cmp2"].includedirs = ["cmp2/includes"]

        cpp_info.clean_data()

        cls.cpp_info = cpp_info
        cls.cpp_info_cmp1 = cpp_info.components["cmp1"]
        cls.cpp_info_cmp2 = cpp_info.components["cmp2"]
        deps_cpp_info = DepsCppInfo("version_value", cpp_info)
        cls.deps_cpp_info = deps_cpp_info
        cls.deps_cpp_info_cmp1 = deps_cpp_info.components["cmp1"]
        cls.deps_cpp_info_cmp2 = deps_cpp_info.components["cmp2"]
        generator_cpp_info = GeneratorCppInfo(deps_cpp_info)
        cls.generator_cpp_info = generator_cpp_info
        cls.generator_cpp_info_cmp1 = generator_cpp_info.components["cmp1"]
        cls.generator_cpp_info_cmp2 = generator_cpp_info.components["cmp2"]

    def test_names(self):
        self.assertEqual(str(self.cpp_info_cmp1), "cmp1")
        self.assertEqual(str(self.cpp_info_cmp2), "cmp2")
        self.assertEqual(str(self.deps_cpp_info_cmp1), "cmp1")
        self.assertEqual(str(self.deps_cpp_info_cmp2), "cmp2")
        self.assertEqual(str(self.generator_cpp_info_cmp1), "cmp1")
        self.assertEqual(str(self.generator_cpp_info_cmp2), "cmp2")

    def test_name_generators(self):
        self.assertEqual(self.cpp_info_cmp1.get_name("cmake"), "cmake_name::cmp1_cmake_name")
        self.assertEqual(self.cpp_info_cmp2.get_name("cmake"), "cmake_name::cmp2")
        self.assertEqual(self.deps_cpp_info_cmp1.get_name("cmake"), "cmake_name::cmp1_cmake_name")
        self.assertEqual(self.deps_cpp_info_cmp2.get_name("cmake"), "cmake_name::cmp2")
        self.assertEqual(self.generator_cpp_info_cmp1.get_name("cmake"),
                         "cmake_name::cmp1_cmake_name")
        self.assertEqual(self.generator_cpp_info_cmp2.get_name("cmake"), "cmake_name::cmp2")

        self.assertEqual(self.cpp_info_cmp1.get_name("not"), "name_value::cmp1_name_value")
        self.assertEqual(self.cpp_info_cmp2.get_name("not"), "name_value::cmp2")
        self.assertEqual(self.deps_cpp_info_cmp1.get_name("not"), "name_value::cmp1_name_value")
        self.assertEqual(self.deps_cpp_info_cmp2.get_name("not"), "name_value::cmp2")
        self.assertEqual(self.generator_cpp_info_cmp1.get_name("not"), "name_value::cmp1_name_value")
        self.assertEqual(self.generator_cpp_info_cmp2.get_name("not"), "name_value::cmp2")

    def test_libs(self):
        self.assertEqual(self.cpp_info_cmp1.libs, ["cmp1"])
        self.assertEqual(self.cpp_info_cmp2.libs, ["cmp2"])
        self.assertEqual(self.deps_cpp_info_cmp1.libs, ["cmp1"])
        self.assertEqual(self.deps_cpp_info_cmp2.libs, ["cmp2"])
        self.assertEqual(self.generator_cpp_info_cmp1.libs, ["cmp1"])
        self.assertEqual(self.generator_cpp_info_cmp2.libs, ["cmp2"])

        self.assertEqual(self.cpp_info.libs, [])
        self.assertEqual(self.deps_cpp_info.libs, [])
        self.assertEqual(self.generator_cpp_info.libs, ["cmp1", "cmp2"])

    def test_includedirs(self):
        self.assertEqual(self.cpp_info_cmp1.includedirs, ["cmp1/includes"])
        self.assertEqual(self.cpp_info_cmp2.includedirs, ["cmp2/includes"])
        self.assertEqual(self.deps_cpp_info_cmp1.includedirs, ["cmp1/includes"])
        self.assertEqual(self.deps_cpp_info_cmp2.includedirs, ["cmp2/includes"])
        self.assertEqual(self.generator_cpp_info_cmp1.includedirs, ["cmp1/includes"])
        self.assertEqual(self.generator_cpp_info_cmp2.includedirs, ["cmp2/includes"])

        self.assertEqual(self.cpp_info.includedirs, [])
        self.assertEqual(self.deps_cpp_info.includedirs, [])
        self.assertEqual(self.generator_cpp_info.includedirs, ["cmp1/includes", "cmp2/includes"])

    def test_include_paths(self):
        #self.assertEqual(self.cpp_info_cmp1.include_paths, ["rootpath/cmp1/includes"])
        #self.assertEqual(self.cpp_info_cmp2.include_paths, ["rootpath/cmp2/includes"])
        self.assertEqual(self.deps_cpp_info_cmp1.include_paths, ["rootpath_value/cmp1/includes"])
        self.assertEqual(self.deps_cpp_info_cmp2.include_paths, ["rootpath_value/cmp2/includes"])
        self.assertEqual(self.generator_cpp_info_cmp1.include_paths, ["rootpath_value/cmp1/includes"])
        self.assertEqual(self.generator_cpp_info_cmp2.include_paths, ["rootpath_value/cmp2/includes"])

        #self.assertEqual(self.cpp_info.include_paths, [])
        self.assertEqual(self.deps_cpp_info.include_paths, [])
        self.assertEqual(self.generator_cpp_info.include_paths,
                         ["rootpath_value/cmp1/includes", "rootpath_value/cmp2/includes"])
