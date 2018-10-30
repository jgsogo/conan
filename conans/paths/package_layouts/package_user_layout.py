# coding=utf-8

import os

from conans.util.files import load
from conans.paths.package_layouts.package_base_layout import PackageBaseLayout


CONAN_PACKAGE_LAYOUT_FILE = '.conan_package_layout'


class PackageUserLayout(PackageBaseLayout):

    def __init__(self, linked_package_file, conan_ref, short_paths=False):
        base_folder = load(linked_package_file)
        super(PackageUserLayout, self).__init__(base_folder, conan_ref, short_paths)

        # TODO: Parse linked_package_file (or wherever the laytout pattern is)
        #  as directories won't have the 'standard' layout.


