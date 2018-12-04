# coding=utf-8

import unittest
from conans.test.utils.tools import TestClient, TestServer


class ReusingPackageTest(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(servers={"default": TestServer()},
                                 users={"default": [("lasote", "mypass")]})

        conanfile = """from conans import ConanFile
class BasePck(ConanFile):
        name = "my_conanfile_base"
        version = "1.0"

        def build(self):
            self.output.info(">>> BasePck '{}/{}'".format(self.name, self.version))
"""
        self.client.save({"conanfile.py": conanfile})
        self.client.run("create . lasote/testing")
        self.assertIn(">>> BasePck 'my_conanfile_base/1.0'", self.client.out)
        self.assertIn("Package '5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9' created", self.client.out)

    def test_build_requires(self):
        br = """from conans import ConanFile

class BrPck(ConanFile):
    name = "package"
    version = "1.0"
    build_requires = "my_conanfile_base/1.0@lasote/testing"

    def build(self):
        self.output.info(">>> BrPck '{}/{}'".format(self.name, self.version))
"""
        self.client.save({"conanfile.py": br}, clean_first=True)
        self.client.run("create . lasote/testing")
        self.assertIn(">>> BrPck 'package/1.0'", self.client.out)
        self.assertNotIn(">>> BasePck 'my_conanfile_base/1.0'", self.client.out)
        self.assertIn("    my_conanfile_base/1.0@lasote/testing:5ab84d6acfe1f23c"
                      "4fae0ab88f26e3a396351ac9 - Cache", self.client.out)

    def test_python_requires(self):
        pr = """from conans import ConanFile, python_requires

base = python_requires("my_conanfile_base/1.0@lasote/testing")

class PrPck(base.BasePck):
    version = "pr"

    def build(self):
        self.output.info(">>> PrPck '{}/{}'".format(self.name, self.version))
        """
        self.client.save({"conanfile.py": pr}, clean_first=True)
        self.client.run("create . lasote/testing")
        self.assertIn(">>> PrPck 'my_conanfile_base/pr'", self.client.out)
        self.assertNotIn(">>> BasePck 'my_conanfile_base/1.0'", self.client.out)
        self.assertIn("    my_conanfile_base/pr@lasote/testing:5ab84d6acfe1f23c"
                      "4fae0ab88f26e3a396351ac9 - Build", self.client.out)

    def test_both(self):
        both = """from conans import ConanFile, python_requires

requirement = "my_conanfile_base/1.0@lasote/testing"
base = python_requires(requirement)

class BothPck(base.BasePck):
    version = "both"
    build_requires = requirement

    def build(self):
        self.output.info(">>> BothPck '{}/{}'".format(self.name, self.version))
        """
        self.client.save({"conanfile.py": both}, clean_first=True)
        self.client.run("create . lasote/testing")
        self.assertIn(">>> BothPck 'my_conanfile_base/both'", self.client.out)
        self.assertNotIn(">>> BasePck 'my_conanfile_base/1.0'", self.client.out)
        self.assertIn("    my_conanfile_base/both@lasote/testing:5ab84d6acfe1f23c"
                      "4fae0ab88f26e3a396351ac9 - Build", self.client.out)
        self.assertIn("    my_conanfile_base/1.0@lasote/testing:5ab84d6acfe1f23c"
                      "4fae0ab88f26e3a396351ac9 - Cache", self.client.out)
