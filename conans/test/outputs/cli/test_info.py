# coding=utf-8

import re
import textwrap
import unittest

from conans.model.ref import ConanFileReference
from conans.test.utils.tools import TestClient


class CLIInfoOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Lib(ConanFile):
            {body}
        """)

    def setUp(self):
        self.client = TestClient()
        self.client.run("profile new --detect default")

        p1 = "p1/version@user/channel"
        files = {'conanfile.py': self.conanfile.format(body="pass")}
        self.client.save(files)
        self.client.run("export . {}".format(p1))

        p2 = "p2/version@user/channel"
        files = {'conanfile.py': self.conanfile.format(body='requires = "{}"'.format(p1))}
        self.client.save(files)
        self.client.run("export . {}".format(p2))

        self.reference = "name/version@user/channel"
        files = {'conanfile.py': self.conanfile.format(body='requires = "{}"'.format(p2))}
        self.client.save(files)
        self.client.run("export . {}".format(self.reference))

    def test_basic(self):
        self.client.run("info {}".format(self.reference))

        # There are only a few types of lines:
        for line in str(self.client.out).splitlines():
            self.assertTrue(ConanFileReference.sep_pattern.match(line) or
                            re.match("^\s{4}[\w\s]+:\s.+$", line) or
                            line.lstrip() in ["Required by:", "Requires:"] or
                            (line.startswith(" "*8) and ConanFileReference.sep_pattern.match(line.rstrip())))

    def test_only(self):
        self.client.run("info {} -n None".format(self.reference))
        for line in str(self.client.out).splitlines():
            self.assertTrue(ConanFileReference.sep_pattern.match(line))

    def test_build_order(self):
        self.client.run("info {} --build-order=p1/version@user/channel".format(self.reference))
        list_refs = [it.strip('[] ') for it in str(self.client.out).split(',')]
        refs = [it2.strip() for it in list_refs for it2 in it.split(',')]
        self.assertTrue(len(refs) > 1)
        for it in refs:
            self.assertTrue(ConanFileReference.sep_pattern.match(it))
