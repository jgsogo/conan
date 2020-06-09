import os
from collections import OrderedDict

import six

from .cpp_info import CppInfo, CppInfoComponent


# TODO: For all this getters, 'yielding' is the way to go, but we might need to prepare
#  generators before, meanwhile, we will copy the lists so they are not modified


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


def _getter_agg_if_components(field_name):
    """ If there are components, aggregate their information, otherwise forward """
    def getter(self):
        if self.components:
            ret = []
            # Aggregate all components
            for _, component in self.components.items():
                ret += getattr(component, field_name)
            # Remove duplicates, keep the latest seen
            seen = set()
            seen_add = seen.add
            return [x for x in ret[::-1] if not (x in seen or seen_add(x))][::-1]
        else:
            return list(getattr(self._cpp_info, field_name))
    return getter


class BaseCppInfoViewMeta(type):
    def __init__(cls, *args, **kwargs):
        for it in CppInfo.FIELDS:
            setattr(cls, it, property(cls._getter_retrieve(it)))

        for outter, inner in cls.FIELDS_PATH_MAPPING.items():
            setattr(cls, outter, property(cls._getter_abs_paths(inner)))

        super(BaseCppInfoViewMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(BaseCppInfoViewMeta)
class BaseCppInfoView(object):
    """ Once cpp_info object is populated, we can no longer modify its members, only
        access is permitted and some extra fields are added.
         * For the configs, information from the main 'cpp_info' object is prepended.
         * If there are components, information is added at the base level
    """

    _getter_retrieve = _getter_forward
    _getter_abs_paths = _getter_abs_paths

    FIELDS_PATH_MAPPING = {
        "include_paths": "includedirs",
        "lib_paths": "libdirs",
        "bin_paths": "bindirs",
        "build_paths": "builddirs",
        "res_paths": "resdirs",
        "framework_paths": "frameworkdirs",
        "build_modules_paths": "build_modules",
        "src_paths": "srcdirs",
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

    _getter_retrieve = _getter_agg_if_components
    AGGREGATE_FIELDS = CppInfo.FIELDS + list(BaseCppInfoView.FIELDS_PATH_MAPPING.keys())

    def __init__(self, cpp_info, version, description=None):
        super(CppInfoView, self).__init__(cpp_info)
        self._cpp_info.clean_data()

        self._version = version
        self._description = description

        self.components = OrderedDict()
        for k, v in self._cpp_info.components.items():
            self.components[k] = CppInfoViewComponents(self, v)

        self._configs = {k: CppInfoViewConfig(self, v)
                         for k, v in self._cpp_info.get_configs().items()}

    @property
    def version(self):
        return self._version

    @property
    def description(self):
        return self._description

    def get_configs(self):
        return self._configs

    def __getattr__(self, item):
        if item in self._configs:
            return self._configs.get(item)
        return super(CppInfoView, self).__getattr__(item)


class CppInfoViewConfig(BaseCppInfoView):
    _getter_retrieve = _getter_append

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
