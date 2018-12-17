# coding=utf-8

import textwrap
import unittest

from conans.test.utils.tools import TestClient
from conans.test.utils.tools import create_local_git_repo


class FixedCommitTest(unittest.TestCase):
    py_requires = textwrap.dedent("""\
        from conans import ConanFile
        
        def get_version_from_dpkg_changelog():
            return "1.2", "{commit}"
        
        class SharedData(ConanFile):
            name = "pyreq"
            version = "0.0"

        """)

    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, python_requires
        from conans.tools import load
        
        base = python_requires("pyreq/0.0@user/testing")
        
        
        class Package(ConanFile):        
            name = "coollib"
            url = "{url}"  # conanfile location: in repo
            version, commit = base.get_version_from_dpkg_changelog()
            
            scm = {{"type": "git",
                   "url": url,
                   "revision": commit}}
                   
            def source(self):
                content = load("sentinel.txt")
                self.output.info(content)
                assert content == ">> content <<"
        """)

    def test_fixed_commit(self):
        path, commit = create_local_git_repo(files={"sentinel.txt": ">> content <<"})

        t = TestClient()
        t.save({'conanfile.py': self.py_requires.format(commit=commit)})
        t.run("create . user/testing")

        t.save({'conanfile.py': self.conanfile.format(url=path)})
        t.run("create . user/testing")

        with t.chdir("build"):
            t.run("install ..")
        print(t.out)
        self.fail("AAA")


