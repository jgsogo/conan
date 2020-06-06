import os

from .cpp_info import CppInfo, CppInfoComponent, CppInfoConfig, BaseCppInfo


class BaseDepsCppInfo(object):
    """ A wrapper to access cppinfo data in a convenient way """

    def __init__(self, cpp_info, remove_missing_paths=False):
        self._cpp_info = cpp_info
        self._remove_missing_paths = remove_missing_paths

    def __str__(self):
        return str(self._cpp_info)

    def _get_absolute_paths(self, _cpp_info_field):
        for it in getattr(self, _cpp_info_field):
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
        self.components = {k: DepsCppInfoComponent(self._cpp_info, v, self._remove_missing_paths)
                           for k, v in self._cpp_info.components.items()}
        self._configs = {k: DepsCppInfoConfig(self._cpp_info, v, self._remove_missing_paths)
                         for k, v in self._cpp_info.get_configs().items()}

    def __getattr__(self, item):
        if item in self._configs:
            return self._configs.get(item)
        return getattr(self._cpp_info, item)


class DepsCppInfoConfig(BaseDepsCppInfo):
    def __init__(self, pkg_cpp_info, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfoConfig), \
            "CppInfoConfig expected, got {}".format(type(cpp_info))
        super(DepsCppInfoConfig, self).__init__(cpp_info, remove_missing_paths)
        self._pkg_cpp_info = pkg_cpp_info

    def __getattr__(self, item):
        if item in BaseCppInfo._path_fields + BaseCppInfo._non_path_fields:
            # If not set at the 'config' level, return the base|package one
            field_name = '_{}'.format(item)
            field = getattr(self._cpp_info, field_name)
            if field.used:
                return getattr(self._cpp_info, item)
            else:
                return getattr(self._pkg_cpp_info, item)
        else:
            return super(DepsCppInfoConfig, self).__getattr__(item)


class DepsCppInfoComponent(BaseDepsCppInfo):

    def __init__(self, pkg_cpp_info, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfoComponent), \
            "CppInfoComponent expected, got {}".format(type(cpp_info))
        super(DepsCppInfoComponent, self).__init__(cpp_info, remove_missing_paths)
        self.requires = list(self._get_requires(str(pkg_cpp_info)))

    def _get_requires(self, pkg_name):
        # TODO: From the consumers POV we always know the name of the package, we always return
        #   full component name
        for req in self._cpp_info.requires:
            if CppInfoComponent.COMPONENTS_SCOPE in req:
                yield req
            else:
                yield CppInfoComponent.COMPONENTS_SCOPE.join([pkg_name, req])
