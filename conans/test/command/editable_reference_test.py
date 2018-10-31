# coding=utf-8

import os
import unittest
import tempfile

from conans.test.utils.tools import TestClient
from conans.paths.package_layouts.package_user_layout import CONAN_PACKAGE_LAYOUT_FILE
from conans.client.tools.files import load
from conans.test import CONAN_TEST_FOLDER


class EditableReferenceTest(unittest.TestCase):
    header = """
#include <iostream>

void hello() {{
    std::cout << "Hello {word}!" << std::endl;
}} 
            """

    def _create_editable_package(self, base_folder):
        client = TestClient(base_folder=base_folder)

        conanfile = """
import os
from conans import ConanFile, tools

class Pkg(ConanFile):
    name = "MyLib"
    version = "0.1"
    
    exports_sources = "*"
        
    def package(self):
        self.copy("*.hpp", dst="include", src="src/include")
        
    def package_info(self):
        self.cpp_info.libs = ["MyLib", "otra", ]
        self.cpp_info.defines = ["MyLibDEFINES",]
        self.cpp_info.libdirs = ["MyLib-libdirs", ]
        self.cpp_info.includedirs = ["MyLib-includedirs", "include", ]
        
"""

        conan_package_layout = """
        """

        client.save({"conanfile.py": conanfile,
                     CONAN_PACKAGE_LAYOUT_FILE: conan_package_layout,
                     "src/include/hello.hpp": self.header.format(word="EDITABLE")})

        client.run("editable . MyLib/0.1@user/editable")
        print(client.out)
        print("*"*200)
        return client

    def test_dev(self):
        base_folder = tempfile.mkdtemp(suffix='conans', dir=CONAN_TEST_FOLDER)

        client_editable = self._create_editable_package(base_folder=base_folder)

        ### Now, consume the installed-as-editable package (keep base_folder, it is the cache!!!)
        client = TestClient(base_folder=base_folder)
        conanfile_txt = """
import os
from conans import ConanFile, CMake

class TestConan(ConanFile):
    name = "pkg"
    version = "0.0"
    
    requires = "MyLib/0.1@user/editable"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    exports_sources = "src/*"

    def build(self):
        cmake = CMake(self)
        cmake.configure(source_folder="src")
        cmake.build()   
    
        os.chdir("bin")
        self.run("./hello")

"""
        cmakelists = """
cmake_minimum_required(VERSION 2.8.12)
project(MyHello CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(hello main.cpp)
"""
        main_cpp = """
#include "hello.hpp"

int main() {
    hello();
}
"""

        client.save({"conanfile.py": conanfile_txt,
                     "src/CMakeLists.txt": cmakelists,
                     "src/main.cpp": main_cpp})

        client.run("install . -g txt -g cmake")

        text = load(os.path.join(client.current_folder, "conanbuildinfo.txt"))
        #txt = ";".join(text.splitlines())
        #self.assertNotIn("[libs];MyLib", txt)
        cmake = load(os.path.join(client.current_folder, "conanbuildinfo.cmake"))
        #self.assertIn("set(CONAN_LIBS MyLib ${CONAN_LIBS})", cmake)

        ## Now, build and run this project
        client.run("create . pkg/0.0@user/testing")
        self.assertIn("Hello EDITABLE!", client.out)
        print(client.out)
        print("^"*200)


        ### Modify the editable package:
        client_editable.save(
            {"src/include/hello.hpp": self.header.format(word="EDITED!!!")})
        client.run("create . pkg/0.0@user/testing")
        self.assertIn("Hello EDITED!!!!", client.out)
        print(client.out)

