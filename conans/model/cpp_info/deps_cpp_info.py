import os

import six

from .cpp_info import CppInfo, CppInfoComponent, CppInfoConfig, BaseCppInfo


class DepsCppInfoMeta(type):
    def __init__(cls, *args, **kwargs):
        # Add properties dynamically
        def getter_property(inner_field):
            def getter(self):
                ret = []
                for it in getattr(self, inner_field):
                    fullpath = os.path.join(self._cpp_info.rootpath, it)
                    if not self._remove_missing_paths:
                        ret.append(fullpath)
                    elif os.path.exists(fullpath):
                        ret.append(fullpath)
                return ret

            return getter

        for outter, inner in cls.FIELDS_PATH_MAPPING.items():
            setattr(cls, outter, property(getter_property(inner)))
        super(DepsCppInfoMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(DepsCppInfoMeta)
class BaseDepsCppInfo(object):
    """ A wrapper to access cppinfo data in a convenient way """

    FIELDS_PATH_MAPPING = {
        "include_paths": "includedirs",
        "lib_paths": "libdirs",
        "bin_paths": "bindirs",
        "build_paths": "builddirs",
        "res_paths": "resdirs",
        "framework_paths": "frameworkdirs",
        "build_modules_paths": "build_modules",
    }

    def __init__(self, cpp_info, remove_missing_paths=False):
        self._cpp_info = cpp_info
        self._remove_missing_paths = remove_missing_paths

    def __str__(self):
        return str(self._cpp_info)

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
        if item in BaseCppInfo.FIELDS:
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
