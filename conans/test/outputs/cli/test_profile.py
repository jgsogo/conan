# coding=utf-8

import os
import unittest

from six.moves.configparser import ConfigParser

from conans.test.utils.tools import TestClient
from conans.util.files import save


class CLIProfileOutputTest(unittest.TestCase):

    def setUp(self):
        self.client = TestClient()
        self.client.run("profile new --detect default")
        self.test_profile = os.path.join(self.client.client_cache.profiles_path, 'test')
        save(self.test_profile, "include(default)\n\n[settings]\n\nbuild_type=test-profile")

    def test_list(self):
        self.client.run("profile list")
        self.assertEqual(str(self.client.out).rstrip('\n'), "default\ntest")

    def test_show(self):
        self.client.run("profile show test")
        lines = str(self.client.out).splitlines()
        self.assertEqual(lines[0], "Configuration for profile test:")
        try:
            cfg = ConfigParser()
            cfg.read_string('\n'.join(lines[1:]))
        except:
            self.fail("Profile was expecxted to be a parseable .cfg file-like")

    def test_get(self):
        self.client.run("profile get settings.build_type test")
        self.assertEqual(str(self.client.out).rstrip('\n'), "test-profile")

