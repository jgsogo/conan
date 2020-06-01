import os
import platform
import textwrap
import unittest

from jinja2 import Template
from parameterized import parameterized

from conans.model.ref import ConanFileReference
from conans.test.utils.tools import TestClient


class LinkOrderTest(unittest.TestCase):
    """ Check that the link order of libraries is preserved when using CMake generators
        https://github.com/conan-io/conan/issues/6280
    """

    conanfile = Template(textwrap.dedent("""
        from conans import ConanFile

        class Recipe(ConanFile):
            name = "{{ref.name}}"
            version = "{{ref.version}}"

            {% if requires %}
            requires =
                {%- for req in requires -%}
                "{{ req }}"{% if not loop.last %}, {% endif %}
                {%- endfor -%}
            {% endif %}

            def build(self):
                {% for cmp, data in components.items() %}
                with open("lib{{ cmp }}.a", "w+") as f:
                    f.write("fake library content")
                with open("{{ cmp }}.lib", "w+") as f:
                    f.write("fake library content")

                    {% if 'libs_extra' in data %}
                        {% for it in data['libs_extra'] %}
                with open("lib{{ cmp }}{{ it }}.a", "w+") as f:
                    f.write("fake library content")
                with open("{{ cmp }}{{ it }}.lib", "w+") as f:
                    f.write("fake library content")
                        {% endfor %}
                    {% endif %}
                {% endfor %}

            def package(self):
                self.copy("*.a", dst="lib")
                self.copy("*.lib", dst="lib")

            def package_info(self):
                {% for cmp, data in components.items() %}

                # Libraries
                self.cpp_info.components["{{ cmp }}"].libs = ["{{ cmp }}"]
                {% for it in data.get('libs_extra', []) %}
                self.cpp_info.components["{{ cmp }}"].libs.append("{{ cmp }}{{ it }}")
                {% endfor %}
                {% for it in data.get('libs_system', []) %}
                self.cpp_info.components["{{ cmp }}"].libs.append("{{ it }}")
                {% endfor %}

                # Requires
                {% if requires and 'requires' in data %}
                self.cpp_info.components["{{ cmp }}"].requires = [
                    {%- for require in data['requires'] -%}
                    {%- if "%%require%%" in require -%}
                    {%- for rq in requires -%}
                    "{{ require.replace("%%require%%", rq.name) }}"{% if not loop.last %}, {% endif %}
                    {%- endfor -%}
                    {%- else -%}
                    "{{ require }}"{% if not loop.last %}, {% endif %}
                    {%- endif -%}
                    {%- endfor -%}]
                {% endif %}

                # System libs
                {% if 'system_libs' in data %}
                self.cpp_info.components["{{ cmp }}"].system_libs = [
                    {%- for it in data['system_libs'] -%}
                    "{{ it }}"{% if not loop.last %}, {% endif %}
                    {%- endfor -%}]
                {% endif %}

                # Frameworks
                {% if 'frameworks' in data %}
                self.cpp_info.components["{{ cmp }}"].frameworks.extend([
                    {%- for it in data['frameworks'] -%}
                    "{{ it }}"{% if not loop.last %}, {% endif %}
                    {%- endfor -%}])
                {% endif %}

                {% endfor %}
    """))


    main_cpp = textwrap.dedent("""
        int main() {return 0;}
    """)

    @classmethod
    def setUpClass(cls):
        libZ_ref = ConanFileReference.loads("libZ/version")
        libH2_ref = ConanFileReference.loads("header2/version")
        libH_ref = ConanFileReference.loads("header/version")
        libA_ref = ConanFileReference.loads("libA/version")
        libB_ref = ConanFileReference.loads("libB/version")
        libC_ref = ConanFileReference.loads("libC/version")
        libD_ref = ConanFileReference.loads("libD/version")

        t = TestClient(path_with_spaces=False)
        t.current_folder = '/private/var/folders/fc/6mvcrc952dqcjfhl4c7c11ph0000gn/T/tmpezu38k36conans/pathwithoutspaces'
        cls._cache_folder = t.cache_folder
        components = {
            'cmp1': {
                'libs_extra': ["1"],
                'libs_system': ["system_assumed"],
                'system_libs': ["system_lib"],
                'frameworks': ["Carbon"],
            },
            'cmp2': {
                'libs_extra': ["1"],
                'libs_system': ["system_assumed"],
                'system_libs': ["system_lib"],
                'frameworks': ["Carbon"],
                'requires': ["cmp1", "%%require%%::cmp1"]
            },
            'cmp3': {
                'libs_extra': ["1"],
                'libs_system': ["system_assumed"],
                'system_libs': ["system_lib"],
                'frameworks': ["Carbon"],
                'requires': ["cmp1", "%%require%%::%%require%%"]
            }
        }

        t.save({
            'libZ/conanfile.py': cls.conanfile.render(
                ref=libZ_ref,
                components=components),
            'libH2/conanfile.py': cls.conanfile.render(
                ref=libH2_ref,
                components=components),
            'libH/conanfile.py': cls.conanfile.render(
                ref=libH_ref,
                requires=[libH2_ref, libZ_ref],
                components=components),
            'libA/conanfile.py': cls.conanfile.render(
                ref=libA_ref,
                requires=[libH_ref],
                components=components),
            'libB/conanfile.py': cls.conanfile.render(
                ref=libB_ref,
                requires=[libA_ref],
                components=components),
            'libC/conanfile.py': cls.conanfile.render(
                ref=libC_ref,
                requires=[libA_ref],
                components=components),
            'libD/conanfile.py': cls.conanfile.render(
                ref=libD_ref,
                requires=[libB_ref, libC_ref],
                components=components),
        })

        # Create all of them
        t.run("create libZ")
        t.run("create libH2")
        t.run("create libH")
        t.run("create libA")
        t.run("create libB")
        t.run("create libC")
        t.run("create libD")

    def _validate_link_order(self, libs):
        self.fail("Validate link order not implemented for this test")
        # Check that all the libraries are there:
        self.assertEqual(len(libs), 19 if platform.system() == "Darwin" else
                         16 if platform.system() == "Linux" else 26,
                         msg="Unexpected number of libs ({}):"
                             " '{}'".format(len(libs), "', '".join(libs)))
        # - Regular libs
        ext = ".lib" if platform.system() == "Windows" else ".a"
        prefix = "" if platform.system() == "Windows" else "lib"
        expected_libs = {prefix + it + ext for it in ['libD', 'D2', 'libB', 'B2', 'libC', 'C2',
                                                      'libA', 'A2', 'libZ', 'Z2']}
        # - System libs
        ext_system = ".lib" if platform.system() == "Windows" else ""
        expected_libs.update([it + ext_system for it in ['header_system_assumed',
                                                         'header_system_lib',
                                                         'header2_system_assumed',
                                                         'header2_system_lib',
                                                         'system_assumed',
                                                         'system_lib']])
        # - Add MacOS frameworks
        if platform.system() == "Darwin":
            expected_libs.update(['CoreAudio', 'Security', 'Carbon'])
        # - Add Windows libs
        if platform.system() == "Windows":
            expected_libs.update(['kernel32.lib', 'user32.lib', 'gdi32.lib', 'winspool.lib',
                                  'shell32.lib', 'ole32.lib', 'oleaut32.lib', 'uuid.lib',
                                  'comdlg32.lib', 'advapi32.lib'])
        self.assertSetEqual(set(libs), expected_libs)

        # These are the first libraries and order is mandatory
        mandatory_1 = [prefix + it + ext for it in ['libD', 'D2', 'libB', 'B2', 'libC',
                                                    'C2', 'libA', 'A2', ]]
        self.assertListEqual(mandatory_1, libs[:len(mandatory_1)])

        # Then, libZ ones must be before system libraries that are consuming
        self.assertLess(libs.index(prefix + 'libZ' + ext),
                        min(libs.index('system_assumed' + ext_system),
                            libs.index('system_lib' + ext_system)))
        self.assertLess(libs.index(prefix + 'Z2' + ext),
                        min(libs.index('system_assumed' + ext_system),
                            libs.index('system_lib' + ext_system)))
        if platform.system() == "Darwin":
            self.assertLess(libs.index('liblibZ.a'), libs.index('Carbon'))
            self.assertLess(libs.index('libZ2.a'), libs.index('Carbon'))

    @staticmethod
    def _get_link_order_from_cmake(content):
        libs = []
        for it in content.splitlines():
            # This is for Linux and Mac
            if 'main.cpp.o  -o example' in it:
                _, links = it.split("main.cpp.o  -o example")
                for it_lib in links.split():
                    if it_lib.startswith("-l"):
                        libs.append(it_lib[2:])
                    elif it_lib == "-framework":
                        continue
                    else:
                        try:
                            _, libname = it_lib.rsplit('/', 1)
                        except ValueError:
                            libname = it_lib
                        finally:
                            libs.append(libname)
                break
            # Windows
            if 'example.exe" /INCREMENTAL:NO /NOLOGO' in it:
                for it_lib in it.split():
                    it_lib = it_lib.strip()
                    if it_lib.endswith(".lib"):
                        try:
                            _, libname = it_lib.rsplit('\\', 1)
                        except ValueError:
                            libname = it_lib
                        finally:
                            libs.append(libname)
                break
        return libs

    def _create_find_package_project(self, multi):
        generator = "cmake_find_package_multi" if multi else "cmake_find_package"
        t = TestClient(cache_folder=self._cache_folder)
        t.current_folder = '/private/var/folders/fc/6mvcrc952dqcjfhl4c7c11ph0000gn/T/tmpezu38k36conans/pathwithoutspaces/cmake_find_package_project'
        t.save({
            'conanfile.txt': textwrap.dedent("""
                [requires]
                libD/version
                [generators]
                {}
                """.format(generator)),
            'CMakeLists.txt': textwrap.dedent("""
                cmake_minimum_required(VERSION 2.8.12)
                project(executable CXX)

                find_package(libD)
                add_executable(example main.cpp)
                target_link_libraries(example libD::libD)
                """),
            'main.cpp': self.main_cpp
        })

        t.run("install . -s build_type=Release")
        return t

    def _create_cmake_project(self, multi):
        generator = "cmake_multi" if multi else "cmake"
        include_cmake_file = "conanbuildinfo_multi" if multi else "conanbuildinfo"
        t = TestClient(cache_folder=self._cache_folder)
        t.current_folder = '/private/var/folders/fc/6mvcrc952dqcjfhl4c7c11ph0000gn/T/tmpezu38k36conans/pathwithoutspaces/cmake_project'
        t.save({
            'conanfile.txt': textwrap.dedent("""
                [requires]
                libD/version
                [generators]
                {}
                """.format(generator)),
            'CMakeLists.txt': textwrap.dedent("""
                cmake_minimum_required(VERSION 2.8.12)
                project(executable CXX)

                include(${{CMAKE_BINARY_DIR}}/{}.cmake)
                conan_basic_setup(TARGETS NO_OUTPUT_DIRS)

                add_executable(example main.cpp)
                target_link_libraries(example CONAN_PKG::libD)
                """.format(include_cmake_file)),
            'main.cpp': self.main_cpp
        })

        t.run("install . -s build_type=Release")
        t.save({"conanbuildinfo_debug.cmake": "# just be there"})
        return t

    def _run_and_get_lib_order(self, t, generator, find_package_config=False):
        extra_cmake = "-DCMAKE_PREFIX_PATH=." if find_package_config else "-DCMAKE_MODULE_PATH=."
        if generator == "Xcode":
            t.run_command("cmake . -G Xcode {} -DCMAKE_VERBOSE_MAKEFILE:BOOL=True"
                          " -DCMAKE_CONFIGURATION_TYPES=Release".format(extra_cmake))
            t.run_command("cmake --build .", assert_error=True)
            # Get the actual link order from the CMake call
            libs = self._get_link_order_from_xcode(t.load(os.path.join('executable.xcodeproj',
                                                                       'project.pbxproj')))
        else:
            t.run_command("cmake . {} -DCMAKE_VERBOSE_MAKEFILE:BOOL=True"
                          " -DCMAKE_BUILD_TYPE=Release".format(extra_cmake))
            extra_build = "--config Release" if platform.system() == "Windows" else ""  # Windows VS
            t.run_command("cmake --build . {}".format(extra_build), assert_error=True)
            # Get the actual link order from the CMake call
            libs = self._get_link_order_from_cmake(str(t.out))
        t.run_command("cmake --graphviz=graphviz.dot .")
        return libs

    """
    @parameterized.expand([(None,), ("Xcode",)])
    def test_cmake_find_package_multi(self, generator):
        if generator == "Xcode" and platform.system() != "Darwin":
            self.skipTest("Xcode is needed")

        t = self._create_find_package_project(multi=True)
        libs = self._run_and_get_lib_order(t, generator, find_package_config=True)
        self._validate_link_order(libs)
    """

    @parameterized.expand([(None,), ("Xcode",)])
    def test_cmake_find_package(self, generator):
        if generator == "Xcode" and platform.system() != "Darwin":
            self.skipTest("Xcode is needed")

        t = self._create_find_package_project(multi=False)
        libs = self._run_and_get_lib_order(t, generator)
        self._validate_link_order(libs)

    @parameterized.expand([(None,), ("Xcode",)])
    def test_cmake(self, generator):
        if generator == "Xcode" and platform.system() != "Darwin":
            self.skipTest("Xcode is needed")

        t = self._create_cmake_project(multi=False)
        libs = self._run_and_get_lib_order(t, generator)
        self._validate_link_order(libs)

    """
    @parameterized.expand([(None,), ("Xcode",)])
    def test_cmake_multi(self, generator):
        if generator == "Xcode" and platform.system() != "Darwin":
            self.skipTest("Xcode is needed")

        t = self._create_cmake_project(multi=True)
        libs = self._run_and_get_lib_order(t, generator)
        self._validate_link_order(libs)
    """
