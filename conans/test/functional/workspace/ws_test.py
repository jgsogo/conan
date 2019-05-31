# coding=utf-8

import unittest

from conans.test.functional.workspace.scaffolding.package import Package
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import NO_SETTINGS_PACKAGE_ID, TestClient
import os


class WSTests(unittest.TestCase):
    """
        Dependency graph: packages on lower level depends on those in the upper one.

                +------+      +------+
                | pkgA |      | pkgD |
                +--+---+      +---+--+
                   ^              ^
        +------+   |   +------+   |
        | pkgB +---+---+ pkgC +---+
        +--+---+       +---+--+
           ^               ^
           |               |
           |    +------+   |  +------+
           +----+ pkgE +---+--+ pkgF |
                +------+      +------+

    """

    @staticmethod
    def _plain_package(client, pkg, lib_requires=None, add_executable=False):
        pkg = Package(name=pkg)
        pkg_lib = pkg.add_library(name="{}_{}".format(pkg.name, "lib"))
        if lib_requires:
            for item in lib_requires:
                library = item.libraries[0]  # There is only one lib per package (wait for Dani)
                pkg_lib.add_link_library(library, generator='cmake')
        if add_executable:
            exec = pkg.add_executable(name="{}_{}".format(pkg.name, "exe"))
            exec.add_link_library(pkg_lib)
        pkg_folder = pkg.render(client.current_folder)
        client.run('export "{}" ws/testing'.format(os.path.join(pkg_folder, 'conanfile.py')))
        return pkg

    @classmethod
    def setUpClass(cls):
        super(WSTests, cls).setUpClass()
        cls.folder = temp_folder(path_with_spaces=True)
        cls.base_folder = temp_folder(path_with_spaces=True)

        t = TestClient(current_folder=cls.folder, base_folder=cls.base_folder)
        cls.libA = cls._plain_package(t, pkg="pkgA")
        cls.libD = cls._plain_package(t, pkg="pkgD")
        cls.libB = cls._plain_package(t, pkg="pkgB", lib_requires=[cls.libA, ])
        cls.libC = cls._plain_package(t, pkg="pkgC", lib_requires=[cls.libA, cls.libD])
        cls.libE = cls._plain_package(t, pkg="pkgE", lib_requires=[cls.libB, cls.libC], add_executable=True)
        cls.libF = cls._plain_package(t, pkg="pkgF", lib_requires=[cls.libC], add_executable=True)

    def setUp(self):
        # Let's have one _local_ client per package
        self.pkgA = TestClient(self.base_folder, os.path.join(self.folder, self.libA.name))
        self.pkgB = TestClient(self.base_folder, os.path.join(self.folder, self.libB.name))
        self.pkgC = TestClient(self.base_folder, os.path.join(self.folder, self.libC.name))
        self.pkgD = TestClient(self.base_folder, os.path.join(self.folder, self.libD.name))
        self.pkgE = TestClient(self.base_folder, os.path.join(self.folder, self.libE.name))
        self.pkgF = TestClient(self.base_folder, os.path.join(self.folder, self.libF.name))

        # Working client
        self.t = TestClient(base_folder=self.base_folder)

    def test_somthing(self):
        # We can build in the cache
        self.t.run('install "{}" --build={}'.format(self.libA.ref, self.libA.name))
        print(self.t.out)

        # And we can get packages locally
        self.pkgC.run('info .')
        print(self.pkgC.out)

        self.fail("AAA")
