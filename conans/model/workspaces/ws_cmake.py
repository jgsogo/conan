# coding=utf-8

import os
import textwrap
import os

from collections import OrderedDict
from jinja2 import Template
import yaml
from conans.client.installer import BinaryInstaller
from conans.client.generators import write_generators

from conans.client.graph.graph import RECIPE_EDITABLE
from conans.errors import ConanException
from conans.model.editable_layout import get_editable_abs_path, EditableLayout
from conans.model.ref import ConanFileReference
from conans.util.files import load, save
from conans.client.cache.remote_registry import Remotes
from conans.model.workspaces.templates import conanworkspace_cmake_template, cmakelists_template


class PackageInsideWS(object):
    """ Packages included in the workspace """
    node = None

    def __init__(self, ref, data):
        self.ref = ConanFileReference.loads(ref, validate=True)
        self.data = data
        self.layout = data.get('layout')

    def __str__(self):
        return self.ref.full_repr()

    @property
    def target(self):
        return self.ref.name

    @property
    def source_folder(self):
        return self.data.get('path')


class PackageOutsideWS(object):
    """ Package NOT included in the workspace """
    node = None

    def __init__(self, ref):
        self.ref = ref

    def __str__(self):
        return self.ref.full_repr()

    @property
    def target(self):
        return self.ref.name


class WSCMake(object):
    default_filename = "conanws.yml"
    _generator = 'cmake'
    inner_packages = {}  # Packages in the workspace (editable ones)
    outter_packages = {}  # Packages out of the workspace (depends on one 'inner_package')
    fixed_packages = []  # Packages out of workspace

    def __init__(self, path, cache, output):
        self._cache = cache
        self._output = output

        if not os.path.isfile(path):
            path = os.path.join(path, self.default_filename)
        self._ws_file = path

        try:
            yml = yaml.safe_load(load(path))

            # Unwrap editables
            editables = yml.pop("editables", {})
            for ref, data in editables.items():
                pck = PackageInsideWS(ref, data)
                self.inner_packages[pck.ref] = pck
        except IOError:
            raise ConanException("Couldn't load workspace file in %s" % path)
        except Exception as e:
            raise ConanException("There was an error parsing %s: %s" % (path, str(e)))

        self._validate()

    def _validate(self):
        for _, pkg in self.inner_packages.items():
            if not os.path.exists(os.path.join(pkg.source_folder, 'CMakeLists.txt')):
                raise ConanException("Source folder of pkg '{}' doesn't contain a"
                                     " 'CMakeLists.txt' file".format(pkg.ref))

    def _build_graph(self, graph_manager, graph_info, recorder):
        # TODO: Ensure version ranges are resolved to packages declared in WS

        # TODO: Load temporal editable packages
        as_editable = {it.ref: {'path': it.source_folder, 'layout': it.layout} for _, it in self.inner_packages.items()}
        self._cache.editable_packages.override(as_editable)

        # TODO: Build the graph
        inner_refs = list(self.inner_packages.keys())
        self.graph, _ = graph_manager.load_graph(inner_refs, create_reference=None,
                                                 graph_info=graph_info, build_mode=["never", ],
                                                 check_updates=False, update=False,
                                                 remotes=Remotes(), recorder=recorder)

        #self.outter_packages = {it.ref: PackageOutsideWS(it.ref) for it in self.graph.nodes
        #                        if it.ref and  # There is a 'None' in the graph
        #                        it.ref not in inner_refs and
        #                        any([dep.ref in inner_refs for dep in it.public_closure])}

        for it in self.graph.nodes:
            if it.ref and it.ref not in inner_refs:
                self.fixed_packages.append(it.ref)
                if any([dep.ref in inner_refs for dep in it.public_closure]):
                    self.outter_packages[it.ref] = PackageOutsideWS(it.ref)

        print("inner packages:")
        for it in self.inner_packages:
            print(" - {}".format(it))
        print("outter packages:")
        for it in self.outter_packages:
            print(" - {}".format(it))
        print("fixed packages:")
        for it in self.fixed_packages:
            print(" - {}".format(it))

    def install(self, graph_manager, graph_info, recorder, install_folder, conan_api):
        print("> WSCMake::install")
        self._build_graph(graph_manager, graph_info, recorder)

        ordered_packages = []
        for node in self.graph.ordered_iterate():
            inner = self.inner_packages.get(node.ref, None)
            outter = self.outter_packages.get(node.ref, None)
            pkg_wrapper = inner or outter
            if pkg_wrapper:
                pkg_wrapper.deps = [it for it in self.inner_packages.values() if it.ref in [pc.ref for pc in node.public_closure]] + \
                                   [it for it in self.outter_packages.values() if it.ref in [pc.ref for pc in node.public_closure]]
                ordered_packages.append(pkg_wrapper)

        build_folder = os.path.join(install_folder, 'build')
        t = Template(conanworkspace_cmake_template)
        conanworkspace_cmake = t.render(ws=self, ordered_packages=ordered_packages,
                                        build_folder=build_folder)
        save(os.path.join(install_folder, 'conanworkspace.cmake'), conanworkspace_cmake)

        t = Template(cmakelists_template)
        cmakelists_txt = t.render(ws=self)
        save(os.path.join(install_folder, 'CMakeLists.txt'), cmakelists_txt)

        # For the inner packages, create fake files
        for ref in self.inner_packages.keys():
            save(os.path.join(build_folder, ref.name, 'conanbuildinfo.cmake'), "# Empty file")

        # TODO: I can generate 'cmake' and 'cmake_find_package' files for all outter packages (and include/find all of them)
        workspace_txt = os.path.join(install_folder, 'workspace.txt')
        save(workspace_txt,
             "[requires]\n{}\n\n[generators]\ncmake_find_package".format('\n'.join(map(str, self.fixed_packages))))
        conan_api.install(workspace_txt, install_folder=install_folder)
        # TODO: How can I create only those finds for packages listed?

        # TODO: I need a 'conanbuildinfo.cmake' (or a toolchain file) to do the magic
        workspace_empty = os.path.join(install_folder, 'workspace_empty.txt')
        save(workspace_empty, "[requires]\n[generators]\ncmake")
        conan_api.install(workspace_empty, install_folder=install_folder)

        #write_generators(conanfile, install_folder, self._output)

        print("< WSCMake::install")

    def remove(self):
        # TODO: Remove from 'cache/editable_packages' those referring to this WS
        pass
