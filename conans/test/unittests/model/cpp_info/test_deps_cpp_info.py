import unittest

from conans.model.cpp_info import CppInfo, DepsCppInfo


class DepsCppInfoTestCase(unittest.TestCase):

    def test_default_fields(self):
        cpp_info = CppInfo("name", "rootpath")
        deps_cpp_info = DepsCppInfo("version", cpp_info, remove_missing_paths=False)

        # paths
        self.assertListEqual(deps_cpp_info.includedirs, ["include"])
        self.assertListEqual(deps_cpp_info.libdirs, ["lib"])
        self.assertListEqual(deps_cpp_info.resdirs, ["res"])
        self.assertListEqual(deps_cpp_info.bindirs, ["bin"])
        self.assertListEqual(deps_cpp_info.builddirs, [""])
        self.assertListEqual(deps_cpp_info.frameworkdirs, ["Frameworks"])
        self.assertListEqual(deps_cpp_info.build_modules, [])
        # rootpath + paths
        self.assertListEqual(deps_cpp_info.include_paths, ["rootpath/include"])
        self.assertListEqual(deps_cpp_info.lib_paths, ["rootpath/lib"])
        self.assertListEqual(deps_cpp_info.res_paths, ["rootpath/res"])
        self.assertListEqual(deps_cpp_info.bin_paths, ["rootpath/bin"])
        self.assertListEqual(deps_cpp_info.build_paths, ["rootpath/"])
        self.assertListEqual(deps_cpp_info.framework_paths, ["rootpath/Frameworks"])
        self.assertListEqual(deps_cpp_info.build_modules_paths, [])

        # non paths
        self.assertListEqual(deps_cpp_info.libs, [])
        self.assertListEqual(deps_cpp_info.defines, [])
        self.assertListEqual(deps_cpp_info.cflags, [])
        self.assertListEqual(deps_cpp_info.cxxflags, [])
        self.assertListEqual(deps_cpp_info.sharedlinkflags, [])
        self.assertListEqual(deps_cpp_info.exelinkflags, [])
        self.assertListEqual(deps_cpp_info.frameworks, [])
        self.assertListEqual(deps_cpp_info.system_libs, [])

    def test_remove_missing(self):
        cpp_info = CppInfo("name", "rootpath")
        deps_cpp_info = DepsCppInfo("version", cpp_info, remove_missing_paths=True)

        # paths
        self.assertListEqual(deps_cpp_info.includedirs, ["include"])
        self.assertListEqual(deps_cpp_info.libdirs, ["lib"])
        self.assertListEqual(deps_cpp_info.resdirs, ["res"])
        self.assertListEqual(deps_cpp_info.bindirs, ["bin"])
        self.assertListEqual(deps_cpp_info.builddirs, [""])
        self.assertListEqual(deps_cpp_info.frameworkdirs, ["Frameworks"])
        self.assertListEqual(deps_cpp_info.build_modules, [])
        # rootpath + paths
        self.assertListEqual(deps_cpp_info.include_paths, [])
        self.assertListEqual(deps_cpp_info.lib_paths, [])
        self.assertListEqual(deps_cpp_info.res_paths, [])
        self.assertListEqual(deps_cpp_info.bin_paths, [])
        self.assertListEqual(deps_cpp_info.build_paths, [])
        self.assertListEqual(deps_cpp_info.framework_paths, [])
        self.assertListEqual(deps_cpp_info.build_modules_paths, [])

    def test_components(self):
        cpp_info = CppInfo("name", "rootpath")
        cpp_info.components["cmp1"].libs = ["lib1", "lib2"]
        cpp_info.components["cmp1"].includedirs.append("include2")
        cpp_info.components["cmp1"].requires = ["cmp2", "other::other"]
        deps_cpp_info = DepsCppInfo("version", cpp_info, remove_missing_paths=False)

        self.assertListEqual(deps_cpp_info.components["cmp1"].libs, ["lib1", "lib2"])
        self.assertListEqual(deps_cpp_info.components["cmp1"].includedirs, ["include", "include2"])
        self.assertListEqual(deps_cpp_info.components["cmp1"].include_paths,
                             ["rootpath/include", "rootpath/include2"])
        self.assertListEqual(deps_cpp_info.components["cmp1"].requires, ["name::cmp2", "other::other"])
