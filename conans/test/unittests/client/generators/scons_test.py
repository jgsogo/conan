import unittest

from conans.client.generators.scons import SConsGenerator
from conans.model.conan_file import ConanFile
from conans.model.env_info import EnvValues
from conans.model.ref import ConanFileReference
from conans.model.settings import Settings
from conans.test.utils.tools import TestBufferConanOutput
from conans.model.cpp_info import CppInfoView, CppInfo


class SConsGeneratorTest(unittest.TestCase):

    def variables_setup_test(self):
        conanfile = ConanFile(TestBufferConanOutput(), None)
        conanfile.initialize(Settings({}), EnvValues())
        ref = ConanFileReference.loads("MyPkg/0.1@lasote/stables")
        cpp_info = CppInfo(ref.name, "")
        cpp_info.defines = ["MYDEFINE1"]
        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, "0.1"))
        ref = ConanFileReference.loads("MyPkg2/3.2.3@lasote/stables")
        cpp_info = CppInfo(ref.name, "")
        cpp_info.defines = ["MYDEFINE2"]
        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, "3.2.3"))
        generator = SConsGenerator(conanfile)
        content = generator.content
        scons_lines = content.splitlines()
        self.assertIn("        \"CPPDEFINES\"  : [\'MYDEFINE2\', \'MYDEFINE1\'],", scons_lines)
        self.assertIn("        \"CPPDEFINES\"  : [\'MYDEFINE1\'],", scons_lines)
        self.assertIn("        \"CPPDEFINES\"  : [\'MYDEFINE2\'],", scons_lines)
        self.assertIn('    "conan_version" : "None",', scons_lines)
        self.assertIn('    "MyPkg_version" : "0.1",', scons_lines)
        self.assertIn('    "MyPkg2_version" : "3.2.3",', scons_lines)
