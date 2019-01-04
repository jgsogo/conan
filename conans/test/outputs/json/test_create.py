# coding=utf-8

import textwrap
import os
import unittest
import json
from parameterized import parameterized

from conans.test.utils.tools import TestClient
from conans.client.tools.files import load


class JsonCreateOutputTest(unittest.TestCase):
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

    def test_basic(self):
        json_file = os.path.join(self.client.current_folder, 'out.json')
        self.client.run('create . {} --json="{}"'.format(self.reference, json_file))
        self.assertIn("JSON file created at '{}'".format(json_file), self.client.out)

        r = json.load(json_file)
        print(r.dumps())
        self.fail("AAA")
