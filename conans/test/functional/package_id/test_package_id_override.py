import textwrap
import unittest

from conans.test.utils.tools import TestClient


class PackageIdOverrideTestCase(unittest.TestCase):
    def test_package_id_override(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile
            
            class Recipe(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                
                def package_id(self):
                    if self.settings.compiler == "gcc":
                        self.info.settings.compiler.version = "any"
                        self.info.settings.compiler.libcxx = "any"
        """)
        t = TestClient()
        t.save({"conanfile.py": conanfile})

        t.run("create . name/version@ -s os=Linux -s compiler=gcc -s compiler.version=8 -s compiler.libcxx=libstdc++11")
        package_id = "bfb9222fb3c8cfb34f0f71a0aeaa96b7f7862feb"
        self.assertIn("name/version: Package '{}' created".format(package_id), t.out)

        # Search the package
        t.run("search name/version@")
        self.assertIn("Package_ID: {}".format(package_id), t.out)

        # Consume the package (install)
        t.run("install name/version@ -s os=Linux -s compiler=gcc -s compiler.version=8 -s compiler.libcxx=libstdc++11")
        self.assertIn("name/version:{} - Cache".format(package_id), t.out)

        # Consume the package (conanfile.txt)
        t.save({'conanfile.txt': "[requires]\nname/version"})
        t.run("install conanfile.txt -s os=Linux -s compiler=gcc -s compiler.version=8 -s compiler.libcxx=libstdc++11")
        self.assertIn("name/version:{} - Cache".format(package_id), t.out)
