# coding=utf-8

import textwrap
import unittest

from parameterized import parameterized

from conans.test.utils.tools import TestClient


class CLIGetOutputTest(unittest.TestCase):

    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        
        class Lib(ConanFile):
            pass
        """)

    def setUp(self):
        self.client = TestClient()
        files = {'conanfile.py': self.conanfile}
        self.client.save(files)

        self.reference = "name/version@user/channel"
        self.client.run("create . {}".format(self.reference))

    @parameterized.expand([(True, ), (False, )])
    def test_get_file(self, use_raw):
        raw = ' --raw' if use_raw else ''

        self.client.run("get {}{}".format(self.reference, raw))
        output = str(self.client.out)[:-1]  # There is an extra '\n' in the output
        self.assertEqual(output, self.conanfile)
