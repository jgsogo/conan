# coding=utf-8

import os
import unittest
import tempfile

from conans.test.utils.tools import TestClient
from conans.paths.package_layouts.package_user_layout import CONAN_PACKAGE_LAYOUT_FILE
from conans.client.tools.files import load
from conans.test import CONAN_TEST_FOLDER


class EditableReferenceTest(unittest.TestCase):

    def _create_editable_package(self, base_folder):
        client = TestClient(base_folder=base_folder)

        conanfile = """
import os
from conans import ConanFile, tools

class Pkg(ConanFile):
    
    def package(self):
        tools.save(os.path.join(self.package_folder, "include/file.h"), "//file")
    
    def package_info(self):
        self.cpp_info.libs = ["MyLib", "otra", ]
        self.cpp_info.defines = ["MyLib-DEFINES",]
        self.cpp_info.libdirs = ["MyLib-libdirs", ]
        self.cpp_info.includedirs = ["MyLib-includedirs", "include", ]
        
"""

        conan_package_layout = """
        """

        client.save({"conanfile.py": conanfile,
                     CONAN_PACKAGE_LAYOUT_FILE: conan_package_layout})

        client.run("create . MyLib/0.1@user/editable")
        return client

    def test_dev(self):
        base_folder = tempfile.mkdtemp(suffix='conans', dir=CONAN_TEST_FOLDER)

        self._create_editable_package(base_folder=base_folder)

        ### Now, consume the installed-as-editable package (keep base_folder, it is the cache!!!)
        client = TestClient(base_folder=base_folder)
        conanfile_txt = """
[requires]
MyLib/0.1@user/editable
"""
        client.save({"conanfile.txt": conanfile_txt})
        client.run("install . -g txt -g cmake")

        text = load(os.path.join(client.current_folder, "conanbuildinfo.txt"))
        txt = ";".join(text.splitlines())
        self.assertIn("[libs];MyLib", txt)
        cmake = load(os.path.join(client.current_folder, "conanbuildinfo.cmake"))
        self.assertIn("set(CONAN_LIBS MyLib ${CONAN_LIBS})", cmake)

