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
    name = "cmake_find_package"

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
        {{ conan_message }}
        {{ conan_find_apple_frameworks }}
        {{ conan_package_library_targets }}

        ########### FOUND PACKAGE ###################################################################
        #############################################################################################

        include(FindPackageHandleStandardArgs)

        conan_message(STATUS "Conan: Using autogenerated Find{{ pkg_name }}.cmake")
        set({{ pkg_name }}_FOUND 1)
        set({{ pkg_name }}_VERSION "{{ pkg_version }}")
        set({{ pkg_name }}_COMPONENTS {{ pkg_components }})

        find_package_handle_standard_args({{ pkg_name }} REQUIRED_VARS
                                          {{ pkg_name }}_VERSION VERSION_VAR {{ pkg_name }}_VERSION)
        mark_as_advanced({{ pkg_name }}_FOUND {{ pkg_name }}_VERSION)

        if({{ pkg_name }}_FIND_COMPONENTS)
            foreach(_FIND_COMPONENT {{ '${'+pkg_name+'_FIND_COMPONENTS}' }})
                list(FIND {{ pkg_name }}_COMPONENTS "{{ pkg_name }}::${_FIND_COMPONENT}" _index)
                if(${_index} EQUAL -1)
                    conan_message(FATAL_ERROR "Conan: Component '${_FIND_COMPONENT}' NOT found in package '{{ pkg_name }}'")
                else()
                    conan_message(STATUS "Conan: Component '${_FIND_COMPONENT}' found in package '{{ pkg_name }}'")
                endif()
            endforeach()
        endif()

        ########### VARIABLES #######################################################################
        #############################################################################################

        {{ global_target_variables }}

        {%- for comp_name, comp in components %}

        ########### COMPONENT {{ comp_name }} VARIABLES #############################################

        set({{ pkg_name }}_{{ comp_name }}_INCLUDE_DIRS {{ comp.include_paths }})
        set({{ pkg_name }}_{{ comp_name }}_INCLUDE_DIR {{ comp.include_path }})
        set({{ pkg_name }}_{{ comp_name }}_INCLUDES {{ comp.include_paths }})
        set({{ pkg_name }}_{{ comp_name }}_LIB_DIRS {{ comp.lib_paths }})
        set({{ pkg_name }}_{{ comp_name }}_RES_DIRS {{ comp.res_paths }})
        set({{ pkg_name }}_{{ comp_name }}_DEFINITIONS {{ comp.defines }})
        set({{ pkg_name }}_{{ comp_name }}_COMPILE_DEFINITIONS {{ comp.compile_definitions }})
        set({{ pkg_name }}_{{ comp_name }}_COMPILE_OPTIONS_LIST "{{ comp.cxxflags_list }}" "{{ comp.cflags_list }}")
        set({{ pkg_name }}_{{ comp_name }}_LIBS {{ comp.libs }})
        set({{ pkg_name }}_{{ comp_name }}_SYSTEM_LIBS {{ comp.system_libs }})
        set({{ pkg_name }}_{{ comp_name }}_FRAMEWORK_DIRS {{ comp.framework_paths }})
        set({{ pkg_name }}_{{ comp_name }}_FRAMEWORKS {{ comp.frameworks }})
        set({{ pkg_name }}_{{ comp_name }}_BUILD_MODULES_PATHS {{ comp.build_modules_paths }})
        set({{ pkg_name }}_{{ comp_name }}_DEPENDENCIES {{ comp.public_deps }})
        set({{ pkg_name }}_{{ comp_name }}_LINKER_FLAGS_LIST
                $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,SHARED_LIBRARY>:{{ comp.sharedlinkflags_list }}>
                $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,MODULE_LIBRARY>:{{ comp.sharedlinkflags_list }}>
                $<$<STREQUAL:$<TARGET_PROPERTY:TYPE>,EXECUTABLE>:{{ comp.exelinkflags_list }}>
        )

        {%- endfor %}


        ########## FIND PACKAGE DEPENDENCY ##########################################################
        #############################################################################################

        include(CMakeFindDependencyMacro)

        {%- for public_dep in pkg_public_deps %}

        if(NOT {{ public_dep }}_FOUND)
            find_dependency({{ public_dep }} REQUIRED)
        else()
            conan_message(STATUS "Conan: Dependency {{ public_dep }} already found")
        endif()

        {%- endfor %}


        ########## FIND LIBRARIES & FRAMEWORKS / DYNAMIC VARS #######################################
        #############################################################################################

        {%- for comp_name, comp in components %}

        ########## COMPONENT {{ comp_name }} FIND LIBRARIES & FRAMEWORKS / DYNAMIC VARS #############

        set({{ pkg_name }}_{{ comp_name }}_FRAMEWORKS_FOUND "")
        conan_find_apple_frameworks({{ pkg_name }}_{{ comp_name }}_FRAMEWORKS_FOUND "{{ '${'+pkg_name+'_'+comp_name+'_FRAMEWORKS}' }}" "{{ '${'+pkg_name+'_'+comp_name+'_FRAMEWORK_DIRS}' }}")

        set({{ pkg_name }}_{{ comp_name }}_LIB_TARGETS "")
        set({{ pkg_name }}_{{ comp_name }}_NOT_USED "")
        set({{ pkg_name }}_{{ comp_name }}_LIBS_FRAMEWORKS_DEPS {{ '${'+pkg_name+'_'+comp_name+'_FRAMEWORKS_FOUND}' }} {{ '${'+pkg_name+'_'+comp_name+'_SYSTEM_LIBS}' }} {{ '${'+pkg_name+'_'+comp_name+'_DEPENDENCIES}' }})
        conan_package_library_targets("{{ '${'+pkg_name+'_'+comp_name+'_LIBS}' }}"
                                      "{{ '${'+pkg_name+'_'+comp_name+'_LIB_DIRS}' }}"
                                      "{{ '${'+pkg_name+'_'+comp_name+'_LIBS_FRAMEWORKS_DEPS}' }}"
                                      {{ pkg_name }}_{{ comp_name }}_NOT_USED
                                      {{ pkg_name }}_{{ comp_name }}_LIB_TARGETS
                                      ""
                                      "{{ pkg_name }}_{{ comp_name }}")

        set({{ pkg_name }}_{{ comp_name }}_LINK_LIBS {{ '${'+pkg_name+'_'+comp_name+'_LIB_TARGETS}' }} {{ '${'+pkg_name+'_'+comp_name+'_DEPENDENCIES}' }})

        set(CMAKE_MODULE_PATH {{ comp.build_paths }} ${CMAKE_MODULE_PATH})
        set(CMAKE_PREFIX_PATH {{ comp.build_paths }} ${CMAKE_PREFIX_PATH})

        foreach(_BUILD_MODULE_PATH {{ '${'+pkg_name+'_'+comp_name+'_BUILD_MODULES_PATHS}' }})
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
                                      "{{ '${'+pkg_name+'_'+comp_name+'_INCLUDE_DIRS}' }}")
                set_target_properties({{ pkg_name }}::{{ comp_name }} PROPERTIES INTERFACE_LINK_DIRECTORIES
                                      "{{ '${'+pkg_name+'_'+comp_name+'_LIB_DIRS}' }}")
                set_target_properties({{ pkg_name }}::{{ comp_name }} PROPERTIES INTERFACE_LINK_LIBRARIES
                                      "{{ '${'+pkg_name+'_'+comp_name+'_LINK_LIBS}' }};{{ '${'+pkg_name+'_'+comp_name+'_LINKER_FLAGS_LIST}' }}")
                set_target_properties({{ pkg_name }}::{{ comp_name }} PROPERTIES INTERFACE_COMPILE_DEFINITIONS
                                      "{{ '${'+pkg_name+'_'+comp_name+'_COMPILE_DEFINITIONS}' }}")
                set_target_properties({{ pkg_name }}::{{ comp_name }} PROPERTIES INTERFACE_COMPILE_OPTIONS
                                      "{{ '${'+pkg_name+'_'+comp_name+'_COMPILE_OPTIONS_LIST}' }}")
            endif()
        endif()

        {%- endfor %}

        ########## GLOBAL TARGET ####################################################################

        if(NOT ${CMAKE_VERSION} VERSION_LESS "3.0")
            if(NOT TARGET {{ pkg_name }}::{{ pkg_name }})
                add_library({{ pkg_name }}::{{ pkg_name }} INTERFACE IMPORTED)
                set_target_properties({{ pkg_name }}::{{ pkg_name }} PROPERTIES INTERFACE_LINK_LIBRARIES
                                      "{{ '${'+pkg_name+'_COMPONENTS}' }}")
            endif()
        endif()

    """))

    @property
    def filename(self):
        return None

    @classmethod
    def _get_name(cls, obj):
        get_name = getattr(obj, "get_name")
        return get_name(cls.name)

    @property
    def content(self):
        ret = {}
        for pkg_name, cpp_info in self.deps_build_info.dependencies:
            pkg_findname = self._get_name(cpp_info)
            ret["Find%s.cmake" % pkg_findname] = self._find_for_dep(pkg_name, pkg_findname, cpp_info)
        return ret

    def _get_components(self, pkg_name, pkg_findname, cpp_info):
        find_package_components = []
        for comp_name, comp in cpp_info.components.items():
            comp_findname = comp.get_name(CMakeFindPackageGenerator.name)
            deps_cpp_cmake = DepsCppCmake(comp)
            deps_cpp_cmake.public_deps = self._get_component_requires(pkg_name, pkg_findname, comp)
            find_package_components.append((comp_findname, deps_cpp_cmake))
        find_package_components.reverse()  # From the less dependent to most one
        return find_package_components

    def _get_component_requires(self, pkg_name, pkg_findname, comp):
        comp_requires_findnames = []
        for require in comp.requires:
            if COMPONENT_SCOPE in require:
                comp_require_pkg_name, comp_require_comp_name = require.split(COMPONENT_SCOPE)
                comp_require_pkg = self.deps_build_info[comp_require_pkg_name]
                comp_require_pkg_findname = self._get_name(comp_require_pkg)
                if comp_require_comp_name == comp_require_pkg_name:
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
        return " ".join(comp_requires_findnames)

    def _find_for_dep(self, pkg_name, pkg_findname, cpp_info):
        # return the content of the FindXXX.cmake file for the package "pkg_name"
        pkg_version = cpp_info.version
        pkg_public_deps = [self._get_name(self.deps_build_info[public_dep]) for public_dep in
                           cpp_info.public_deps]
        pkg_public_deps_names = ";".join(["{n}::{n}".format(n=n) for n in pkg_public_deps])
        if cpp_info.components:
            components = self._get_components(pkg_name, pkg_findname, cpp_info)
            # Note these are in reversed order, from more dependent to less dependent
            pkg_components = " ".join(["{p}::{c}".format(p=pkg_findname, c=comp_findname) for
                                       comp_findname, _ in reversed(components)])
            pkg_info = DepsCppCmake(cpp_info)
            global_target_variables = target_template.format(name=pkg_findname, deps=pkg_info,
                                                             build_type_suffix="",
                                                             deps_names=pkg_public_deps_names)
            return self.find_components_tpl.render(
                pkg_name=pkg_findname,
                pkg_version=pkg_version,
                pkg_components=pkg_components,
                global_target_variables=global_target_variables,
                pkg_public_deps=pkg_public_deps,
                components=components,
                conan_message=CMakeFindPackageCommonMacros.conan_message,
                conan_find_apple_frameworks=CMakeFindPackageCommonMacros.apple_frameworks_macro,
                conan_package_library_targets=CMakeFindPackageCommonMacros.conan_package_library_targets)
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
            deps = DepsCppCmake(dep_cpp_info)
            find_libraries_block = target_template.format(name=pkg_findname, deps=deps,
                                                          build_type_suffix="",
                                                          deps_names=pkg_public_deps_names)

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
