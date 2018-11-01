# coding=utf-8

import os

from conans.model.ref import ConanFileReference


class PackageBaseLayout(object):
    """ User customizable layout for packages """

    def __init__(self, base_folder, conan_ref, short_paths=False):
        assert isinstance(conan_ref, ConanFileReference)
        self._conan_ref = conan_ref
        self._base_folder = os.path.normpath(base_folder)
        self._short_paths = short_paths

    def conan(self):
        """ Returns the base folder for this package reference """
        return self._base_folder

    def installed_as_editable(self):
        return False

    def editable_package_layout_file(self):
        raise RuntimeError("Non editable package")