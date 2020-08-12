import json
import unittest

from conans.client.generators.json_generator import JsonGenerator
from conans.model.conan_file import ConanFile
from conans.model.cpp_info import CppInfoView, CppInfo
from conans.model.env_info import EnvValues
from conans.model.ref import ConanFileReference
from conans.model.settings import Settings
from conans.test.utils.mocks import TestBufferConanOutput


class JsonTest(unittest.TestCase):

    def variables_setup_test(self):
        conanfile = ConanFile(TestBufferConanOutput(), None)
        conanfile.initialize(Settings({}), EnvValues())
        ref = ConanFileReference.loads("MyPkg/0.1@lasote/stables")
        cpp_info = CppInfo(ref.name, "dummy_root_folder1")
        cpp_info.defines = ["MYDEFINE1"]
        cpp_info.cflags.append("-Flag1=23")

        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, "1.3", "My cool description"))
        ref = ConanFileReference.loads("MyPkg2/0.1@lasote/stables")
        cpp_info = CppInfo(ref.name, "dummy_root_folder2")
        cpp_info.defines = ["MYDEFINE2"]
        cpp_info.exelinkflags = ["-exelinkflag"]
        cpp_info.sharedlinkflags = ["-sharedlinkflag"]
        cpp_info.cxxflags = ["-cxxflag"]
        cpp_info.public_deps = ["MyPkg"]
        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, "2.3"))
        generator = JsonGenerator(conanfile)
        json_out = generator.content

        parsed = json.loads(json_out)
        dependencies = parsed["dependencies"]
        self.assertEqual(len(dependencies), 2)
        my_pkg = dependencies[0]
        self.assertEqual(my_pkg["name"], "MyPkg")
        self.assertEqual(my_pkg["description"], "My cool description")
        self.assertEqual(my_pkg["defines"], ["MYDEFINE1"])
