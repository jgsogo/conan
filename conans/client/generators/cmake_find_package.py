from jinja2 import Template
import textwrap

from conans.client.generators.cmake import DepsCppCmake
from conans.client.generators.cmake_find_package_common import (target_template,
                                                                CMakeFindPackageCommonMacros,
                                                                find_transitive_dependencies)
from conans.client.generators.cmake_multi import extend
from conans.errors import ConanException
from conans.model import Generator
from conans.model.build_info import COMPONENT_SCOPE


class CMakeFindPackageGenerator(Generator):
    generator_name = "cmake_find_package"

    find_template = textwrap.dedent("""
        {macros_and_functions}

        include(FindPackageHandleStandardArgs)

        conan_message(STATUS "Conan: Using autogenerated Find{name}.cmake")
        # Global approach
        set({name}_FOUND 1)
        set({name}_VERSION "{version}")

        find_package_handle_standard_args({name} REQUIRED_VARS
                                          {name}_VERSION VERSION_VAR {name}_VERSION)
        mark_as_advanced({name}_FOUND {name}_VERSION)

        {find_libraries_block}
        if(NOT ${{CMAKE_VERSION}} VERSION_LESS "3.0")
            # Target approach
            if(NOT TARGET {name}::{name})
                add_library({name}::{name} INTERFACE IMPORTED)
                if({name}_INCLUDE_DIRS)
                    set_target_properties({name}::{name} PROPERTIES INTERFACE_INCLUDE_DIRECTORIES
                                          "${{{name}_INCLUDE_DIRS}}")
                endif()
                set_property(TARGET {name}::{name} PROPERTY INTERFACE_LINK_LIBRARIES
                             "${{{name}_LIBRARIES_TARGETS}};${{{name}_LINKER_FLAGS_LIST}}")
                set_property(TARGET {name}::{name} PROPERTY INTERFACE_COMPILE_DEFINITIONS
                             ${{{name}_COMPILE_DEFINITIONS}})
                set_property(TARGET {name}::{name} PROPERTY INTERFACE_COMPILE_OPTIONS
                             "${{{name}_COMPILE_OPTIONS_LIST}}")
                {find_dependencies_block}
            endif()
        endif()
        """)

    find_components_tpl = Template(textwrap.dedent("""\
        ########## MACROS ###########################################################################
        #############################################################################################
        {% raw %}
        function(conan_message MESSAGE_OUTPUT)
            if(NOT CONAN_CMAKE_SILENT_OUTPUT)
                message(${ARGV${0}})
            endif()
        endfunction()

        macro(conan_find_apple_frameworks FRAMEWORKS_FOUND FRAMEWORKS FRAMEWORKS_DIRS)
            if(APPLE)
                foreach(_FRAMEWORK ${FRAMEWORKS})
                    # https://cmake.org/pipermail/cmake-developers/2017-August/030199.html
                    find_library(CONAN_FRAMEWORK_${_FRAMEWORK}_FOUND NAME ${_FRAMEWORK} PATHS ${FRAMEWORKS_DIRS})
                    if(CONAN_FRAMEWORK_${_FRAMEWORK}_FOUND)
                        list(APPEND ${FRAMEWORKS_FOUND} ${CONAN_FRAMEWORK_${_FRAMEWORK}_FOUND})
                    else()
                        message(FATAL_ERROR "Framework library ${_FRAMEWORK} not found in paths: ${FRAMEWORKS_DIRS}")
                    endif()
                endforeach()
            endif()
        endmacro()

        function(conan_component_library_targets out_libraries_target libdir libraries)
            foreach(_LIBRARY_NAME ${libraries})
                find_library(CONAN_FOUND_LIBRARY NAME ${_LIBRARY_NAME} PATHS ${libdir}
                             NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
                if(CONAN_FOUND_LIBRARY)
                    conan_message(STATUS "Library ${_LIBRARY_NAME} found ${CONAN_FOUND_LIBRARY}")
                    if(NOT ${CMAKE_VERSION} VERSION_LESS "3.0")
                        # Create a micro-target for each lib/a found
                        set(_LIB_NAME ${_LIBRARY_NAME})
                        if(NOT TARGET ${_LIB_NAME})
                            # Create a micro-target for each lib/a found
                            add_library(${_LIB_NAME} UNKNOWN IMPORTED)
                            set_target_properties(${_LIB_NAME} PROPERTIES IMPORTED_LOCATION ${CONAN_FOUND_LIBRARY})
                        else()
                            conan_message(STATUS "Skipping already existing target: ${_LIB_NAME}")
                        endif()
                        list(APPEND _out_libraries_target ${_LIB_NAME})
                    endif()
                    conan_message(STATUS "Found: ${CONAN_FOUND_LIBRARY}")
                else()
                    conan_message(STATUS "Library ${_LIBRARY_NAME} NOT FOUND!!")
                endif()
                unset(CONAN_FOUND_LIBRARY CACHE)
            endforeach()

            conan_message(STATUS "Components Library targets: ${_out_libraries_target}")
            set(${out_libraries_target} ${_out_libraries_target} PARENT_SCOPE)
        endfunction()
        {% endraw %}

        ########### FOUND PACKAGE ###################################################################
        #############################################################################################

        include(FindPackageHandleStandardArgs)

        conan_message(STATUS "Conan: Using autogenerated Find{{ pkg_name }}.cmake")
        set({{ pkg_name }}_FOUND 1)
        set({{ pkg_name }}_VERSION "{{ pkg_version }}")

        find_package_handle_standard_args({{ pkg_name }} REQUIRED_VARS
                                          {{ pkg_name }}_VERSION VERSION_VAR {{ pkg_name }}_VERSION)
        mark_as_advanced({{ pkg_name }}_FOUND {{ pkg_name }}_VERSION)


        ########### VARIABLES #######################################################################
        #############################################################################################

        set({{ pkg_name }}_COMPONENTS {{ pkg_components }})
        set({{ pkg_name }}_DEPENDENCIES {{ pkg_dependencies }})

        {%- for comp_name, comp in components %}

        ########### COMPONENT {{ comp_name }} VARIABLES #############################################

        set({{ comp_name }}_INCLUDE_DIRS {{ comp.include_paths }})
        set({{ comp_name }}_INCLUDE_DIR {{ comp.include_path }})
        set({{ comp_name }}_INCLUDES {{ comp.include_paths }})
        set({{ comp_name }}_LIB_DIRS {{ comp.lib_paths }})
        set({{ comp_name }}_RES_DIRS {{ comp.res_paths }})
        set({{ comp_name }}_DEFINITIONS {{ comp.defines }})
        set({{ comp_name }}_COMPILE_DEFINITIONS {{ comp.compile_definitions }})
        set({{ comp_name }}_COMPILE_OPTIONS_LIST "{{ comp.cxxflags_list }}" "{{ comp.cflags_list }}")
        set({{ comp_name }}_LIBS {{ comp.libs }})
        set({{ comp_name }}_SYSTEM_LIBS {{ comp.system_libs }})
        set({{ comp_name }}_FRAMEWORK_DIRS {{ comp.framework_paths }})
        set({{ comp_name }}_FRAMEWORKS {{ comp.frameworks }})
        set({{ comp_name }}_BUILD_MODULES_PATHS {{ comp.build_modules_paths }})
        set({{ comp_name }}_DEPENDENCIES {{ comp.public_deps }})

        {%- endfor %}


        ########## FIND PACKAGE DEPENDENCY ##########################################################
        #############################################################################################

        include(CMakeFindDependencyMacro)

        {%- for public_dep in pkg_public_deps %}

        if(NOT {{ public_dep }}_FOUND)
            find_dependency({{ public_dep }} REQUIRED)
        else()
            message(STATUS "Dependency {{ public_dep }} already found")
        endif()

        {%- endfor %}


        ########## FIND LIBRARIES & FRAMEWORKS / DYNAMIC VARS #######################################
        #############################################################################################

        {%- for comp_name, comp in components %}

        ########## COMPONENT {{ comp_name }} FIND LIBRARIES & FRAMEWORKS / DYNAMIC VARS #############

        set({{ comp_name }}_LIB_TARGETS "") # Will be filled later, if CMake 3
        conan_component_library_targets({{ comp_name }}_LIB_TARGETS "${% raw %}{{% endraw %}{{ comp_name }}_LIB_DIRS{% raw %}}{% endraw %}" "${% raw %}{{% endraw %}{{ comp_name }}_LIBS{% raw %}}{% endraw %}")
        conan_message(STATUS "Components Library targets2: ${% raw %}{{% endraw %}{{ comp_name }}_LIB_TARGETS{% raw %}}{% endraw %}")

        set({{ comp_name }}_FRAMEWORKS_FOUND "") # Will be filled later
        conan_find_apple_frameworks({{ comp_name }}_FRAMEWORKS_FOUND "${% raw %}{{% endraw %}{{ comp_name }}_FRAMEWORKS{% raw %}}{% endraw %}" "${% raw %}{{% endraw %}{{ comp_name }}_FRAMEWORK_DIRS{% raw %}}{% endraw %}")

        set({{ comp_name }}_LINK_LIBS "${% raw %}{{% endraw %}{{ comp_name }}_LIB_TARGETS{% raw %}}{% endraw %};${% raw %}{{% endraw %}{{ comp_name }}_SYSTEM_LIBS{% raw %}}{% endraw %};${% raw %}{{% endraw %}{{ comp_name }}_FRAMEWORKS_FOUND{% raw %}}{% endraw %};${% raw %}{{% endraw %}{{ comp_name }}_DEPENDENCIES{% raw %}}{% endraw %}")


        set(CMAKE_MODULE_PATH {{ comp.build_paths }} ${CMAKE_MODULE_PATH})
        set(CMAKE_PREFIX_PATH {{ comp.build_paths }} ${CMAKE_PREFIX_PATH})

        foreach(_BUILD_MODULE_PATH ${% raw %}{{% endraw %}{{ comp_name }}_BUILD_MODULES_PATHS{% raw %}}{% endraw %})
            include(${_BUILD_MODULE_PATH})
        endforeach()

        {%- endfor %}


        ########## TARGETS ##########################################################################
        #############################################################################################

        {%- for comp_name, comp in components %}

        ########## COMPONENT {{ comp_name }} TARGET #################################################

        if(NOT ${CMAKE_VERSION} VERSION_LESS "3.0")
            # Target approach
            if(NOT TARGET {{ pkg_name }}::{{ comp_name }})
                add_library({{ pkg_name }}::{{ comp_name }} INTERFACE IMPORTED)
                set_target_properties({{ pkg_name }}::{{ comp_name }} PROPERTIES INTERFACE_INCLUDE_DIRECTORIES
                                      "${% raw %}{{% endraw %}{{ comp_name }}_INCLUDE_DIRS{% raw %}}{% endraw %}")
                set_property(TARGET {{ pkg_name }}::{{ comp_name }} PROPERTY INTERFACE_LINK_DIRECTORIES
                             "${% raw %}{{% endraw %}{{ comp_name }}_LIB_DIRS{% raw %}}{% endraw %}")
                set_property(TARGET {{ pkg_name }}::{{ comp_name }} PROPERTY INTERFACE_LINK_LIBRARIES
                             "${% raw %}{{% endraw %}{{ comp_name }}_LINK_LIBS{% raw %}}{% endraw %};${% raw %}{{% endraw %}{{ comp_name }}_LINKER_FLAGS_LIST{% raw %}}{% endraw %}")
                set_property(TARGET {{ pkg_name }}::{{ comp_name }} PROPERTY INTERFACE_COMPILE_DEFINITIONS
                             ${% raw %}{{% endraw %}{{ comp_name }}_COMPILE_DEFINITIONS{% raw %}}{% endraw %})
                set_property(TARGET {{ pkg_name }}::{{ comp_name }} PROPERTY INTERFACE_COMPILE_OPTIONS
                             "${% raw %}{{% endraw %}{{ comp_name }}_COMPILE_OPTIONS_LIST{% raw %}}{% endraw %}")
            endif()
        endif()

        {%- endfor %}

        ########## GLOBAL TARGET ####################################################################

        if(NOT ${CMAKE_VERSION} VERSION_LESS "3.0")
            if(NOT TARGET {{ pkg_name }}::{{ pkg_name }})
                add_library({{ pkg_name }}::{{ pkg_name }} INTERFACE IMPORTED)
                set_property(TARGET {{ pkg_name }}::{{ pkg_name }} PROPERTY INTERFACE_LINK_LIBRARIES
                             "${% raw %}{{% endraw %}{{ pkg_name }}_COMPONENTS{% raw %}}{% endraw %};${% raw %}{{% endraw %}{{ pkg_name }}_DEPENDENCIES{% raw %}}{% endraw %}")
            endif()
        endif()

    """))

    @property
    def filename(self):
        return None

    def _get_name(self, obj):
        get_name = getattr(obj, "get_name")
        return get_name(self.generator_name)

    @property
    def content(self):
        ret = {}
        for pkg_name, cpp_info in self.deps_build_info.dependencies:
            pkg_findname = self._get_name(cpp_info)
            ret["Find%s.cmake" % pkg_findname] = self._find_for_dep(pkg_name, pkg_findname, cpp_info)
        return ret

    def _get_components(self, pkg_name, pkg_findname, cpp_info):
        find_package_components = []
        for comp_name, comp in cpp_info._get_sorted_components().items():
            comp_findname = self._get_name(cpp_info.components[comp_name])
            deps_cpp_cmake = DepsCppCmake(comp)
            deps_cpp_cmake.public_deps = self._get_component_requires(pkg_name, pkg_findname, comp)
            find_package_components.append((comp_findname, deps_cpp_cmake))
        find_package_components.reverse()  # From the less dependent to most one
        return find_package_components

    def _get_component_requires(self, pkg_name, pkg_findname, comp):
        comp_requires_findnames = []
        for require in comp.requires:
            if COMPONENT_SCOPE in require:
                comp_require_pkg_name = require[:require.find("::")]
                if comp_require_pkg_name not in self.deps_build_info.deps:
                    raise ConanException("Component '%s' not found: '%s' is not a package "
                                         "requirement" % (require, comp_require_pkg_name))
                comp_require_pkg = self.deps_build_info[comp_require_pkg_name]
                comp_require_pkg_findname = self._get_name(comp_require_pkg)
                comp_require_comp_name = require[require.find("::") + 2:]
                if comp_require_comp_name in self.deps_build_info.deps:
                    comp_require_comp_findname = comp_require_pkg_findname
                elif comp_require_comp_name in self.deps_build_info[comp_require_pkg_name].components:
                    comp_require_comp = comp_require_pkg.components[comp_require_comp_name]
                    comp_require_comp_findname = self._get_name(comp_require_comp)
                else:
                    raise ConanException("Component '%s' not found in '%s' package requirement"
                                         % (require, comp_require_pkg_name))
            else:
                comp_require_pkg_findname = pkg_findname
                comp_require_comp = self.deps_build_info[pkg_name].components[require]
                comp_require_comp_findname = self._get_name(comp_require_comp)
            f = "{}::{}".format(comp_require_pkg_findname, comp_require_comp_findname)
            comp_requires_findnames.append(f)
        return ";".join(comp_requires_findnames)

    def _find_for_dep(self, pkg_name, pkg_findname, cpp_info):
        pkg_version = cpp_info.version
        pkg_public_deps = [self._get_name(self.deps_build_info[public_dep]) for public_dep in
                           cpp_info.public_deps]
        if cpp_info.components:
            pkg_components = ";".join(["{p}::{c}".format(p=pkg_findname, c=comp_findname) for
                                       comp_findname, _ in self._get_components(pkg_name,
                                                                                pkg_findname,
                                                                                cpp_info)])
            pkg_dependencies = ";".join(["{n}::{n}".format(n=dep) for dep in pkg_public_deps])
            return self.find_components_tpl.render(
                pkg_name=pkg_findname,
                pkg_version=pkg_version,
                pkg_components=pkg_components,
                pkg_dependencies=pkg_dependencies,
                pkg_public_deps=pkg_public_deps,
                components=self._get_components(pkg_name, pkg_findname, cpp_info))
        else:
            # The common macros
            macros_and_functions = "\n".join([
                CMakeFindPackageCommonMacros.conan_message,
                CMakeFindPackageCommonMacros.apple_frameworks_macro,
                CMakeFindPackageCommonMacros.conan_package_library_targets,
                ])

            # compose the cpp_info with its "debug" or "release" specific config
            dep_cpp_info = cpp_info
            build_type = self.conanfile.settings.get_safe("build_type")
            if build_type:
                dep_cpp_info = extend(dep_cpp_info, build_type.lower())

            # The find_libraries_block, all variables for the package, and creation of targets
            deps_names = ";".join(["{n}::{n}".format(n=n) for n in pkg_public_deps])

            deps = DepsCppCmake(dep_cpp_info)
            find_libraries_block = target_template.format(name=pkg_findname, deps=deps,
                                                          build_type_suffix="",
                                                          deps_names=deps_names)

            # The find_transitive_dependencies block
            find_dependencies_block = ""
            if dep_cpp_info.public_deps:
                # Here we are generating FindXXX, so find_modules=True
                f = find_transitive_dependencies(pkg_public_deps, find_modules=True)
                # proper indentation
                find_dependencies_block = ''.join("        " + line if line.strip() else line
                                                  for line in f.splitlines(True))

            return self.find_template.format(name=pkg_findname, version=pkg_version,
                                             find_libraries_block=find_libraries_block,
                                             find_dependencies_block=find_dependencies_block,
                                             macros_and_functions=macros_and_functions)
