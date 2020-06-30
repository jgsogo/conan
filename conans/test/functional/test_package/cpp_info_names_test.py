import unittest
import textwrap
from conans.test.utils.tools import TestClient


class CppInfoNamesTestCase(unittest.TestCase):
    conanfile = textwrap.dedent("""
        from conans import ConanFile

        class Recipe(ConanFile):
            name = "pkg_name"

            def package_info(self):
                self.cpp_info.name = "name"
                self.cpp_info.names["txt"] = "txt_name"
                self.cpp_info.names["cmake_find_package"] = "cmake_find_package"
    """)

    test_package = textwrap.dedent("""
        from conans import ConanFile

        class TestPackage(ConanFile):
            generators = "cmake_find_package"

            def build(self):
                pkg_info = self.deps_cpp_info["pkg_name"]
                self.output.info("name: {}".format(pkg_info.name))  # Deprecated in Conan v2
                self.output.info("txt: {}".format(pkg_info.get_name("txt")))
                self.output.info("cmake: {}".format(pkg_info.get_name("cmake_find_package")))

            def test(self):
                pass
    """)

    def test_names(self):
        t = TestClient()
        t.save({'conanfile.py': self.conanfile,
                'test_package/conanfile.py': self.test_package})
        t.run("create conanfile.py pkg_name/version@")

        # Names in generated files match expected
        self.assertIn("pkg_name/version (test package): Generator cmake_find_package"
                      " created Findcmake_find_package.cmake", t.out)

        # Information should be preserved
        self.assertIn("pkg_name/version (test package): name: name", t.out)
        self.assertIn("pkg_name/version (test package): txt: txt_name", t.out)
        self.assertIn("pkg_name/version (test package): cmake: cmake_find_package", t.out)
