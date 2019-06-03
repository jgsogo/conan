# coding=utf-8

import textwrap

conanworkspace_cmake_template = textwrap.dedent(r"""
    cmake_minimum_required(VERSION 3.10)
    
    # List of targets handled by the workspace
    {%- for it in ws.inner_packages.keys() %}
    list(APPEND ws_targets "{{ it.name }}")
    {%- endfor %}
    {%- for it in ws.fixed_packages %}
    list(APPEND ws_targets "{{ it.name }}")
    {%- endfor %}
    
    # Override functions to avoid importing existing TARGETs 
    function(conan_basic_setup)
        message("Ignored call to 'conan_basic_setup'")
    endfunction()
    
    function(find_package)
        if(NOT "${ARG0}" IN_LIST ws_targets)
            # Note.- If it's been already overridden, it will recurse forever
            message("find_package(${ARG0})")
            _find_package(${ARGV})
        else()
            message("find_package(${ARG0}) ignored, it is a target handled by Conan workspace")
        endif()
    endfunction()
    
    # Custom target
    function(outer_package PKG_NAME FULL_REF)
        set(PKG_SENTINEL "{{build_folder}}/${PKG_NAME}.setinel")
        add_custom_command(OUTPUT ${PKG_SENTINEL}
                           COMMAND sh "{{script_file}}" ${FULL_REF}
                           WORKING_DIRECTORY "{{build_folder}}"
                           COMMENT "Conan install for outter ${PKG_NAME}")
        add_custom_target(${PKG_NAME} DEPENDS ${PKG_SENTINEL})
    endfunction()

    # Add subdirectories for inner packages and custom targets for outter ones
    {% for pkg in ordered_packages %}
        {%- if pkg.ref in ws.inner_packages %}
            # Inner: {{ pkg.ref }}
            add_subdirectory("{{pkg.source_folder}}" "{{build_folder}}/{{pkg.ref.name}}")
            add_library({{pkg.ref.name}}::{{pkg.ref.name}} ALIAS {{pkg.ref.name}})
            add_library(CONAN_PKG::{{pkg.ref.name}} ALIAS {{pkg.ref.name}})
        {%- else %}
            # Outter: {{ pkg.ref }}
            outer_package({{pkg.target}} {{pkg.ref}})
        {%- endif %}
        {%- for dep in pkg.deps %}
            add_dependencies({{pkg.target}} {{dep.target}})
        {%- endfor %}  
    {% endfor %}
""")

cmakelists_template = textwrap.dedent(r"""
    cmake_minimum_required(VERSION 3.10)
    project(workspace LANGUAGES CXX)
    
    include("${CMAKE_CURRENT_SOURCE_DIR}/conanbuildinfo.cmake")
    conan_basic_setup(TARGETS)
    
    {% for pkg in ws.fixed_packages %}
        find_package({{pkg.name}} REQUIRED)
        set_target_properties({{pkg.name}}::{{pkg.name}} PROPERTIES IMPORTED_GLOBAL TRUE)
        add_library(CONAN_PKG::{{pkg.name}} ALIAS {{pkg.name}}::{{pkg.name}})
    {% endfor %}
    
    include("${CMAKE_CURRENT_SOURCE_DIR}/conanworkspace.cmake")
    
""")


build_outter_template = textwrap.dedent(r"""
    #!/usr/bin/env bash
    set -x  # echo on
    
    REFERENCE=${1?Error: no reference given}
    
    env CONAN_USER_HOME="{{CONAN_USER_HOME}}" conan search
    
    env CONAN_USER_HOME="{{CONAN_USER_HOME}}" conan workspace2 build_outter "{{ws._ws_file}}" $REFERENCE
""")
