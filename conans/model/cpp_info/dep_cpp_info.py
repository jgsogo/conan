import os

import six

from .cpp_info import CppInfo, CppInfoComponent, CppInfoConfig, BaseCppInfo


class DepCppInfoMeta(type):
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
        super(DepCppInfoMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(DepCppInfoMeta)
class BaseDepCppInfo(object):
    """ A wrapper to access cppinfo data in a convenient way """

    FIELDS_PATH_MAPPING = {
        "include_paths": "includedirs",
        "lib_paths": "libdirs",
        "bin_paths": "bindirs",
        "build_paths": "builddirs",
        "res_paths": "resdirs",
        "framework_paths": "frameworkdirs",
        "build_modules_paths": "build_modules",
        "src_paths": "srcdirs",  # TODO: Documented?
    }

    def __init__(self, cpp_info, remove_missing_paths=False):
        self._cpp_info = cpp_info
        self._remove_missing_paths = remove_missing_paths
        self.public_deps = []  # TODO: Why this here?
        self.sysroot = ""  # TODO: Where is this one populated?

    def __str__(self):
        return str(self._cpp_info)

    def __getattr__(self, item):
        return getattr(self._cpp_info, item)


class DepCppInfo(BaseDepCppInfo):
    def __init__(self, version, description, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfo), "CppInfo expected, got {}".format(type(cpp_info))
        super(DepCppInfo, self).__init__(cpp_info, remove_missing_paths)

        self._version = version
        self._description = description
        self.components = {k: DepCppInfoComponent(self._cpp_info, v, self._remove_missing_paths)
                           for k, v in self._cpp_info.components.items()}
        self._configs = {k: DepCppInfoConfig(self._cpp_info, v, self._remove_missing_paths)
                         for k, v in self._cpp_info.get_configs().items()}

    @property
    def version(self):
        return self._version

    @property
    def description(self):
        return self._description

    @property
    def configs(self):
        return self._configs

    def get_configs(self):
        # TODO: Avoid duplicity
        return self._configs

    def __getattr__(self, item):
        if item in self._configs:
            return self._configs.get(item)
        return getattr(self._cpp_info, item)


class DepCppInfoConfig(BaseDepCppInfo):
    def __init__(self, pkg_cpp_info, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfoConfig), \
            "CppInfoConfig expected, got {}".format(type(cpp_info))
        super(DepCppInfoConfig, self).__init__(cpp_info, remove_missing_paths)
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
            return super(DepCppInfoConfig, self).__getattr__(item)


class DepCppInfoComponent(BaseDepCppInfo):

    def __init__(self, pkg_cpp_info, cpp_info, remove_missing_paths=False):
        assert isinstance(cpp_info, CppInfoComponent), \
            "CppInfoComponent expected, got {}".format(type(cpp_info))
        super(DepCppInfoComponent, self).__init__(cpp_info, remove_missing_paths)
        self.requires = list(self._get_requires(str(pkg_cpp_info)))

    def _get_requires(self, pkg_name):
        # TODO: From the consumers POV we always know the name of the package, we always return
        #   full component name
        for req in self._cpp_info.requires:
            if CppInfoComponent.COMPONENTS_SCOPE in req:
                yield req
            else:
                yield CppInfoComponent.COMPONENTS_SCOPE.join([pkg_name, req])
