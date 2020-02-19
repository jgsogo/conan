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
    client.run('create "{}" user/testing'.format(os.path.join(pkg_folder, 'conanfile.py')))
    return pkg


class ProtobufFullExampleTestCase(unittest.TestCase):
    """
        The objective is to generate an application that uses protobuf library. This application will
        build-require 'protoc' in order to generate the files for the messages and it will also private-require
        a library 'gtest' for testing (and 'protoc' too in order to generate the files we need to use
        in the test suite).

        +-------------+                         +--------------+
        |protobuf|host+<--+                     |protobuf|build|
        +------+------+   |                     +-------+------+
               ^          |                             ^
               |          |                             |
               |          |                             |
         +-----+-----+    |   +----------+       +------------+
         |protoc|host|    |   |gtest|host|       |protoc|build|
         +-----+-----+    |   +----------+       +------------+
               ^          |         ^                   ^
               +----------+---------+-------------------+
                                    |
                               +----+---+
                               |app|host|
                               +--------+
    """

    def setUp(self):
        self.t = TestClient(current_folder="/private/var/folders/fc/6mvcrc952dqcjfhl4c7c11ph0000gn/T/tmpwnt05atdconans/pathwithoutspaces")
        self.t.run("config set log.print_run_commands=True")
        self.gtest = _plain_package(self.t, pkg="gtest")
        self.protobuf = _plain_package(self.t, pkg="protobuf")
        self.protoc = _plain_package(self.t, pkg="protoc", requires=[self.protobuf, ], add_executable=True)
        self.app = _plain_package(self.t, pkg="app", requires=[self.protobuf, ], add_executable=True,
                                  build_requires=[(self.protoc, CONTEXT_HOST), (self.protoc, CONTEXT_BUILD),
                                                  (self.gtest, CONTEXT_HOST)])

    def test_protobuf_full_example(self):
        print(self.t.current_folder)

        self.t.run("profile new --detect --force profile_host")
        self.t.save({"profiles/profile_build": textwrap.dedent("""
            include(profile_host)
            
            [settings]
            build_type=Debug
        """)})

        #self.t.run("install {} --build".format(self.app.ref))
        #print(self.t.out)
        #print("*"*100)

        self.t.run("install {} --build --profile:host=profile_host --profile:build=profiles/profile_build".format(self.app.ref))
        print(self.t.out)

        self.fail("AAAA")
