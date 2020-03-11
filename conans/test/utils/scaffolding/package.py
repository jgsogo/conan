import os
import platform
from collections import namedtuple, defaultdict

from conans.test.utils.scaffolding.templates import conanfile_template, \
    cmakelists_template, lib_cpp_template, lib_h_template, main_cpp_template
from conans.test.utils.test_files import temp_folder
from conans.util.files import mkdir
from conans.client.graph.graph import CONTEXT_BUILD, CONTEXT_HOST


class _Library:
    Requirement = namedtuple("Requirement", ["name", "target"])

    def __init__(self, name, package):
        self.package = package
        self.name = name
        self.target = name
        self._requires = set()

    def add_link_library(self, other, generator=None):
        assert isinstance(other, _Library), "type(other)={}".format(type(other))
        if other.package == self.package:
            # Generator makes no sense for library in the same package, it always be the naked target
            self._requires.add(self.Requirement(other.name, other.target))
        else:
            if generator == 'cmake':
                self._requires.add(self.Requirement(other.name, "CONAN_PKG::{}".format(other.package.name)))
            elif generator == 'cmake_find_package':
                self._requires.add(self.Requirement(other.name, "{pkg}::{pkg}".format(pkg=other.package.name)))
            else:
                raise RuntimeError("Generator '{}' not expected".format(generator))
            self.package._add_requires(other.package, generator=generator)

    def link_to_pkg(self, pkg):
        assert isinstance(pkg, Package), "type(other)={}".format(type(pkg))
        for library in pkg.libraries:
            self._requires.add(self.Requirement(library.name, "{pkg}::{pkg}".format(pkg=pkg.name)))

    def __str__(self):
        return self.name

    @property
    def requires(self):
        return sorted(self._requires, key=lambda u: u.name)

    def path_to_exec(self):
        # Get build folder from the layout
        return os.path.join(self.package.local_path, 'build', self.name)


class Package:
    def __init__(self, name, version="0.1", user="user", channel="testing"):
        self.name = name
        self.version = version
        self.user = user
        self.channel = channel
        self._requires = set()
        self._build_requires_build = set()
        self._build_requires_host = set()
        self._libraries = []
        self._executables = []
        self.shared = False

        self.generators = defaultdict(set)
        self.generators['cmake'] = set()  # Need to apply Conan magic to every package (handle fPIC)

        self._directory = None

    @property
    def local_path(self):
        return self._directory

    @property
    def ref(self):
        return "{}/{}@{}/{}".format(self.name, self.version, self.user, self.channel)

    @property
    def requires(self):
        return sorted(self._requires, key=lambda u: u.name)

    @property
    def build_requires_build(self):
        return sorted(self._build_requires_build, key=lambda u: u.name)

    @property
    def build_requires_host(self):
        return sorted(self._build_requires_host, key=lambda u: u.name)

    @property
    def libraries(self):
        return sorted(self._libraries, key=lambda u: u.name)

    @property
    def executables(self):
        return sorted(self._executables, key=lambda u: u.name)

    @property
    def layout_file(self):
        return os.path.join(self.local_path, 'layout')

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

    def add_build_requires(self, pkg, context=CONTEXT_BUILD, use_executable=False):
        assert isinstance(pkg, Package), "type(pgk)={}".format(type(pkg))
        if context == CONTEXT_BUILD:
            assert len(pkg.executables) > 0, "It makes no sense to add it without executables to use"
            self._build_requires_build.add(pkg)
        elif context == CONTEXT_HOST:
            self._build_requires_host.add(pkg)
            #self.generators["cmake_find_package"].add(pkg)
            #for lib in self.libraries:
            #    lib.link_to_pkg(pkg)

    @staticmethod
    def _render_template(tpl, output_filename, **context):
        context["windows"] = bool(platform.system() == "Windows")
        output = tpl.render(**context)
        with open(output_filename, 'w') as f:
            f.write(output)
        return output_filename

    def modify_cpp_message(self, message=None):
        context = {'package': self}
        if message:
            context["message"] = message

        for library in self._libraries:
            library_dir = os.path.join(self._directory, library.name)
            self._render_template(lib_h_template,
                                  os.path.join(library_dir, 'lib.h'),
                                  library=library, **context)
            self._render_template(lib_cpp_template,
                                  os.path.join(library_dir, 'lib.cpp'),
                                  library=library, **context)

    def modify_options(self, shared=False):
        self.shared = shared
        self._render_template(conanfile_template,
                              os.path.join(self._directory, 'conanfile.py'),
                              package=self)

    def render(self, output_folder=None):
        self._directory = output_folder or os.path.join(temp_folder(False), self.name)
        mkdir(self._directory)
        self._render_template(conanfile_template,
                              os.path.join(self._directory, 'conanfile.py'),
                              package=self)
        self._render_template(cmakelists_template,
                              os.path.join(self._directory, 'CMakeLists.txt'),
                              package=self)
        #self._render_template(layout_template, self.layout_file, package=self)
        for library in self._libraries:
            library_dir = os.path.join(self._directory, library.name)
            mkdir(library_dir)
            self._render_template(lib_h_template,
                                  os.path.join(library_dir, 'lib.h'),
                                  package=self, library=library)
            self._render_template(lib_cpp_template,
                                  os.path.join(library_dir, 'lib.cpp'),
                                  package=self, library=library)
        for executable in self._executables:
            executable_dir = os.path.join(self._directory, executable.name)
            mkdir(executable_dir)
            self._render_template(main_cpp_template,
                                  os.path.join(executable_dir, 'main.cpp'),
                                  package=self, executable=executable)
        return self._directory


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
    pkg1.render(os.path.join(output_folder, pkg1.name))

    # Package 2
    pkg2 = Package(name="pkg2")
    pkg2_lib1 = pkg2.add_library(name="pkg2_lib1")
    pkg2_lib1.add_link_library(lib1, generator='cmake')
    pkg2_exe1 = pkg2.add_executable(name="pkg2_exe1")
    pkg2_exe1.add_link_library(pkg2_lib1)
    pkg2.render(os.path.join(output_folder, pkg2.name))
