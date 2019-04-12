# coding=utf-8

import textwrap
import unittest
from uuid import uuid1

from parameterized import parameterized

from conans.test.utils.tools import TestClient, create_local_git_repo, temp_folder


class EditablePackageTest(unittest.TestCase):

    conanfile = textwrap.dedent("""
        import os
        from conans import ConanFile, tools

        def get_version():
            git = tools.Git(os.path.dirname(__file__))
            try:
                return git.get_tag()
            except:
                return "no-git"

        class Lib(ConanFile):
            name = "name"
            version = get_version()

            def configure(self):
                self.output.info(">>>> version: {}".format(self.version))
    """)

    def setUp(self):
        self.url, _ = create_local_git_repo({"conanfile.py": self.conanfile})

        cache_directory = temp_folder(path_with_spaces=False)
        self.userA = TestClient(base_folder=cache_directory)
        self._userB = TestClient(base_folder=cache_directory, current_folder=self.url)

    def _create_new_version(self, version):
        self._userB.save({str(uuid1()): "random file"})
        self._userB.runner('git add . && git commit -am "new file"', cwd=self._userB.current_folder)
        self._userB.runner("git tag {}".format(version), cwd=self._userB.current_folder)
        self._userB.run('create . user/channel')
        self.assertIn("name/{v}@user/channel: >>>> version: {v}".format(v=version), self._userB.out)

    @parameterized.expand([("alias", True, ), ("no_alias", False, )])
    def test_use_case(self, _, alias_workaround):
        # Create version 1.0.0 in the cache
        version = "1.0.0"
        self._create_new_version(version=version)

        # User will consume it (and will put it into editable mode)
        self.userA.runner('git clone "{}" lib'.format(self.url), cwd=self.userA.current_folder)
        self.userA.run("editable add lib name/{v}@user/channel".format(v=version))

        self.userA.save({"conanfile.txt": "[requires]\nname/[>0.0.0]@user/channel"})
        self.userA.run("install .")
        self.assertIn("name/{v}@user/channel from user folder - Editable".format(v=version),
                      self.userA.out)

        if alias_workaround:
            # Create an alias with a huge version that links to my editable
            self.userA.run("alias name/99999@user/channel name/{v}@user/channel".format(v=version))

        # Create a new version
        version2 = "2.0.0"
        self._create_new_version(version=version2)

        # If user updates from the consumer it will no longer use the editable
        self.userA.run("install . --update")
        if not alias_workaround:
            self.assertIn("name/{v}@user/channel from local cache - No remote".format(v=version2),
                          self.userA.out)
        else:
            self.assertIn("name/{v}@user/channel from user folder - Editable".format(v=version),
                          self.userA.out)
