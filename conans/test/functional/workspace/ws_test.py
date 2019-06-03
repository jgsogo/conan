# coding=utf-8

import unittest
import textwrap
from jinja2 import Template
from conans.test.functional.workspace.scaffolding.package import Package
from conans.test.functional.workspace.scaffolding.ws_templates import workspace_yml_template
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import NO_SETTINGS_PACKAGE_ID, TestClient
import os
import platform


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
                   ^               ^
                   |               |
                   |    +------+   |
                   +----+ pkgG +---+
                        +------+

    """

    @staticmethod
    def _plain_package(client, pkg, lib_requires=None, add_executable=False):
        pkg = Package(name=pkg)
        #pkg_lib = pkg.add_library(name="{}_{}".format(pkg.name, "lib"))
        pkg_lib = pkg.add_library(name=pkg.name)  # TODO: Need Dani components
        if lib_requires:
            for item in lib_requires:
                library = item.libraries[0]  # There is only one lib per package (wait for Dani)
                pkg_lib.add_link_library(library, generator='cmake')
        if add_executable:
            exec = pkg.add_executable(name="{}_{}".format(pkg.name, "exe"))
            exec.add_link_library(pkg_lib)
        pkg_folder = pkg.render()
        client.run('create "{}" ws/testing'.format(os.path.join(pkg_folder, 'conanfile.py')))
        return pkg

    @classmethod
    def setUpClass(cls):
        super(WSTests, cls).setUpClass()
        cls.folder = temp_folder(path_with_spaces=False)
        cls.base_folder = temp_folder(path_with_spaces=False)

        t = TestClient(current_folder=cls.folder, base_folder=cls.base_folder)
        cls.libA = cls._plain_package(t, pkg="pkgA")
        cls.libD = cls._plain_package(t, pkg="pkgD")
        cls.libB = cls._plain_package(t, pkg="pkgB", lib_requires=[cls.libA, ])
        cls.libC = cls._plain_package(t, pkg="pkgC", lib_requires=[cls.libA, cls.libD])
        cls.libE = cls._plain_package(t, pkg="pkgE", lib_requires=[cls.libB, cls.libC])
        cls.libF = cls._plain_package(t, pkg="pkgF", lib_requires=[cls.libC])
        cls.libG = cls._plain_package(t, pkg="pkgG", lib_requires=[cls.libE, cls.libF], add_executable=True)

    def setUp(self):
        # Let's have one _local_ client per package
        self.pkgA = TestClient(self.base_folder, self.libA.local_path)
        self.pkgB = TestClient(self.base_folder, self.libB.local_path)
        self.pkgC = TestClient(self.base_folder, self.libC.local_path)
        self.pkgD = TestClient(self.base_folder, self.libD.local_path)
        self.pkgE = TestClient(self.base_folder, self.libE.local_path)
        self.pkgF = TestClient(self.base_folder, self.libF.local_path)
        self.pkgG = TestClient(self.base_folder, self.libG.local_path)

    def run_outside_ws(self):
        """ This function runs the full project without taking into account the ws,
            it should only take into account packages in the cache and those in
            editable mode
        """
        t = TestClient(base_folder=self.base_folder)
        t.save({'conanfile.txt': "[requires]\n{}".format(self.libG.ref)})
        t.run('install conanfile.txt -g virtualrunenv')
        for exec in self.libG.executables:
            if platform.system() != "Windows":
                t.run_command("bash -c 'source activate_run.sh && {}'".format(exec.name))
            else:
                t.run_command("activate_run.bat && {}.exe".format(exec.name))
            # print(t.out)
            # TODO: Check printed lines (messages)

    def test_created_projects(self):
        self.run_outside_ws()

    def test_workspace(self):
        editables = [self.libA, self.libB, self.libE, self.libG]
        root = self.libG

        t = TestClient(base_folder=self.base_folder)
        ws_yml = Template(workspace_yml_template).render(editables=editables, root=root)
        t.save({'ws.yml': ws_yml}, clean_first=True)
        t.run("workspace2 install ws.yml")
        print(t.out)

        print("*" * 20)
        t.run_command('cd build && cmake .. -DCMAKE_MODULE_PATH="{}"'.format(t.current_folder))
        print(t.out)
        print("*" * 20)

        print("*" * 20)
        t.run_command('cd build && cmake --build .')
        print(t.out)
        print("*" * 20)

        #t.save({'build/CMakeGraphVizOptions.cmake': textwrap.dedent(r"""
        #    set(GRAPHVIZ_EXTERNAL_LIBS TRUE)
        #    set(GRAPHVIZ_GENERATE_PER_TARGET FALSE)
        #    set(GRAPHVIZ_GENERATE_DEPENDERS FALSE)
        #    set(GRAPHVIZ_CUSTOM_TARGETS TRUE)
        #""")})
        # t.run_command('cd build && cmake --graphviz=test.dot .')
        #print(t.out)


        print("*" * 20)
        t.run_command('cd build && ./bin/pkgG_exe')
        print(t.out)
        print("*" * 20)

        self.libA.modify_cpp_message("Edited!!!")
        t.run_command('cd build && cmake --build .')
        t.run_command('cd build && ./bin/pkgG_exe')
        print(t.out)

        self.fail("test_workspace")
