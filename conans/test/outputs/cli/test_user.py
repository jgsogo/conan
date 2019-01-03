# coding=utf-8

import unittest

from mock import patch

from conans.client.conan_api import Conan
from conans.test.utils.tools import TestClient


class CLIUserOutputTest(unittest.TestCase):

    def setUp(self):
        self.client = TestClient()
        self.remote_names = ["name", "other"]
        for it in self.remote_names:
            self.client.run("remote add {n} https://{n}.url".format(n=it))

    def test_list(self):
        self.client.run("user")
        lines = ["Current user of remote '{}' set to: 'None' (anonymous)".format(it)
                 for it in self.remote_names]
        for line in str(self.client.out).splitlines():
            self.assertTrue(line in lines)

    def test_set_different_user(self):
        remote_name, prev_user, user = "remote_name", "prev_user", "user"
        with patch.object(Conan, "authenticate", return_value=[remote_name, prev_user, user]):
            self.client.run("user -p password -r {} username".format(self.remote_names[0]))
            self.assertEqual(str(self.client.out).rstrip('\n'),
                             "Changed user of remote '{}' from '{}' to '{}'".format(remote_name,
                                                                                    prev_user, user))

    def test_set_same_user(self):
        remote_name, prev_user, user = "remote_name", "user", "user"
        with patch.object(Conan, "authenticate", return_value=[remote_name, prev_user, user]):
            self.client.run("user -p password -r {} username".format(self.remote_names[0]))
            self.assertEqual(str(self.client.out).rstrip('\n'),
                             "User of remote '{}' is already '{}'".format(remote_name, user))

