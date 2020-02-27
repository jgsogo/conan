import textwrap

from jinja2 import Template

# At package level
cmakelists_template = Template(textwrap.dedent(r"""
    set(CMAKE_CXX_COMPILER_WORKS 1)
    set(CMAKE_CXX_ABI_COMPILED 1)

    cmake_minimum_required(VERSION {{cmake_minimum_version|default("3.10")}})
    project({{package.name}} LANGUAGES CXX)

    {% if 'cmake' in package.generators %}
    include(${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup({% if use_targets|default(True) %}TARGETS{% endif %})
    {% endif %}

    {%- if 'cmake_find_package' in package.generators %}
    {%- for item in package.generators["cmake_find_package"] %}
    find_package({{ item.name }} REQUIRED)
    {%- endfor %}
    {%- endif %}

    file(WRITE ${CMAKE_CURRENT_SOURCE_DIR}/{{ package.name }}.h "#pragma once\nconst char* const {{ package.name }}_MESSAGE=\"${MESSAGE}\";")

    {% for library in package.libraries %}
    add_library({{library.target}} {{library.name}}/lib.cpp {{library.name}}/lib.h)
    target_include_directories({{library.target}}
        PUBLIC
            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>)
    {% if library.requires %}target_link_libraries({{library.target}} PUBLIC {% for r in library.requires %}{{r.target}} {% endfor %}){% endif%}
    set_target_properties({{library.target}} PROPERTIES OUTPUT_NAME {{library.name}})
    {% endfor %}

    {% for executable in package.executables %}
    add_executable({{executable.name}} {{executable.name}}/main.cpp)
    {% if executable.requires %}target_link_libraries({{executable.target}} PUBLIC {% for r in executable.requires %}{{r.target}} {% endfor %}){% endif%}
    set_target_properties({{executable.target}} PROPERTIES OUTPUT_NAME {{executable.name}})
    {% endfor %}
"""))

conanfile_template = Template(textwrap.dedent(r"""
    import os
    from conans import ConanFile, CMake

    class {{package.name}}(ConanFile):
        name = "{{ package.name }}"
        version = "{{ package.version }}"
        settings = "os", "arch", "compiler", "build_type"
        options = {"shared": [True, False], "fPIC": [True, False], "message": "ANY"}
        default_options = {"shared": {{"True" if package.shared else "False"}}, "fPIC": True, "message": ""}
        exports = "*"

        {% if package.generators %}
        generators = "{{package.generators.keys()|join('", "')}}"
        {% endif %}

        def configure(self):
            if self.settings.compiler == 'Visual Studio':
                del self.options.fPIC

        def requirements(self):
            {%- for require in package.requires %}
            self.requires("{{require.ref}}")
            {%- endfor %}
            pass

        def build_requirements(self):
            {%- for require in package.build_requires_build %}
            self.build_requires("{{require.ref}}")
            {%- endfor %}
            {%- for require in package.build_requires_host %}
            self.build_requires("{{require.ref}}", force_host_context=True)
            {%- endfor %}
            pass
        
        def build(self):
            # Check build_requires (build) are available
            {%- for require in package.build_requires_build %}
            {%- for exec in require.executables %}
            self.output.write(">>>> {{ require.name }} | {{ exec }}")
            self.run("{{ exec }}", run_environment=True)
            {%- endfor %}
            {%- endfor %}
            
            # Run actual compilation
            cmake = CMake(self)
            message = str(self.options.message)
            if not message:
                message = "|".join(map(str, [self.settings.os, self.settings.arch, self.settings.compiler, self.settings.build_type]))
            cmake.definitions["MESSAGE:STRING"] = message
            cmake.configure()
            cmake.build()

        def package(self):
            self.copy("*.h", dst="include", keep_path=True)
            self.copy("*.lib", dst="lib", keep_path=False)
            self.copy("*.dll", dst="bin", keep_path=False)
            self.copy("*.so", dst="lib", keep_path=False)
            self.copy("*.dylib", dst="lib", keep_path=False)
            self.copy("*.a", dst="lib", keep_path=False)
            {%- for exec in package.executables %}
            self.copy("{{ exec.name }}", src="bin", dst="bin", keep_path=False)
            {%- endfor %}

        def package_info(self):
            self.cpp_info.libs = ["{{package.libraries|join('", "')}}"]
            {%- if package.executables %}
            self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
            {%- endif %}
"""))

# For each library/component inside a package
lib_cpp_template = Template(textwrap.dedent(r"""
    #include "{{library.name}}/lib.h"

    // Requires and build_requires (host)
    {%- for require in library.requires %}
    #include "{{require.name}}/lib.h"
    {%- endfor %}

    void {{library.name}}(int tabs) {
        #ifdef {{library.name}}_EXPORTS
            std::cout << std::string(tabs, '\t') << "> {{library.name}} (" << {{package.name}}_MESSAGE << "): {{ message|default("default") }} (shared!)" << std::endl;
        #else
            std::cout << std::string(tabs, '\t') << "> {{library.name}} (" << {{package.name}}_MESSAGE << "): {{ message|default("default") }}" << std::endl;
        #endif
        
        // Requires and build_requires (host)
        {%- for require in library.requires %}
        {{require.name}}_header(tabs+1);
        {{require.name}}(tabs+1);
        {%- endfor %}
    }
"""))

lib_h_template = Template(textwrap.dedent(r"""
    #pragma once

    #include <iostream>
    #include "{{ package.name }}.h"

    void {{library.name}}(int tabs);

    static void {{library.name}}_header(int tabs) {
        std::cout << std::string(tabs, '\t') << "> {{library.name}}_header (" << {{package.name}}_MESSAGE << "): {{ message|default("default") }}" << std::endl;
    }
"""))

main_cpp_template = Template(textwrap.dedent(r"""
    #include <iostream>

    {% for require in executable.requires %}
    #include "{{require.name}}/lib.h"
    {% endfor %}
    
    int main() {
        std::cout << "> {{executable.name}} (" << {{package.name}}_MESSAGE << "): {{ message|default("default") }}" << std::endl;
        {% for require in executable.requires %}
        {{require.name}}_header(0);
        {{require.name}}(0);
        {% endfor %}
    }
"""))
