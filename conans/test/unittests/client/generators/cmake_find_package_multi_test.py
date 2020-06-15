import unittest

from conans.client.generators import CMakeFindPackageMultiGenerator
from conans.model.conan_file import ConanFile
from conans.model.env_info import EnvValues
from conans.model.ref import ConanFileReference
from conans.test.unittests.client.generators.cmake_test import _MockSettings
from conans.test.utils.tools import TestBufferConanOutput
from conans.model.cpp_info import CppInfoView, CppInfo


class CMakeFindPackageMultiTest(unittest.TestCase):

    def cmake_find_package_multi_version_test(self):
        # https://github.com/conan-io/conan/issues/6908
        settings_mock = _MockSettings(build_type="Debug")
        conanfile = ConanFile(TestBufferConanOutput(), None)
        conanfile.initialize(settings_mock, EnvValues())
        ref = ConanFileReference.loads("my_pkg/0.1@user/stable")
        cpp_info = CppInfo(ref.name, "")
        cpp_info.debug.libs = ["mylib"]
        conanfile.deps_cpp_info.add(ref.name, CppInfoView(cpp_info, ref.version))

        generator = CMakeFindPackageMultiGenerator(conanfile)
        content = generator.content
        config_version = content["my_pkgConfigVersion.cmake"]
        self.assertIn('set(PACKAGE_VERSION "0.1")', config_version)
