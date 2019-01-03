# coding=utf-8

import unittest

from mock import patch
import textwrap

from conans.client.conan_api import Conan
from conans.test.utils.tools import TestClient
from conans.model.ref import ConanFileReference, PackageReference


class CLIRemoteOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        
        class Lib(ConanFile):
            pass
    """)

    def setUp(self):
        self.client = TestClient()
        self.remote_names = ["name", "other"]
        for it in self.remote_names:
            self.client.run("remote add {n} https://{n}.url".format(n=it))

        # Add some packages to remotes
        for it in ["pk1", "pk2"]:
            self.client.save({'conanfile.py': self.conanfile})
            self.client.run("export . {}/version@user/channel".format(it))

    def test_list(self):
        self.client.run("remote list")
        lines = ["{n}: https://{n}.url [Verify SSL: True]".format(n=it) for it in self.remote_names]
        for line in str(self.client.out).splitlines():
            self.assertTrue(line in lines)

    def test_list_raw(self):
        self.client.run("remote list --raw")
        lines = ["{n} https://{n}.url True".format(n=it) for it in self.remote_names]
        for line in str(self.client.out).splitlines():
            self.assertTrue(line in lines)

    def test_list_ref(self):
        refs = {"pk1/version@user/channel": "remote1", "pk2/version@user/channel": "remote2", }
        with patch.object(Conan, "remote_list_ref", return_value=refs):
            self.client.run("remote list_ref")
            lines = str(self.client.out).splitlines()
            self.assertTrue(len(lines))
            for line in lines:
                ref, remote = line.split(':')
                self.assertTrue(ConanFileReference.sep_pattern.match(ref))

    def test_list_pref(self):
        prefs = {"opencv/4.0.0@conan/stable:8cb67aa8aca987bb2ebfa7814003995d7aaf8388": "remote1",
                 "openexr/2.3.0@conan/stable:d38d40c1236cab14590c629534a35032d00adac2": "remote2", }
        with patch.object(Conan, "remote_list_pref", return_value=prefs):
            self.client.run("remote list_pref opencv/4.0.0@conan/stable")
            lines = str(self.client.out).splitlines()
            self.assertTrue(len(lines))
            for line in lines:
                pref, remote = line.rsplit(':', 1)
                try:
                    PackageReference.loads(pref, validate=True)
                except:
                    self.fail("Invalid format in command 'conan remote list_pref <ref>' output")
