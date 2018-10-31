# coding=utf-8

import os

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
        return self.paths.get('conanfile', os.path.join(self.conan(), CONANFILE))

    def package(self, package_reference):
        assert isinstance(package_reference, PackageReference)
        assert package_reference.conan == self._conan_ref

        return self.conan()
        return os.path.join(self.conan(), "package_reference")
