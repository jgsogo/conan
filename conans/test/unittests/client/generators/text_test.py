# coding=utf-8
import textwrap
import unittest

from conans.client.generators.text import TXTGenerator
from conans.model.conan_file import ConanFile
from conans.model.env_info import EnvValues
from conans.model.ref import ConanFileReference
from conans.model.settings import Settings
from conans.test.utils.tools import TestBufferConanOutput
from conans.model.cpp_info import CppInfoView, CppInfo


class TextGeneratorTest(unittest.TestCase):

    def test_content(self):
        conanfile = ConanFile(TestBufferConanOutput(), None)
        conanfile.initialize(Settings({}), EnvValues())
        ref = ConanFileReference.loads("MyPkg/0.1@lasote/stables")
        cpp_info = CppInfo(ref.name, "dummy_root_folder1")
        cpp_info.defines = ["MYDEFINE1"]
        cpp_info.cxxflags = ["-cxxflag_parent"]
        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, "<version>"))

        ref = ConanFileReference.loads("MyPkg2/0.1@lasote/stables")
        cpp_info = CppInfo(ref.name, "dummy_root_folder2")
        cpp_info.defines = ["MYDEFINE2"]
        cpp_info.cxxflags = ["-cxxflag_dep"]
        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, "<version>"))

        generator = TXTGenerator(conanfile)
        txt_out = generator.content

        self.assertIn(textwrap.dedent("""
            [cppflags_MyPkg]
            -cxxflag_parent

            [cxxflags_MyPkg]
            -cxxflag_parent"""), txt_out)

        self.assertIn(textwrap.dedent("""
            [cppflags_MyPkg]
            -cxxflag_parent

            [cxxflags_MyPkg]
            -cxxflag_parent"""), txt_out)

    def test_load_sytem_libs(self):
        content = textwrap.dedent("""
            [system_libs]
            main

            [system_libs_requirement]
            requirement

            [system_libs_requirement_other]
            requirement_other
        """)

        deps_cpp_info, _, _ = TXTGenerator.loads(content)
        self.assertEqual(deps_cpp_info.system_libs, ["main", ])
        a = deps_cpp_info["requirement"]
        self.assertEqual(deps_cpp_info["requirement"].system_libs, ["requirement", ])
        self.assertEqual(deps_cpp_info["requirement_other"].system_libs, ["requirement_other", ])
