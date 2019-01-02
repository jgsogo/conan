# coding=utf-8

import re
import textwrap
import unittest

from conans.test.utils.tools import TestClient


class CLIInspectOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Lib(ConanFile):
            pass
        """)

    re_attr_pattern = re.compile("^\w+:\s.*$")

    def setUp(self):
        self.client = TestClient()
        self.client.run("profile new --detect default")

        self.reference = "name/version@user/channel"
        files = {'conanfile.py': self.conanfile}
        self.client.save(files)

    def test_basic(self):
        # There are only a few types of lines:
        self.client.run("inspect .".format(self.reference))
        for line in str(self.client.out).splitlines():
            self.assertTrue(self.re_attr_pattern.match(line))

    def test_enumerated_attributes(self):
        # There are only a few types of lines:
        self.client.run("inspect . -a name -a version".format(self.reference))
        for line in str(self.client.out).splitlines():
            self.assertTrue(self.re_attr_pattern.match(line))


