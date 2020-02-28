import unittest
from conans.test.utils.tools import TestClient, NO_SETTINGS_PACKAGE_ID, GenConanfile
import os
import re
import textwrap
import unittest

from conans.model.editable_layout import LAYOUTS_FOLDER
from conans.model.ref import ConanFileReference
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import TestClient, GenConanfile
from conans.util.files import save_files, save
from jinja2 import Template
from conans.client.graph.graph import DepsGraph, Node, RECIPE_EDITABLE, CONTEXT_HOST, \
    CONTEXT_BUILD

from conans.test.utils.scaffolding.package import Package


def _plain_package(client, pkg, requires=None, build_requires=None, add_executable=False, shared=False, version="0.1"):
    """ Create a package with only one library that links and uses libraries declared
        in 'lib_requires'. Optionally it adds an executable to the package (the
        executable will link to the library in the same package)
    """
    pkg = Package(name=pkg, version=version)
    pkg_lib = pkg.add_library(name=pkg.name)  # TODO: Include components (@danimtb)
    if requires:
        for item in requires:
            library = item.libraries[0]  # There is only one lib per package (wait for Dani)
            pkg_lib.add_link_library(library, generator='cmake_find_package')
    if build_requires:
        for item, context in build_requires:
            pkg.add_build_requires(item, context=context, use_executable=bool(len(pkg.executables)))
    if add_executable:
        executable = pkg.add_executable(name="{}_{}".format(pkg.name, "exe"))
        executable.add_link_library(pkg_lib)
    pkg.shared = shared
    pkg_folder = pkg.render(output_folder=os.path.join(client.current_folder, pkg.name))
    client.run('export "{}" user/testing'.format(os.path.join(pkg_folder, 'conanfile.py')))
    return pkg


class ProtobufFullExampleTestCase(unittest.TestCase):
    """
        The objective is to generate an application that uses protobuf library, this application will
        build-require 'protoc' in order to generate the files for the messages. The application itself
        will use CMake as a build-require.

        For the test-suite, it needs several tools and libs: an executable 'testtool', the 'protoc' utility
        to generate some messages for the test suite and the 'gtest' library.

         +------------+      +-------------+                         +--------------+      +--------------+
         |testlib|host|      |protobuf|host+<--+                     |protobuf|build|      |cmakelib|build|
         +-----+------+      +------+------+   |                     +-------+------+      +------+-------+
               ^                    ^          |                             ^                    ^
               |                    |          |                             |                    |
               |                    |          |                             |                    |
        +------+------+       +-----+-----+    |   +----------+       +------------+        +-----------+
        |testtool|host|       |protoc|host|    |   |gtest|host|       |protoc|build|        |cmake|build|
        +------+------+       +-----+-----+    |   +----------+       +------------+        +-----------+
               ^                    ^          |         ^                   ^                    ^
               +--------------------+----------+-----------------------------+--------------------+
                                                         |
                                                    +----+---+
                                                    |app|host|
                                                    +--------+
    """

    def setUp(self):
        #self.t = TestClient(current_folder="/private/var/folders/fc/6mvcrc952dqcjfhl4c7c11ph0000gn/T/tmpbcfoylyfconans/path with spaces")
        self.t = TestClient(current_folder="/tmp/tmpgi21hvxwconans/path with spaces")
        self.t.run("config set log.print_run_commands=True")
        #self.gtest = _plain_package(self.t, pkg="gtest")
        self.protobuf = _plain_package(self.t, pkg="protobuf")
        self.protoc = _plain_package(self.t, pkg="protoc", requires=[self.protobuf, ], add_executable=True)
        self.testlib = _plain_package(self.t, pkg="testlib")
        self.testtool = _plain_package(self.t, pkg="testtool", requires=[self.testlib], add_executable=True)
        self.cmakelib = _plain_package(self.t, pkg="cmakelib")
        self.cmake = _plain_package(self.t, pkg="cmake", requires=[self.cmakelib], add_executable=True)
        self.app = _plain_package(self.t, pkg="app", requires=[self.protobuf, ], add_executable=True,
                                  build_requires=[(self.testtool, CONTEXT_HOST), (self.protoc, CONTEXT_HOST),  # Tools for testing
                                                  (self.protoc, CONTEXT_BUILD), (self.cmake, CONTEXT_BUILD),  # Tools to build
                                                  #(self.gtest, CONTEXT_HOST) # Library for testing (somehow private)
                                                  ])

    def test_protobuf_full_example(self):
        print(self.t.current_folder)

        self.t.run("profile new --detect --force default")
        self.t.save({"profiles/profile_host": textwrap.dedent("""
            include(default)

            [settings]
            build_type=Release
            
            [options]
            *:shared=True
        """)})
        self.t.save({"profiles/profile_build": textwrap.dedent("""
            include(default)

            [settings]
            build_type=Debug

            [options]
            *:shared=True
        """)})

        # Build the application for the 'host_profile' using some tools that would be available to run
        #   in the 'build_profile'.
        self.t.run("install {} --build -g virtualrunenv --profile:host=profiles/profile_host --profile:build=profiles/profile_build".format(self.app.ref))

        # - Make sure we use the tools from the build_context:
        self.assertIn("app/0.1@user/testing: >>>> cmake | cmake_exe", self.t.out)
        self.assertIn("	> cmakelib (Linux|x86_64|gcc|Debug): default (shared!)", self.t.out)
        self.assertIn("app/0.1@user/testing: >>>> protoc | protoc_exe", self.t.out)
        self.assertIn("	> protobuf (Linux|x86_64|gcc|Debug): default (shared!)", self.t.out)

        # - Generator 'virtualrunenv' as implemented now propagates nothing for the xbuild implementation
        #self.t.run("install {} -g virtualrunenv --profile:host=profiles/profile_host --profile:build=profiles/profile_build".format(self.app.ref))
        content = self.t.load("environment_run.sh.env")
        self.assertIn("DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH+:$DYLD_LIBRARY_PATH}", content)
        self.assertIn("LD_LIBRARY_PATH=${LD_LIBRARY_PATH+:$LD_LIBRARY_PATH}", content)
        self.assertIn("PATH=${PATH+:$PATH}", content)

        # - If we want the path to the application, we need to use the old behavior without profile_build:
        self.t.run("install {} -g virtualrunenv --profile:host=profiles/profile_host".format(self.app.ref))
        self.t.run_command("bash -c 'source activate_run.sh && app_exe'")
        self.assertIn("> app_exe (Linux|x86_64|gcc|Release): default", self.t.out)
        self.assertIn("	> protobuf (Linux|x86_64|gcc|Release): default (shared!)", self.t.out)

        # - Or use a new generator that will propagate the app we are installing (it might not run in this 'build_machine', but it is user requested)
        self.t.run("install {} -g virtualrunenv2 --profile:host=profiles/profile_host --profile:build=profiles/profile_build".format(self.app.ref))
        self.t.run_command("bash -c 'source activate_run.sh && app_exe'")
        self.assertIn("> app_exe (Linux|x86_64|gcc|Release): default", self.t.out)
        self.assertIn("	> protobuf (Linux|x86_64|gcc|Release): default (shared!)", self.t.out)
