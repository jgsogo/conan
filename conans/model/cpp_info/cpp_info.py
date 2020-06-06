from collections import defaultdict

import six

from conans.errors import ConanException
from conans.model.build_info import DEFAULT_INCLUDE, DEFAULT_LIB, DEFAULT_RES, DEFAULT_BIN, \
    DEFAULT_BUILD, DEFAULT_FRAMEWORK


class _keydefaultdict(defaultdict):
    def __missing__(self, key):
        ret = self[key] = self.default_factory(key)
        return ret


class CppInfoField(object):
    def __init__(self, init_values=None):
        self.values = init_values or []
        self.used = False


class CppInfoMeta(type):
    def __init__(cls, *args, **kwargs):
        # Add properties dynamically
        def getter_property(field_name):
            field_name = '_{}'.format(field_name)

            def getter(self):
                field = getattr(self, field_name)
                field.used = True
                return field.values

            return getter

        def setter_property(field_name):
            field_name = '_{}'.format(field_name)

            def setter(self, value):
                field = getattr(self, field_name)
                field.used = True
                field.values = value

            return setter

        for it in cls._path_fields + cls._non_path_fields:
            setattr(cls, it, property(getter_property(it), setter_property(it)))
        super(CppInfoMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(CppInfoMeta)
class BaseCppInfo(object):
    """ This is the object provided in 'package_info' as 'self.cpp_info', but also
        the one offered for the components in 'self.cpp_info.components["cmp"]
    """
    _allow_configs = True
    _path_fields = ["includedirs", "libdirs", "resdirs", "bindirs", "builddirs",
                    "frameworkdirs", "build_modules"]
    _non_path_fields = ["libs", "defines", "cflags", "cxxflags", "sharedlinkflags", "exelinkflags",
                        "frameworks", "system_libs"]

    _default_values = {
        "includedirs": [DEFAULT_INCLUDE, ],
        "libdirs": [DEFAULT_LIB, ],
        "resdirs": [DEFAULT_RES, ],
        "bindirs": [DEFAULT_BIN, ],
        "builddirs": [DEFAULT_BUILD, ],
        "frameworkdirs": [DEFAULT_FRAMEWORK, ]
    }

    def __init__(self, name, rootpath):
        self.rootpath = rootpath
        self.name = self._fixed_name = name
        self._names_for_generator = {}

        # TODO: I can move all these attributes to the metaclass
        # path fields
        self._includedirs = CppInfoField([DEFAULT_INCLUDE, ])
        self._libdirs = CppInfoField([DEFAULT_LIB, ])
        self._resdirs = CppInfoField([DEFAULT_RES, ])
        self._bindirs = CppInfoField([DEFAULT_BIN, ])
        self._builddirs = CppInfoField([DEFAULT_BUILD, ])
        self._frameworkdirs = CppInfoField([DEFAULT_FRAMEWORK, ])
        self._build_modules = CppInfoField()

        # non path fields
        self._libs = CppInfoField()
        self._defines = CppInfoField()
        self._cflags = CppInfoField()
        self._cxxflags = CppInfoField()
        self._sharedlinkflags = CppInfoField()
        self._exelinkflags = CppInfoField()
        self._frameworks = CppInfoField()
        self._system_libs = CppInfoField()

    def __str__(self):
        # Package name of component name as it is initially assigned
        return self._fixed_name

    @property
    def names(self):
        return self._names_for_generator

    def get_name(self, generator):
        return self._names_for_generator.get(generator, self.name)


class CppInfo(BaseCppInfo):
    def __init__(self, name, rootpath):
        super(CppInfo, self).__init__(name=name, rootpath=rootpath)
        self._components = _keydefaultdict(lambda key: CppInfoComponent(key, rootpath))
        self._configs = {}

    @property
    def components(self):
        return self._components

    def get_configs(self):
        return self._configs

    def __getattr__(self, config):
        if not self._allow_configs:
            raise AttributeError("Invalid attribute '{}'".format(config))
        else:
            # TODO: We might allow here only those defined in 'settings.build_type'
            config = self._configs.setdefault(config, CppInfoConfig(self.name, self.rootpath))
            return config

    def clean_data(self):
        # Do not use components and root attributes at the same time
        used_attributes = any(getattr(self, '_{}'.format(it)).used
                              for it in self._path_fields + self._non_path_fields)
        if self._components and (self._configs or used_attributes):
            raise ConanException("Cannot use components together with root values")

        if self._components:
            # TODO: Order components according to requires
            # self._components = OrderedDict
            pass


class CppInfoConfig(BaseCppInfo):
    pass


class CppInfoComponent(BaseCppInfo):
    _non_path_fields = CppInfo._non_path_fields + ['requires']

    def __init__(self, *args, **kwargs):
        super(CppInfoComponent, self).__init__(*args, **kwargs)
        self._requires = CppInfoField()
