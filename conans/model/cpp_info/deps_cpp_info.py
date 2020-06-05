import os
from .cpp_info import CppInfo


class DepsCppInfo(object):

    _path_fields_mapping = {
        "include_paths": "includedirs",
        "lib_paths": "libdirs",
        "bin_paths": "bindirs",
        "build_paths": "builddirs",
        "res_paths": "resdirs",
        "framework_paths": "frameworkdirs",
        "build_modules_paths": "build_modules"}

    def __init__(self, version, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfo), "CppInfo expected, got {}".format(type(cpp_info))
        self.version = version
        self._cpp_info = cpp_info

        def get_absolute_paths(_cpp_info_field):
            for it in getattr(self._cpp_info, _cpp_info_field):
                fullpath = os.path.join(self._cpp_info.rootpath, it)
                if not remove_missing_paths:
                    yield fullpath
                elif os.path.exists(fullpath):
                    yield fullpath

        for field, cpp_info_field in self._path_fields_mapping.items():
            setattr(self, field, property(get_absolute_paths(cpp_info_field)))

