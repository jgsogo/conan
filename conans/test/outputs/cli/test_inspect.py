# coding=utf-8

import re
import textwrap
import unittest

from conans.model.ref import ConanFileReference
from conans.test.utils.tools import TestClient


class CLIInspectOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Lib(ConanFile):
            pass
        """)

    def setUp(self):
        self.client = TestClient()
        self.client.run("profile new --detect default")

        self.reference = "name/version@user/channel"
        files = {'conanfile.py': self.conanfile}
        self.client.save(files)
        # self.client.run("install . {}".format(self.reference))

    def test_basic(self):
        # There are only a few types of lines:
        self.client.run("inspect .".format(self.reference))
        print(self.client.out)
        self.fail("AAA")
