# coding=utf-8

import os
import textwrap

from conans.client.cache.remote_registry import Remotes
from conans.client.graph.graph import CONTEXT_HOST, CONTEXT_BUILD
from conans.client.recorder.action_recorder import ActionRecorder
from conans.model.graph_info import GraphInfo
from conans.model.options import OptionsValues
from conans.model.profile import Profile
from conans.model.ref import ConanFileReference
from conans.test.functional.graph.graph_manager_base import GraphManagerTest
from conans.test.utils.test_files import temp_folder
from conans.util.files import save


class BuildRequiresInProfileExample(GraphManagerTest):
    """ There is an application with a requirement 'lib', both of them need
        a tool called 'cmake' to build. This tool is defined in profile.

        All these requirements are declared in the profiles
    """

    cmake = textwrap.dedent("""
        from conans import ConanFile

        class CMake(ConanFile):
            name = "cmake"
            version = "testing"

            settings = "os"

            def build(self):
                self.output.info(">> settings.os:".format(self.settings.os))
    """)

    lib = textwrap.dedent("""
        from conans import ConanFile

        class Library(ConanFile):
            name = "protobuf"
            version = "testing"

            settings = "os"  # , "arch", "compiler", "build_type"

            def build(self):
                self.output.info(">> settings.os:".format(self.settings.os))
    """)

    application = textwrap.dedent("""
        from conans import ConanFile

        class Application(ConanFile):
            name = "application"
            version = "testing"

            settings = "os"
            requires = "lib/testing@user/channel"

            def build(self):
                self.output.info(">> settings.os:".format(self.settings.os))
    """)

    settings_yml = textwrap.dedent("""
        os:
            Host:
            Build:
    """)

    def setUp(self):
        super(BuildRequiresInProfileExample, self).setUp()
        self._cache_recipe("cmake/testing@user/channel", self.cmake)
        self._cache_recipe("lib/testing@user/channel", self.lib)
        self._cache_recipe("application/testing@user/channel", self.application)

        save(self.cache.settings_path, self.settings_yml)

    def _build_graph(self, profile_host, profile_build):
        path = temp_folder()
        path = os.path.join(path, "conanfile.txt")
        save(path, textwrap.dedent("""
            [requires]
            application/testing@user/channel
        """))

        ref = ConanFileReference(None, None, None, None, validate=False)
        graph_info = GraphInfo(profile_build=profile_build, profile_host=profile_host,
                               options=OptionsValues(), build_options=OptionsValues(), root_ref=ref)

        deps_graph, _ = self.manager.load_graph(path, create_reference=None, graph_info=graph_info,
                                                build_mode=[], check_updates=False, update=False,
                                                remotes=Remotes(), recorder=ActionRecorder())
        return deps_graph

    def test_crossbuilding(self):
        profile_host = Profile()
        profile_host.settings["os"] = "Host"
        profile_host.build_requires["*"] = [ConanFileReference.loads("cmake/testing@user/channel"), ]
        profile_host.process_settings(self.cache)

        profile_build = Profile()
        profile_build.settings["os"] = "Build"
        profile_build.process_settings(self.cache)

        deps_graph = self._build_graph(profile_host=profile_host, profile_build=profile_build)

        # Check HOST packages
        application = deps_graph.root.dependencies[0].dst
        self.assertEqual(len(application.dependencies), 2)
        self.assertEqual(application.conanfile.name, "application")
        self.assertEqual(application.build_context, CONTEXT_HOST)
        self.assertEqual(application.conanfile.settings.os, profile_host.settings['os'])
        self.assertEqual(str(application.conanfile.settings_host.os), profile_host.settings['os'])
        self.assertEqual(str(application.conanfile.settings_build.os), profile_build.settings['os'])

        lib_host = application.dependencies[0].dst
        self.assertEqual(lib_host.conanfile.name, "lib")
        self.assertEqual(lib_host.build_context, CONTEXT_HOST)
        self.assertEqual(lib_host.conanfile.settings.os, profile_host.settings['os'])
        self.assertEqual(str(lib_host.conanfile.settings_host.os), profile_host.settings['os'])
        self.assertEqual(str(lib_host.conanfile.settings_build.os), profile_build.settings['os'])

        # Check BUILD packages
        # TODO: As the default for the build_requires is HOST, here there is no context switch
        cmake_application_build = application.dependencies[1].dst
        self.assertEqual(cmake_application_build.conanfile.name, "cmake")
        self.assertEqual(cmake_application_build.build_context, CONTEXT_HOST)
        self.assertEqual(str(cmake_application_build.conanfile.settings.os),
                         profile_host.settings['os'])
        self.assertEqual(str(cmake_application_build.conanfile.settings_host.os), profile_host.settings['os'])
        self.assertEqual(str(cmake_application_build.conanfile.settings_build.os), profile_build.settings['os'])

        cmake_lib_build = lib_host.dependencies[0].dst
        self.assertNotEqual(cmake_application_build, cmake_lib_build)  # TODO: Different node/graph, bug or feature?
        self.assertEqual(cmake_lib_build.conanfile.name, "cmake")
        self.assertEqual(cmake_lib_build.build_context, CONTEXT_HOST)
        self.assertEqual(str(cmake_lib_build.conanfile.settings.os), profile_host.settings['os'])
        self.assertEqual(str(cmake_lib_build.conanfile.settings_host.os), profile_host.settings['os'])
        self.assertEqual(str(cmake_lib_build.conanfile.settings_build.os), profile_build.settings['os'])