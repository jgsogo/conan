{% import '_toolchain_macros.cmake' as toolchain_macros %}

# Conan automatically generated toolchain file
# DO NOT EDIT MANUALLY, it will be overwritten

# Avoid including toolchain file several times (bad if appending to variables like
#   CMAKE_CXX_FLAGS. See https://github.com/android/ndk/issues/323
if(CONAN_TOOLCHAIN_INCLUDED)
  return()
endif()
set(CONAN_TOOLCHAIN_INCLUDED TRUE)

{% block compiler_features_config %}
{% endblock %}

get_property( _CMAKE_IN_TRY_COMPILE GLOBAL PROPERTY IN_TRY_COMPILE )
if(_CMAKE_IN_TRY_COMPILE)
    message(STATUS "Running toolchain IN_TRY_COMPILE")
    return()
endif()


set(CMAKE_EXPORT_NO_PACKAGE_REGISTRY ON)

# To support the cmake_find_package generators
set(CMAKE_MODULE_PATH {{ tc.cmake_module_path }} ${CMAKE_MODULE_PATH})
set(CMAKE_PREFIX_PATH {{ tc.cmake_prefix_path }} ${CMAKE_PREFIX_PATH})


{% block main %}
    {# It is ok to modify content here, these are options of the project itself. There is no alternative #}
    {% if tc.shared_libs %}set(BUILD_SHARED_LIBS {{ tc.shared_libs }}){% endif %}
    {% if tc.fpic %}set(CMAKE_POSITION_INDEPENDENT_CODE ON){% endif %}


    set(CONAN_CXX_FLAGS "${CONAN_CXX_FLAGS} {{ tc.architecture }}")
    set(CONAN_C_FLAGS "${CONAN_C_FLAGS} {{ tc.architecture }}")
    set(CONAN_SHARED_LINKER_FLAGS "${CONAN_SHARED_LINKER_FLAGS} {{ tc.architecture }}")
    set(CONAN_EXE_LINKER_FLAGS "${CONAN_EXE_LINKER_FLAGS} {{ tc.architecture }}")
{% endblock %}


{% block flags_init %}
set(CMAKE_CXX_FLAGS_INIT "${CONAN_CXX_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_C_FLAGS_INIT "${CONAN_C_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_SHARED_LINKER_FLAGS_INIT "${CONAN_SHARED_LINKER_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_EXE_LINKER_FLAGS_INIT "${CONAN_EXE_LINKER_FLAGS}" CACHE STRING "" FORCE)
{% endblock %}


# Variables
{% for it, value in variables.items() %}
set({{ it }} "{{ value }}")
{%- endfor %}
# Variables  per configuration
{{ toolchain_macros.iterate_configs(variables.configuration_types, action='set') }}

# Preprocessor definitions
{% for it, value in preprocessor_definitions.items() -%}
# add_compile_definitions only works in cmake >= 3.12
add_definitions(-D{{ it }}="{{ value }}")
{%- endfor %}
# Preprocessor definitions per configuration
{{ toolchain_macros.iterate_configs(preprocessor_definitions.configuration_types, action='add_definitions') }}
