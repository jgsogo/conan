import os
from .cpp_info import CppInfo, CppInfoComponent, CppInfoConfig


class BaseDepsCppInfo(object):
    """ A wrapper to access cppinfo data in a convenient way """

    def __init__(self, cpp_info, remove_missing_paths=False):
        self._cpp_info = cpp_info
        self._remove_missing_paths = remove_missing_paths

    def _get_absolute_paths(self, _cpp_info_field):
        for it in getattr(self._cpp_info, _cpp_info_field):
            fullpath = os.path.join(self._cpp_info.rootpath, it)
            if not self._remove_missing_paths:
                yield fullpath
            elif os.path.exists(fullpath):
                yield fullpath

    @property
    def include_paths(self):
        return list(self._get_absolute_paths("includedirs"))

    @property
    def lib_paths(self):
        return list(self._get_absolute_paths("libdirs"))

    @property
    def bin_paths(self):
        return list(self._get_absolute_paths("bindirs"))

    @property
    def build_paths(self):
        return list(self._get_absolute_paths("builddirs"))

    @property
    def res_paths(self):
        return list(self._get_absolute_paths("resdirs"))

    @property
    def framework_paths(self):
        return list(self._get_absolute_paths("frameworkdirs"))

    @property
    def build_modules_paths(self):
        return list(self._get_absolute_paths("build_modules"))

    def __getattr__(self, item):
        return getattr(self._cpp_info, item)


class DepsCppInfo(BaseDepsCppInfo):
    def __init__(self, version, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfo), "CppInfo expected, got {}".format(type(cpp_info))
        super(DepsCppInfo, self).__init__(cpp_info, remove_missing_paths)
        self.version = version

    @property
    def components(self):
        return {k: DepsCppInfoComponent(self._cpp_info, v, self._remove_missing_paths)
                for k, v in self._cpp_info.components.items()}

    def __getattr__(self, item):
        if item in self._cpp_info.get_configs():
            config = getattr(self._cpp_info, item)
            return DepsCppInfoConfig(self._cpp_info, config, self._remove_missing_paths)

        return getattr(self._cpp_info, item)


class DepsCppInfoConfig(BaseDepsCppInfo):
    def __init__(self, pkg_cpp_info, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfoConfig), \
            "CppInfoConfig expected, got {}".format(type(cpp_info))
        super(DepsCppInfoConfig, self).__init__(cpp_info, remove_missing_paths)
        self._pkg_cpp_info = pkg_cpp_info


class DepsCppInfoComponent(BaseDepsCppInfo):
    COMPONENTS_SCOPE = '::'

    def __init__(self, pkg_cpp_info, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfoComponent), \
            "CppInfoComponent expected, got {}".format(type(cpp_info))
        super(DepsCppInfoComponent, self).__init__(cpp_info, remove_missing_paths)
        self._pkg_cpp_info = pkg_cpp_info

    @property
    def requires(self):
        # TODO: From the consumers POV we always know the name of the package, we always return
        #   full component name
        def _get_req():
            for req in self._cpp_info.requires:
                if self.COMPONENTS_SCOPE in req:
                    yield req
                else:
                    yield self.COMPONENTS_SCOPE.join([str(self._pkg_cpp_info), req])
        return list(_get_req())
