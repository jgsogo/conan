# coding=utf-8

import os
import textwrap
import os

from collections import OrderedDict
from jinja2 import Template
import yaml

from conans.client.graph.graph import RECIPE_EDITABLE
from conans.errors import ConanException
from conans.model.editable_layout import get_editable_abs_path, EditableLayout
from conans.model.ref import ConanFileReference
from conans.util.files import load, save
from conans.client.cache.remote_registry import Remotes
from conans.model.workspaces.templates import conanworkspace_cmake_template


class PackageInsideWS(object):
    """ Packages included in the workspace """
    node = None

    def __init__(self, ref, data):
        self.ref = ConanFileReference.loads(ref, validate=True)
        self.data = data
        self.layout = EditableLayout(data.get('layout'))

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
    inner_packages = {}  # Packages in the workspace
    outter_packages = {}  # Packages out of the workspace

    def __init__(self, path, cache):
        self._cache = cache

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

        self.outter_packages = {it.ref: PackageOutsideWS(it.ref) for it in self.graph.nodes
                                if it.ref and  # There is a 'None' in the graph
                                it.ref not in inner_refs and
                                any([dep.ref in inner_refs for dep in it.public_closure])}

    def install(self, graph_manager, graph_info, recorder, install_folder):
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

        t = Template(conanworkspace_cmake_template, lstrip_blocks=True)
        conanworkspace_cmake = t.render(ws=self, ordered_packages=ordered_packages,
                                        build_folder=os.path.join(install_folder, 'build'))
        save(os.path.join(install_folder, 'conanworkspace.cmake'), conanworkspace_cmake)

        print("< WSCMake::install")

    def remove(self):
        # TODO: Remove from 'cache/editable_packages' those referring to this WS
        pass
