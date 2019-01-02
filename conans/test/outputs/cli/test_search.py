# coding=utf-8

import textwrap
import unittest

from conans.model.ref import ConanFileReference
from conans.test.utils.tools import TestClient


class CLISearchOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Lib(ConanFile):
            pass
        """)

    def setUp(self):
        self.client = TestClient()
        files = {'conanfile.py': self.conanfile}
        self.client.save(files)
        self.name = "zlib"

        for v in ["1.0", "2.0", "3.0"]:
            self.client.run("export . {}/{}@user/channel".format(self.name, v))

    def test_basic(self):
        self.client.run("search {}\*".format(self.name))
        lines = str(self.client.out).splitlines()
        self.assertEqual(lines[0], "Existing package recipes:")
        refs = [it for it in lines[1:] if it]
        self.assertTrue(len(refs))
        for line in refs:
            self.assertTrue(ConanFileReference.sep_pattern.match(line))

    def test_raw(self):
        self.client.run("search {}\* --raw".format(self.name))
        lines = str(self.client.out).splitlines()
        for line in lines:
            self.assertTrue(ConanFileReference.sep_pattern.match(line))
