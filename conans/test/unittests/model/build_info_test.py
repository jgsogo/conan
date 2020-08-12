import os
import unittest
from collections import defaultdict, namedtuple

from conans.client.generators import TXTGenerator
from conans.model.build_info import CppInfo
from conans.model.cpp_info import CppInfo, CppInfoView, CppInfoViewDict, CppInfoViewAggregated
from conans.model.env_info import DepsEnvInfo, EnvInfo
from conans.model.user_info import DepsUserInfo
from conans.test.utils.test_files import temp_folder
from conans.util.files import mkdir


class BuildInfoTest(unittest.TestCase):
    maxDiff = None

    def parse_test(self):
        text = """[includedirs]
F:/ChildrenPath
G:/mylib_path
H:/otherlib_path
I:/my_component_lib
J:/my-component-tool

[name_Boost]
Boost
[rootpath_Boost]
F:/
[includedirs_Boost]
F:/ChildrenPath

[name_My_Lib]
My_Lib
[rootpath_My_Lib]
G:/
[includedirs_My_Lib]
G:/mylib_path

[name_My_Other_Lib]
My_Other_Lib
[rootpath_My_Other_Lib]
H:/
[includedirs_My_Other_Lib]
H:/otherlib_path

[name_My.Component.Lib]
My.Component.Lib
[rootpath_My.Component.Lib]
I:/
[includedirs_My.Component.Lib]
I:/my_component_lib

[name_My-Component-Tool]
My-Component-Tool
[rootpath_My-Component-Tool]
J:/
[includedirs_My-Component-Tool]
J:/my-component-tool
        """
        deps_cpp_info, _, _, _ = TXTGenerator.loads(text)

        def assert_cpp(deps_cpp_info_test):
            self.assertEqual(deps_cpp_info_test.includedirs,
                             ['F:/ChildrenPath', 'G:/mylib_path', 'H:/otherlib_path',
                              'I:/my_component_lib', 'J:/my-component-tool'])
            self.assertEqual(deps_cpp_info_test["Boost"].includedirs, ['ChildrenPath'])
            self.assertEqual(deps_cpp_info_test["My_Lib"].includedirs, ['mylib_path'])
            self.assertEqual(deps_cpp_info_test["My_Other_Lib"].includedirs, ['otherlib_path'])
            self.assertEqual(deps_cpp_info_test["My-Component-Tool"].includedirs,
                             ['my-component-tool'])

        assert_cpp(deps_cpp_info)
        # Now adding env_info
        text2 = text + """
[ENV_LIBA]
VAR2=23
"""
        deps_cpp_info, _, deps_env_info, _ = TXTGenerator.loads(text2)
        assert_cpp(deps_cpp_info)
        self.assertEqual(deps_env_info["LIBA"].VAR2, "23")

        # Now only with user info
        text3 = text + """
[USER_LIBA]
VAR2=23
"""
        deps_cpp_info, deps_user_info, _, _ = TXTGenerator.loads(text3)
        assert_cpp(deps_cpp_info)
        self.assertEqual(deps_user_info["LIBA"].VAR2, "23")

        # Now with all
        text4 = text + """
[USER_LIBA]
VAR2=23

[ENV_LIBA]
VAR2=23
"""
        deps_cpp_info, deps_user_info, deps_env_info, _ = TXTGenerator.loads(text4)
        assert_cpp(deps_cpp_info)
        self.assertEqual(deps_user_info["LIBA"].VAR2, "23")
        self.assertEqual(deps_env_info["LIBA"].VAR2, "23")

    def help_test(self):
        cpp_info = CppInfo("base", "C:")
        cpp_info.includedirs.append("whatever")
        cpp_info.includedirs.append("whenever")
        cpp_info.libdirs.append("other")
        cpp_info.libs.extend(["math", "winsock", "boost"])

        deps_cpp_info = CppInfoViewAggregated(CppInfoView(cpp_info, "<version>", "<description>"))
        child = CppInfo("Boost", "F:")
        child.includedirs.append("ChildrenPath")
        child.cxxflags.append("cxxmyflag")
        deps_cpp_info.add("Boost", CppInfoView(child, "<version>", "<description>"))

        deps_env_info = DepsEnvInfo()
        fakeconan = namedtuple("Conanfile",
                               "deps_cpp_info cpp_info deps_env_info env_info user_info deps_user_info")
        output = TXTGenerator(
            fakeconan(deps_cpp_info, None, deps_env_info, None, {}, defaultdict(dict))).content
        deps_cpp_info2, _, _ = TXTGenerator.loads(output)
        self.assertEqual(deps_cpp_info.get_configs(), deps_cpp_info2.get_configs())
        self.assertEqual(deps_cpp_info.includedirs, deps_cpp_info2.includedirs)
        self.assertEqual(deps_cpp_info.libdirs, deps_cpp_info2.libdirs)
        self.assertEqual(deps_cpp_info.bindirs, deps_cpp_info2.bindirs)
        self.assertEqual(deps_cpp_info.libs, deps_cpp_info2.libs)
        self.assertEqual(len(deps_cpp_info._dependencies),
                         len(deps_cpp_info2._dependencies))
        self.assertEqual(deps_cpp_info["Boost"].includedirs,
                         deps_cpp_info2["Boost"].includedirs)
        self.assertEqual(deps_cpp_info["Boost"].cxxflags,
                         deps_cpp_info2["Boost"].cxxflags)
        self.assertEqual(deps_cpp_info["Boost"].cxxflags, ["cxxmyflag"])

    def test_configs_test(self):
        cpp_info = CppInfo("root", "C:")
        cpp_info.includedirs.append("whatever")
        cpp_info.debug.includedirs.append("whenever")
        cpp_info.libs.extend(["math"])
        cpp_info.debug.libs.extend(["debug_Lib"])
        cpp_info_root = CppInfoView(cpp_info, "<version>", "<description>")

        deps_cpp_info = CppInfoViewDict()
        child = CppInfo("Boost", "F:")
        child.includedirs.append("ChildrenPath")
        child.debug.includedirs.append("ChildrenDebugPath")
        child.cxxflags.append("cxxmyflag")
        child.debug.cxxflags.append("cxxmydebugflag")
        deps_cpp_info.add("Boost", CppInfoView(child, "<version>", "<description>"))

        deps_env_info = DepsEnvInfo()
        env_info_lib1 = EnvInfo()
        env_info_lib1.var = "32"
        env_info_lib1.othervar.append("somevalue")
        deps_env_info.update(env_info_lib1, "LIB1")

        deps_user_info = DepsUserInfo()
        deps_user_info["LIB2"].myuservar = "23"

        fakeconan = namedtuple("Conanfile",
                               "deps_cpp_info cpp_info deps_env_info env_info user_info deps_user_info")
        output = TXTGenerator(
            fakeconan(deps_cpp_info, cpp_info_root, deps_env_info, deps_user_info, {},
                      defaultdict(dict))).content

        deps_cpp_info2, _, deps_env_info2, _ = TXTGenerator.loads(output, filter_empty=False)
        self.assertEqual(deps_cpp_info.includedirs, deps_cpp_info2.includedirs)
        self.assertEqual(deps_cpp_info.libdirs, deps_cpp_info2.libdirs)
        self.assertEqual(deps_cpp_info.bindirs, deps_cpp_info2.bindirs)
        self.assertEqual(deps_cpp_info.libs, deps_cpp_info2.libs)
        self.assertEqual(len(deps_cpp_info._dependencies),
                         len(deps_cpp_info2._dependencies))
        self.assertEqual(deps_cpp_info["Boost"].includedirs,
                         deps_cpp_info2["Boost"].includedirs)
        self.assertEqual(deps_cpp_info["Boost"].cxxflags,
                         deps_cpp_info2["Boost"].cxxflags)
        self.assertEqual(deps_cpp_info["Boost"].cxxflags, ["cxxmyflag"])

        self.assertEqual(deps_cpp_info.debug.includedirs, deps_cpp_info2.debug.includedirs)
        self.assertEqual(deps_cpp_info.debug.includedirs, ['F:/include', 'F:/ChildrenDebugPath'])

        self.assertEqual(deps_cpp_info.debug.libs, deps_cpp_info2.debug.libs)
        self.assertEqual(deps_cpp_info.debug.libs, ["debug_Lib"])

        self.assertEqual(deps_cpp_info["Boost"].debug.includedirs,
                         deps_cpp_info2["Boost"].debug.includedirs)
        self.assertEqual(deps_cpp_info["Boost"].debug.includedirs, ['include', 'ChildrenDebugPath'])
        self.assertEqual(deps_cpp_info["Boost"].debug.cxxflags,
                         deps_cpp_info2["Boost"].debug.cxxflags)
        self.assertEqual(deps_cpp_info["Boost"].debug.cxxflags, ["cxxmydebugflag"])

        self.assertEqual(deps_env_info["LIB1"].var, "32")
        self.assertEqual(deps_env_info["LIB1"].othervar, ["somevalue"])

        self.assertEqual(deps_user_info["LIB2"].myuservar, "23")

    def cpp_info_test(self):
        folder = temp_folder()
        mkdir(os.path.join(folder, "include"))
        mkdir(os.path.join(folder, "lib"))
        mkdir(os.path.join(folder, "local_bindir"))
        abs_folder = temp_folder()
        abs_include = os.path.join(abs_folder, "usr/include")
        abs_lib = os.path.join(abs_folder, "usr/lib")
        abs_bin = os.path.join(abs_folder, "usr/bin")
        mkdir(abs_include)
        mkdir(abs_lib)
        mkdir(abs_bin)
        info = CppInfo("", folder)
        info.includedirs.append(abs_include)
        info.libdirs.append(abs_lib)
        info.bindirs.append(abs_bin)
        info.bindirs.append("local_bindir")
        info = CppInfoView(info, "<version>", "<description>")
        self.assertEqual(info.include_paths, [os.path.join(folder, "include"), abs_include])
        self.assertEqual(info.lib_paths, [os.path.join(folder, "lib"), abs_lib])
        self.assertEqual(info.bin_paths, [abs_bin,
                                          os.path.join(folder, "bin"),
                                          os.path.join(folder, "local_bindir")])

    def cpp_info_system_libs_test(self):
        info1 = CppInfo("dep1", "folder1")
        info1.system_libs = ["sysdep1"]
        info2 = CppInfo("dep2", "folder2")
        info2.system_libs = ["sysdep2", "sysdep3"]
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("dep1", CppInfoView(info1, "<version>", "<description>"))
        deps_cpp_info.add("dep2", CppInfoView(info2, "<version>", "<description>"))
        self.assertEqual(["sysdep1", "sysdep2", "sysdep3"], deps_cpp_info.system_libs)
        self.assertEqual(["sysdep1"], deps_cpp_info["dep1"].system_libs)
        self.assertEqual(["sysdep2", "sysdep3"], deps_cpp_info["dep2"].system_libs)

    def cpp_info_name_test(self):
        folder = temp_folder()
        info = CppInfo("myname", folder)
        info.name = "MyName"
        info.names["my_generator"] = "MyNameForMyGenerator"
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("myname", CppInfoView(info, "<version>", "<description>"))
        self.assertIn("MyName", deps_cpp_info["myname"].get_name("my_undefined_generator"))
        self.assertIn("MyNameForMyGenerator", deps_cpp_info["myname"].get_name("my_generator"))

    def cpp_info_build_modules_test(self):
        folder = temp_folder()
        info = CppInfo("myname", folder)
        info.build_modules.append("my_module.cmake")
        info.debug.build_modules = ["mod-release.cmake"]
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("myname", CppInfoView(info, "<version>", "<description>"))
        self.assertListEqual([os.path.join(folder, "my_module.cmake")],
                             deps_cpp_info["myname"].build_modules_paths)
        self.assertListEqual([os.path.join(folder, "my_module.cmake"),
                              os.path.join(folder, "mod-release.cmake")],
                             deps_cpp_info["myname"].debug.build_modules_paths)

    def cppinfo_public_interface_test(self):
        folder = temp_folder()
        info = CppInfo("", folder)
        self.assertEqual([], info.libs)
        self.assertEqual([], info.system_libs)
        self.assertEqual(["include"], info.includedirs)
        self.assertEqual([], info.srcdirs)
        self.assertEqual(["res"], info.resdirs)
        self.assertEqual([""], info.builddirs)
        self.assertEqual(["bin"], info.bindirs)
        self.assertEqual(["lib"], info.libdirs)
        self.assertEqual(folder, info.rootpath)
        self.assertEqual([], info.defines)
        self.assertEqual("", info.sysroot)
        self.assertEqual([], info.cflags)
        self.assertEqual({}, info.get_configs())
        self.assertEqual([], info.cxxflags)
        self.assertEqual([], info.exelinkflags)
        self.assertEqual([], info.public_deps)
        self.assertEqual([], info.sharedlinkflags)
