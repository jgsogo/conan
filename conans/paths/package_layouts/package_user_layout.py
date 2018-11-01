# coding=utf-8

import re
import os
import ntpath
import posixpath
import configparser

from conans.util.files import load
from conans.paths.package_layouts.package_base_layout import PackageBaseLayout
from conans.paths import CONANFILE
from conans.model.ref import PackageReference


CONAN_PACKAGE_LAYOUT_FILE = '.conan_package_layout'


class PackageUserLayout(PackageBaseLayout):

    paths = {}

    def __init__(self, linked_package_file, conan_ref, short_paths=False):
        base_folder = load(linked_package_file)
        super(PackageUserLayout, self).__init__(base_folder, conan_ref, short_paths)

        # TODO: Parse linked_package_file (or wherever the laytout pattern is)
        #  as directories won't have the 'standard' layout.
        self.paths = {}

    def installed_as_editable(self):
        return True

    def conanfile(self):
        """ Path to the conanfile. We can agree that an editable package needs to be a Conan package """
        return self.paths.get(CONANFILE, os.path.join(self.conan(), CONANFILE))

    def editable_package_layout_file(self):
        return self.paths.get(CONAN_PACKAGE_LAYOUT_FILE,
                              os.path.join(self.conan(), CONAN_PACKAGE_LAYOUT_FILE))

    def package(self, package_reference):
        assert isinstance(package_reference, PackageReference)
        assert package_reference.conan == self._conan_ref

        return self.conan()
        return os.path.join(self.conan(), "package_reference")


def parse_package_layout_content(content, base_path=None):
    """ Returns a dictionary containing information about paths for a CppInfo object: includes,
    libraries, resources, binaries,... """
    ret = {k: [] for k in ['includedirs', 'libdirs', 'resdirs', 'bindirs']}

    def make_abs(value):
        value = re.sub(r'\\\\+', r'\\', value)
        value = value.replace('\\', '/')

        isabs = ntpath.isabs(value) or posixpath.isabs(value)
        if base_path and not isabs:
            value = os.path.abspath(os.path.join(base_path, value))
        value = os.path.normpath(value)
        return value

    parser = configparser.ConfigParser(allow_no_value=True, delimiters=('#', ))
    parser.optionxform = str
    parser.read_string(content)
    for section in ret.keys():
        if section in parser:
            ret[section] = [make_abs(value) for value in parser[section]]
    return ret


