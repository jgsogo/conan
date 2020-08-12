import os
import unittest

import six

from conans.errors import ConanException
from conans.model.cpp_info import CppInfo, CppInfoView, CppInfoViewDict
from conans.test.utils.test_files import temp_folder
from conans.util.files import save


class CppInfoComponentsTest(unittest.TestCase):

    def test_components_set(self):
        cpp_info = CppInfo("dep", "root_folder")
        cpp_info.components["liba"].name = "LIBA"
        cpp_info.components["libb"].includedirs.append("includewhat")
        cpp_info.components["libc"].libs.append("thelibc")
        self.assertListEqual(list(cpp_info.components.keys()), ["liba", "libb", "libc"])
        self.assertEqual(cpp_info.components["liba"].get_name("any"), "dep::LIBA")
        self.assertListEqual(cpp_info.components["libb"].includedirs, ["include", "includewhat"])
        self.assertListEqual(cpp_info.components["libc"].libs, ["thelibc"])

    def test_no_components_inside_components(self):
        cpp_info = CppInfo("", "root_folder")
        cpp_info.components["liba"].name = "LIBA"
        with self.assertRaises(AttributeError):
            _ = cpp_info.components["libb"].components

    def test_deps_cpp_info_libs(self):
        deps_cpp_info = CppInfoViewDict()

        dep1 = CppInfo("dep1", "root")
        dep1.components["liba"].libs.append("liba")
        dep1.components["libb"].libs.append("libb")
        deps_cpp_info.add("dep1", CppInfoView(dep1, "<version>", "<description>"))

        dep2 = CppInfo("dep2", "root")
        dep2.components["libc"].libs.append("libc")
        dep2.components["libd"].libs.append("libd")
        deps_cpp_info.add("dep2", CppInfoView(dep2, "<version>", "<description>"))

        dep3 = CppInfo("dep3", "root")
        dep3.libs.append("libdep3")
        deps_cpp_info.add("dep3", CppInfoView(dep3, "<version>", "<description>"))

        self.assertListEqual(["liba", "libb"], deps_cpp_info["dep1"].libs)
        self.assertListEqual(["libc", "libd"], deps_cpp_info["dep2"].libs)
        self.assertListEqual(["libdep3"], deps_cpp_info["dep3"].libs)
        self.assertListEqual(["liba", "libb", "libc", "libd", "libdep3"],
                             list(deps_cpp_info.libs))

    def test_deps_cpp_info_paths(self):
        deps_cpp_info = CppInfoViewDict()

        folder1 = temp_folder()
        dep1 = CppInfo("dep1", folder1)
        os.mkdir(os.path.join(folder1, "include"))
        os.mkdir(os.path.join(folder1, "includea"))
        os.mkdir(os.path.join(folder1, "includeb"))
        dep1.components["liba"].includedirs.append("includea")
        dep1.components["libb"].includedirs.append("includeb")
        deps_cpp_info.add("dep1", CppInfoView(dep1, "<version>", "<description>"))

        folder2 = temp_folder()
        dep2 = CppInfo("dep2", folder2)
        os.mkdir(os.path.join(folder2, "include"))
        os.mkdir(os.path.join(folder2, "includec"))
        os.mkdir(os.path.join(folder2, "included"))
        dep2.components["libc"].includedirs.append("includec")
        dep2.components["libd"].includedirs.append("included")
        deps_cpp_info.add("dep2", CppInfoView(dep2, "<version>", "<description>"))

        self.assertListEqual([os.path.join(folder1, "includea"), os.path.join(folder1, "include"),
                              os.path.join(folder1, "includeb")],
                             deps_cpp_info["dep1"].include_paths)
        self.assertListEqual([os.path.join(folder2, "includec"), os.path.join(folder2, "include"),
                              os.path.join(folder2, "included")],
                             deps_cpp_info["dep2"].include_paths)
        self.assertListEqual([os.path.join(folder1, "includea"), os.path.join(folder1, "include"),
                              os.path.join(folder1, "includeb"), os.path.join(folder2, "includec"),
                              os.path.join(folder2, "include"), os.path.join(folder2, "included")],
                             deps_cpp_info.include_paths)

    def test_deps_cpp_info_libs_defines_flags(self):
        deps_cpp_info = CppInfoViewDict()

        dep1 = CppInfo("dep1", "root")
        dep1.components["liba"].libs.append("liba")
        dep1.components["liba"].defines.append("DEFINEA")
        dep1.components["liba"].system_libs.append("sysa")
        dep1.components["liba"].cxxflags.append("cxxflaga")
        dep1.components["liba"].cflags.append("cflaga")
        dep1.components["liba"].sharedlinkflags.append("slinka")
        dep1.components["liba"].frameworks.append("frameworka")
        dep1.components["liba"].exelinkflags.append("elinka")
        dep1.components["libb"].libs.append("libb")
        dep1.components["libb"].defines.append("DEFINEB")
        dep1.components["libb"].system_libs.append("sysb")
        dep1.components["libb"].cxxflags.append("cxxflagb")
        dep1.components["libb"].cflags.append("cflagb")
        dep1.components["libb"].sharedlinkflags.append("slinkb")
        dep1.components["libb"].frameworks.append("frameworkb")
        dep1.components["libb"].exelinkflags.append("elinkb")
        deps_cpp_info.add("dep1", CppInfoView(dep1, "<version>", "<description>"))

        dep2 = CppInfo("dep2", "root")
        dep2.components["libc"].libs.append("libc")
        dep2.components["libd"].libs.append("libd")
        dep2.components["systemlib"].system_libs = ["systemlib"]
        dep2.components["libc"].cxxflags = ["cxxflagc"]
        dep2.components["libd"].cflags = ["cflagd"]
        dep2.components["libc"].sharedlinkflags = ["slinkc"]
        dep2.components["libd"].sharedlinkflags = ["slinkd"]
        deps_cpp_info.add("dep2", CppInfoView(dep2, "<version>", "<description>"))

        self.assertListEqual(["liba", "libb"], deps_cpp_info["dep1"].libs)
        self.assertListEqual(["libc", "libd"], deps_cpp_info["dep2"].libs)
        self.assertListEqual(["liba", "libb", "libc", "libd"], list(deps_cpp_info.libs))

        self.assertListEqual(["DEFINEA", "DEFINEB"], deps_cpp_info["dep1"].defines)
        self.assertListEqual(["DEFINEA", "DEFINEB"], list(deps_cpp_info.defines))

        self.assertListEqual(["sysa", "sysb"], deps_cpp_info["dep1"].system_libs)
        self.assertListEqual(["systemlib"], deps_cpp_info["dep2"].system_libs)
        self.assertListEqual(["sysa", "sysb", "systemlib"], list(deps_cpp_info.system_libs))

        self.assertListEqual(["cxxflaga", "cxxflagb"], deps_cpp_info["dep1"].cxxflags)
        self.assertListEqual(["cxxflagc"], deps_cpp_info["dep2"].cxxflags)
        self.assertListEqual(["cxxflaga", "cxxflagb", "cxxflagc"], deps_cpp_info.cxxflags)

        self.assertListEqual(["cflaga", "cflagb"], deps_cpp_info["dep1"].cflags)
        self.assertListEqual(["cflagd"], deps_cpp_info["dep2"].cflags)
        self.assertListEqual(["cflaga", "cflagb", "cflagd"], deps_cpp_info.cflags)

        self.assertListEqual(["slinka", "slinkb"], deps_cpp_info["dep1"].sharedlinkflags)
        self.assertListEqual(["slinkc", "slinkd"], deps_cpp_info["dep2"].sharedlinkflags)
        self.assertListEqual(["slinka", "slinkb", "slinkc", "slinkd"],
                             deps_cpp_info.sharedlinkflags)

        self.assertListEqual(["frameworka", "frameworkb"], deps_cpp_info["dep1"].frameworks)
        self.assertListEqual(["frameworka", "frameworkb"], list(deps_cpp_info.frameworks))

        self.assertListEqual(["elinka", "elinkb"], deps_cpp_info["dep1"].exelinkflags)
        self.assertListEqual([], deps_cpp_info["dep2"].exelinkflags)
        self.assertListEqual(["elinka", "elinkb"], list(deps_cpp_info.exelinkflags))

    def test_deps_cpp_info_libs_release_debug(self):
        deps_cpp_info = CppInfoViewDict()

        dep1 = CppInfo("dep1", "root")
        dep1.components["liba"].libs.append("liba")
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoConfig' object has no attribute 'components'"):
            dep1.release.components["libb"].libs.append("libb")
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoConfig' object has no attribute 'components'"):
            dep1.debug.components["libb"].libs.append("libb_d")
        with six.assertRaisesRegex(self, ConanException,
                                   "Cannot use components together with root values"):
            deps_cpp_info.add("dep1", CppInfoView(dep1, "<version>", "<description>"))

        deps_cpp_info = CppInfoViewDict()

        dep2 = CppInfo("dep2", "root")
        dep2.release.libs.append("libdep2")
        dep2.debug.libs.append("libdep2_d")
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoComponent' object has no attribute 'release'"):
            dep2.components["libc"].release.libs.append("libc")
        with six.assertRaisesRegex(self, AttributeError,
                                   "'CppInfoComponent' object has no attribute 'debug'"):
            dep2.components["libc"].debug.libs.append("libc_d")
        dep2.components["libc"].libs.append("libc")
        dep2.components["libc"].libs.append("libc2")

        with six.assertRaisesRegex(self, ConanException,
                                   "Cannot use components together with root values"):
            deps_cpp_info.add("dep2", CppInfoView(dep2, "<version>", "<description>"))

    def cpp_info_link_order_test(self):

        def _assert_link_order(sorted_libs):
            """
            Assert that dependent libs of a component are always found later in the list
            """
            assert sorted_libs, "'sorted_libs' is empty"
            for num, lib in enumerate(sorted_libs):
                component_name = lib[-1]
                for dep in info.components[component_name].requires:
                    for comp_lib in info.components[dep].libs:
                        self.assertIn(comp_lib, sorted_libs[num:])

        info = CppInfo("dep1", "")
        info.components["6"].libs = ["lib6"]
        info.components["6"].requires = ["4", "5"]
        info.components["5"].libs = ["lib5"]
        info.components["5"].requires = ["2"]
        info.components["4"].libs = ["lib4"]
        info.components["4"].requires = ["1"]
        info.components["3"].libs = ["lib3"]
        info.components["3"].requires = ["1"]
        info.components["1"].libs = ["lib1"]
        info.components["1"].requires = ["2"]
        info.components["2"].libs = ["lib2"]
        info.components["2"].requires = []
        dep_cpp_info = CppInfoView(info, "<version>", "<description>")
        _assert_link_order(dep_cpp_info.libs)
        self.assertEqual(["lib6", "lib5", "lib4", "lib3", "lib1", "lib2"], dep_cpp_info.libs)

        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("dep1", dep_cpp_info)
        self.assertEqual(["lib6", "lib5", "lib4", "lib3", "lib1", "lib2"],
                         deps_cpp_info.libs)

        info = CppInfo("dep2", "")
        info.components["K"].libs = ["libK"]
        info.components["K"].requires = ["G", "H"]
        info.components["J"].libs = ["libJ"]
        info.components["J"].requires = ["F"]
        info.components["G"].libs = ["libG"]
        info.components["G"].requires = ["F"]
        info.components["H"].libs = ["libH"]
        info.components["H"].requires = ["F", "E"]
        info.components["L"].libs = ["libL"]
        info.components["L"].requires = ["I"]
        info.components["F"].libs = ["libF"]
        info.components["F"].requires = ["C", "D"]
        info.components["I"].libs = ["libI"]
        info.components["I"].requires = ["E"]
        info.components["C"].libs = ["libC"]
        info.components["C"].requires = ["A"]
        info.components["D"].libs = ["libD"]
        info.components["D"].requires = ["A"]
        info.components["E"].libs = ["libE"]
        info.components["E"].requires = ["A", "B"]
        info.components["A"].libs = ["libA"]
        info.components["A"].requires = []
        info.components["B"].libs = ["libB"]
        info.components["B"].requires = []
        dep_cpp_info = CppInfoView(info, "<version>", "<description>")
        _assert_link_order(dep_cpp_info.libs)
        self.assertEqual(["libK", "libJ", "libG", "libH", "libL", "libF", "libI", "libC", "libD",
                          "libE", "libA", "libB"], dep_cpp_info.libs)
        deps_cpp_info.add("dep2", dep_cpp_info)

        self.assertEqual(["lib6", "lib5", "lib4", "lib3", "lib1", "lib2", "libK", "libJ", "libG",
                          "libH", "libL", "libF", "libI", "libC", "libD", "libE", "libA", "libB"],
                         list(deps_cpp_info.libs))

    def cppinfo_inexistent_component_dep_test(self):

        info = CppInfo("mydep", None)
        info.components["LIB1"].requires = ["LIB2"]
        with six.assertRaisesRegex(self, ConanException,
                                   "Component 'mydep::LIB1' declares a missing dependency"):
            _ = CppInfoView(info, "<version>", "<description>").libs
        info.components["LIB1"].requires = ["::LIB2"]
        with six.assertRaisesRegex(self, ConanException, "Leading character '::' not allowed in "
                                                         "LIB1 requires"):
            _ = CppInfoView(info, "<version>", "<description>").libs

    def cpp_info_components_requires_loop_test(self):
        info = CppInfo("", "")
        info.components["LIB1"].requires = ["LIB1"]
        with six.assertRaisesRegex(self, ConanException, "Component 'LIB1' requires itself"):
            _ = CppInfoView(info, "<version>", "<description>").libs
        info = CppInfo("", "")
        info.components["LIB1"].requires = ["LIB2"]
        info.components["LIB2"].requires = ["LIB1", "LIB2"]
        with six.assertRaisesRegex(self, ConanException, "Component 'LIB2' requires itself"):
            _ = CppInfoView(info, "<version>", "<description>").libs
        info = CppInfo("", "")
        info.components["LIB1"].requires = ["LIB2"]
        info.components["LIB2"].requires = ["LIB3"]
        info.components["LIB3"].requires = ["LIB1"]
        with six.assertRaisesRegex(self, ConanException,
                                   "There is a loop in component requirements"):
            _ = CppInfoView(info, "<version>", "<description>").defines

    def components_libs_order_test(self):
        info = CppInfo("dep1", "")
        info.components["liba"].libs = ["liba"]
        info.components["libb"].libs = ["libb"]
        dep_cpp_info = CppInfoView(info, "<version>", "<description>")
        self.assertListEqual(["liba", "libb"], dep_cpp_info.libs)
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("dep1", dep_cpp_info)
        self.assertListEqual(["liba", "libb"], deps_cpp_info["dep1"].libs)
        self.assertListEqual(["liba", "libb"], list(deps_cpp_info.libs))

        info = CppInfo("dep1", "")
        info.components["liba"].libs = ["liba"]
        info.components["libb"].libs = ["libb"]
        dep_cpp_info = CppInfoView(info, "<version>", "<description>")
        info2 = CppInfo("dep2", "")
        info2.components["libc"].libs = ["libc"]
        dep_cpp_info2 = CppInfoView(info2, "<version>", "<description>")
        deps_cpp_info = CppInfoViewDict()
        # Update in reverse order
        deps_cpp_info.add("dep2", dep_cpp_info2)
        deps_cpp_info.add("dep1", dep_cpp_info)
        self.assertListEqual(["liba", "libb"], deps_cpp_info["dep1"].libs)
        self.assertListEqual(["libc"], deps_cpp_info["dep2"].libs)
        self.assertListEqual(["libc", "liba", "libb"], list(deps_cpp_info.libs))

        info = CppInfo("dep1", "")
        info.components["liba"].libs = ["liba"]
        info.components["libb"].libs = ["libb"]
        info.components["libb"].requires = ["liba"]
        dep_cpp_info = CppInfoView(info, "<version>", "<description>")
        self.assertListEqual(["libb", "liba"], dep_cpp_info.libs)
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("dep1", dep_cpp_info)
        self.assertListEqual(["libb", "liba"], deps_cpp_info["dep1"].libs)
        self.assertListEqual(["libb", "liba"], list(deps_cpp_info.libs))

        info = CppInfo("dep1", "")
        info.components["liba"].libs = ["liba"]
        info.components["libb"].libs = ["libb"]
        info.components["libb"].requires = ["liba"]
        dep_cpp_info = CppInfoView(info, "<version>", "<description>")
        info2 = CppInfo("dep2", "")
        info2.components["libc"].libs = ["libc"]
        dep_cpp_info2 = CppInfoView(info2, "<version>", "<description>")
        deps_cpp_info = CppInfoViewDict()
        # Update in reverse order
        deps_cpp_info.add("dep2", dep_cpp_info2)
        deps_cpp_info.add("dep1", dep_cpp_info)
        self.assertListEqual(["libb", "liba"], deps_cpp_info["dep1"].libs)
        self.assertListEqual(["libc"], deps_cpp_info["dep2"].libs)
        self.assertListEqual(["libc", "libb", "liba"], list(deps_cpp_info.libs))

    def cppinfo_components_dirs_test(self):
        folder = temp_folder()
        info = CppInfo("OpenSSL", folder)
        info.components["OpenSSL"].includedirs = ["include"]
        info.components["OpenSSL"].libdirs = ["lib"]
        info.components["OpenSSL"].builddirs = ["build"]
        info.components["OpenSSL"].bindirs = ["bin"]
        info.components["OpenSSL"].resdirs = ["res"]
        info.components["Crypto"].includedirs = ["headers"]
        info.components["Crypto"].libdirs = ["libraries"]
        info.components["Crypto"].builddirs = ["build_scripts"]
        info.components["Crypto"].bindirs = ["binaries"]
        info.components["Crypto"].resdirs = ["resources"]
        self.assertEqual(["include"], info.components["OpenSSL"].includedirs)
        self.assertEqual(["lib"], info.components["OpenSSL"].libdirs)
        self.assertEqual(["build"], info.components["OpenSSL"].builddirs)
        self.assertEqual(["bin"], info.components["OpenSSL"].bindirs)
        self.assertEqual(["res"], info.components["OpenSSL"].resdirs)
        self.assertEqual(["headers"], info.components["Crypto"].includedirs)
        self.assertEqual(["libraries"], info.components["Crypto"].libdirs)
        self.assertEqual(["build_scripts"], info.components["Crypto"].builddirs)
        self.assertEqual(["binaries"], info.components["Crypto"].bindirs)
        self.assertEqual(["resources"], info.components["Crypto"].resdirs)

        info.components["Crypto"].includedirs = ["different_include"]
        info.components["Crypto"].libdirs = ["different_lib"]
        info.components["Crypto"].builddirs = ["different_build"]
        info.components["Crypto"].bindirs = ["different_bin"]
        info.components["Crypto"].resdirs = ["different_res"]
        self.assertEqual(["different_include"], info.components["Crypto"].includedirs)
        self.assertEqual(["different_lib"], info.components["Crypto"].libdirs)
        self.assertEqual(["different_build"], info.components["Crypto"].builddirs)
        self.assertEqual(["different_bin"], info.components["Crypto"].bindirs)
        self.assertEqual(["different_res"], info.components["Crypto"].resdirs)

        info.components["Crypto"].includedirs.extend(["another_include"])
        info.components["Crypto"].includedirs.append("another_other_include")
        info.components["Crypto"].libdirs.extend(["another_lib"])
        info.components["Crypto"].libdirs.append("another_other_lib")
        info.components["Crypto"].builddirs.extend(["another_build"])
        info.components["Crypto"].builddirs.append("another_other_build")
        info.components["Crypto"].bindirs.extend(["another_bin"])
        info.components["Crypto"].bindirs.append("another_other_bin")
        info.components["Crypto"].resdirs.extend(["another_res"])
        info.components["Crypto"].resdirs.append("another_other_res")
        self.assertEqual(["different_include", "another_include", "another_other_include"],
                         info.components["Crypto"].includedirs)
        self.assertEqual(["different_lib", "another_lib", "another_other_lib"],
                         info.components["Crypto"].libdirs)
        self.assertEqual(["different_build", "another_build", "another_other_build"],
                         info.components["Crypto"].builddirs)
        self.assertEqual(["different_bin", "another_bin", "another_other_bin"],
                         info.components["Crypto"].bindirs)
        self.assertEqual(["different_res", "another_res", "another_other_res"],
                         info.components["Crypto"].resdirs)

    def test_component_default_dirs_deps_cpp_info_test(self):
        folder = temp_folder()
        info = CppInfo("my_lib", folder)
        info.components["Component"].filter_empty = False  # For testing purposes
        dep_info = CppInfoView(info, "<version>", "<description>")
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("my_lib", dep_info)
        self.assertListEqual(["include"], deps_cpp_info.includedirs)
        self.assertListEqual([os.path.join(folder, "include")], deps_cpp_info.include_paths)
        self.assertListEqual([], deps_cpp_info.srcdirs)
        self.assertListEqual([os.path.join(folder, "lib")], deps_cpp_info.lib_paths)
        self.assertListEqual([os.path.join(folder, "bin")], deps_cpp_info.bin_paths)
        self.assertListEqual([os.path.join(folder, "")], deps_cpp_info.build_paths)
        self.assertListEqual([os.path.join(folder, "res")], deps_cpp_info.res_paths)
        self.assertListEqual([os.path.join(folder, "Frameworks")], deps_cpp_info.framework_paths)

    def deps_cpp_info_components_test(self):
        folder = temp_folder()
        info = CppInfo("my_lib", folder)
        # Create file so path is not cleared
        save(os.path.join(folder, "include", "my_file.h"), "")
        info.components["Component"].libs = ["libcomp"]
        dep_info = CppInfoView(info, "<version>", "<description>")
        deps_cpp_info = CppInfoViewDict()
        deps_cpp_info.add("my_lib", dep_info)
        self.assertListEqual(["libcomp"], deps_cpp_info.libs)
        self.assertListEqual(["libcomp"], deps_cpp_info["my_lib"].components["Component"].libs)
        self.assertListEqual([os.path.join(folder, "include")], list(deps_cpp_info.include_paths))
        self.assertListEqual([os.path.join(folder, "include")],
                             list(deps_cpp_info["my_lib"].components["Component"].include_paths))
