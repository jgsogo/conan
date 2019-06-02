# coding=utf-8

import textwrap

conanworkspace_cmake_template = textwrap.dedent(r"""
    cmake_minimum_required(VERSION 3.10)
    
    # List of inner packages
    {%- for it in ws.inner_packages.keys() %}
    list(APPEND inner_targets "{{ it.name }}")
    {%- endfor %}
    
    # Override functions to avoid importing existing TARGETs 
    function(conan_basic_setup)
        message("Ignored call to 'conan_basic_setup'")
    endfunction()
    
    function(find_package)
        if(NOT "${ARG0}" IN_LIST inner_target)
            # Note.- If it's been already overridden, it will recurse forever
            message("find_package(${ARG0})")
            _find_package(${ARGV})
        else()
            message("find_package(${ARG0}) ignored, it is already a target")
        endif()
    endfunction()
    
    # Custom target
    function(outer_package PKG_NAME FULL_REF)
        set(PKG_SENTINEL "{{build_folder}}/${PKG_NAME}.setinel")
        add_custom_command(OUTPUT ${PKG_SENTINEL}
                           COMMAND "conan workspace2 build_outter ${FULL_REF} --build=${PKG_NAME}"
                           WORKING_DIRECTORY "{{build_folder}}"
                           COMMENT "Conan install for outter ${PKG_NAME}")
        add_custom_target(${PKG_NAME} DEPENDS ${PKG_SENTINEL})
    endfunction()

    # Add subdirectories for inner packages and custom targets for outter ones
    {% for pkg in ordered_packages %}
        {%- if pkg.ref in ws.inner_packages %}
            # Inner: {{ pkg.ref }}
            add_subdirectory("{{pkg.source_folder}}" "{{build_folder}}/{{pkg.ref.name}}")
        {%- else %}
            # Outter: {{ pkg.ref }}
            outer_package({{pkg.target}} {{pkg.ref}})
        {%- endif %}
        {%- for dep in pkg.deps %}
            add_dependencies({{pkg.target}} {{dep.target}})
        {%- endfor %}  
    {% endfor %}
""")
