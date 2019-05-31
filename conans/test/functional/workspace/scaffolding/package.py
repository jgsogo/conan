# coding=utf-8

import os
from collections import namedtuple, defaultdict

from jinja2 import Template

from conans.test.functional.workspace.scaffolding.templates import conanfile_template, \
    cmakelists_template, lib_cpp_template, lib_h_template, main_cpp_template


class _Library:
    Requirement = namedtuple("Requirement", ["name", "target"])

    def __init__(self, name, package):
        self.package = package
        self.name = name
        self.target = name
        self.requires = set()

    def add_link_library(self, other, generator=None):
        assert isinstance(other, _Library), "type(other)={}".format(type(other))
        if other.package == self.package:
            # Generator makes no sense for the same package, it always be the naked target
            self.requires.add(self.Requirement(other.name, other.target))
        else:
            if generator == 'cmake':
                self.requires.add(self.Requirement(other.name, "CONAN_PKG::{}".format(other.package.name)))
            elif generator == 'cmake_find_packages':
                self.requires.add(
                    self.Requirement(other.name, "{pkg}::{pkg}".format(pkg=other.package.name)))
            else:
                raise RuntimeError("Generator '{}' not expected".format(generator))
            self.package._add_requires(other.package, generator=generator)

    def __str__(self):
        return self.name


class Package:
    def __init__(self, name, version="0.1", user="ws", channel="testing"):
        self.name = name
        self.version = version
        self.user = user
        self.channel = channel
        self._requires = set()
        self._libraries = []
        self._executables = []
        self.shared = False

        # About generators
        self.generators = defaultdict(set)

    @property
    def ref(self):
        return "{}/{}@{}/{}".format(self.name, self.version, self.user, self.channel)

    @property
    def requires(self):
        return self._requires

    @property
    def libraries(self):
        return self._libraries

    @property
    def executables(self):
        return self._executables

    def add_library(self, **data):
        lib = _Library(package=self, **data)
        self._libraries.append(lib)
        return lib

    def add_executable(self, **data):
        exe = _Library(package=self, **data)
        self._executables.append(exe)
        return exe

    def _add_requires(self, requirement, generator):
        assert isinstance(requirement, Package), "type(requirement)={}".format(type(requirement))
        self._requires.add(requirement)
        self.generators[generator].add(requirement)

    @staticmethod
    def _render_template(template_content, output_filename, **context):
        t = Template(template_content)
        output = t.render(**context)
        with open(output_filename, 'w') as f:
            f.write(output)
        return output_filename

    def render(self, output_folder):
        package_dir = os.path.join(output_folder, self.name)
        os.makedirs(package_dir)
        self._render_template(conanfile_template,
                              os.path.join(package_dir, 'conanfile.py'),
                              package=self)
        self._render_template(cmakelists_template,
                              os.path.join(package_dir, 'CMakeLists.txt'),
                              package=self)
        for library in self._libraries:
            library_dir = os.path.join(package_dir, library.name)
            os.makedirs(library_dir)
            self._render_template(lib_h_template,
                                  os.path.join(library_dir, 'lib.h'),
                                  package=self, library=library)
            self._render_template(lib_cpp_template,
                                  os.path.join(library_dir, 'lib.cpp'),
                                  package=self, library=library)
        for executable in self._executables:
            executable_dir = os.path.join(package_dir, executable.name)
            os.makedirs(executable_dir, exist_ok=True)
            self._render_template(main_cpp_template,
                                  os.path.join(executable_dir, 'main.cpp'),
                                  package=self, executable=executable)
        return package_dir


if __name__ == "__main__":
    # Clean output folder
    import shutil
    me = os.path.dirname(__file__)
    output_folder = os.path.join(me, "_tmp")
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    # Package 1
    pkg1 = Package(name="pkg1")
    lib1 = pkg1.add_library(name="lib1")
    lib2 = pkg1.add_library(name="lib2")
    lib2.add_link_library(lib1)
    exe1 = pkg1.add_executable(name="exe1")
    exe1.add_link_library(lib1)
    pkg1.render(output_folder)

    # Package 2
    pkg2 = Package(name="pkg2")
    pkg2_lib1 = pkg2.add_library(name="pkg2_lib1")
    pkg2_lib1.add_link_library(lib1, generator='cmake')
    pkg2_exe1 = pkg2.add_executable(name="pkg2_exe1")
    pkg2_exe1.add_link_library(pkg2_lib1)
    pkg2.render(output_folder)

