import os

import six

from .cpp_info import CppInfo, CppInfoComponent


def _getter_forward(field_name):
    """ Forward to the inner 'self._cpp_info' field """

    def getter(self):
        return list(getattr(self._cpp_info, field_name))

    return getter


def _getter_abs_paths(inner_field):
    """ Build absolute paths before retrieving values """

    def getter(self):
        ret = []
        for it in getattr(self, inner_field):
            fullpath = os.path.join(self._cpp_info.rootpath, it)
            ret.append(fullpath)
        return ret

    return getter


def _getter_append(field_name):
    """ Append self values to the ones in the package """

    def getter(self):
        ret = list(getattr(self._pkg_cpp_info, field_name))
        ret += getattr(self._cpp_info, field_name)
        return ret

    return getter


class BaseCppInfoViewMeta(type):
    def __init__(cls, *args, **kwargs):
        for it in CppInfo.FIELDS:
            setattr(cls, it, property(cls._getter_forward(it)))

        for outter, inner in cls.FIELDS_PATH_MAPPING.items():
            setattr(cls, outter, property(cls._getter_abs_paths(inner)))

        super(BaseCppInfoViewMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(BaseCppInfoViewMeta)
class BaseCppInfoView(object):
    """ Once cpp_info object is populated, we can no longer modify its members, only
        access is permitted and some extra fields are added.
    """

    _getter_forward = _getter_forward
    _getter_abs_paths = _getter_abs_paths

    FIELDS_PATH_MAPPING = {
        "include_paths": "includedirs",
        "lib_paths": "libdirs",
        "bin_paths": "bindirs",
        "build_paths": "builddirs",
        "res_paths": "resdirs",
        "framework_paths": "frameworkdirs",
        "build_modules_paths": "build_modules",
    }

    def __init__(self, cpp_info):
        self._cpp_info = cpp_info

    def __str__(self):
        return str(self._cpp_info)

    @property
    def name(self):
        raise RuntimeError("Using 'get_name(generator)' to get the name for a generator")

    def __getattr__(self, item):
        return getattr(self._cpp_info, item)


class CppInfoView(BaseCppInfoView):

    def __init__(self, cpp_info, version, description=None):
        super(CppInfoView, self).__init__(cpp_info)

        self._version = version
        self._description = description

        # TODO: OrderedDict
        self.components = {k: CppInfoViewComponents(self, v)
                           for k, v in self._cpp_info.components.items()}
        self._configs = {k: CppInfoViewConfig(self, v)
                         for k, v in self._cpp_info.get_configs().items()}

    @property
    def version(self):
        return self._version

    @property
    def description(self):
        return self._description

    def __getattr__(self, item):
        if item in self._configs:
            return self._configs.get(item)
        return getattr(self._cpp_info, item)


class CppInfoViewConfig(BaseCppInfoView):
    _getter_forward = _getter_append

    def __init__(self, pkg_cpp_info, cpp_info):
        super(CppInfoViewConfig, self).__init__(cpp_info)
        self._pkg_cpp_info = pkg_cpp_info


class CppInfoViewComponents(BaseCppInfoView):
    def __init__(self, pkg_cpp_info, cpp_info):
        super(CppInfoViewComponents, self).__init__(cpp_info)
        self._requires = list(self._get_requires(str(pkg_cpp_info)))

    @property
    def requires(self):
        return self._requires

    def _get_requires(self, pkg_name):
        # TODO: From the consumers POV we always know the name of the package, we always return
        #   full component name
        for req in self._cpp_info.requires:
            if CppInfoComponent.COMPONENTS_SCOPE in req:
                yield req
            else:
                yield CppInfoComponent.COMPONENTS_SCOPE.join([pkg_name, req])
