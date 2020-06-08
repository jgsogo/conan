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

    def reset(self):
        self.values = []
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

        for it in cls.FIELDS:
            setattr(cls, it, property(getter_property(it), setter_property(it)))
        super(CppInfoMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(CppInfoMeta)
class BaseCppInfo(object):
    """ This is the base object provided in 'package_info' as 'self.cpp_info', also
        the one offered for the components in 'self.cpp_info.components["cmp"]' and for
        'configs'. Just raw data.
    """
    _allow_configs = True
    FIELDS = ["includedirs", "libdirs", "resdirs", "bindirs", "builddirs", "frameworkdirs",
              "build_modules", "libs", "defines", "cflags", "cxxflags", "sharedlinkflags",
              "exelinkflags", "frameworks", "system_libs"]

    def __init__(self):
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


class CppInfo(BaseCppInfo):
    def __init__(self, name, rootpath):
        super(CppInfo, self).__init__()
        self.rootpath = rootpath
        self.name = name
        self._package_name = name
        self._names_for_generator = {}
        self._components = _keydefaultdict(lambda key: CppInfoComponent(self, key))
        self._configs = {}

    def __str__(self):
        # Package name of component name as it is initially assigned
        return self._package_name

    @property
    def names(self):
        return self._names_for_generator

    def get_name(self, generator):
        return self._names_for_generator.get(generator, self.name)

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
            config = self._configs.setdefault(config, CppInfoConfig(self))
            return config

    def clean_data(self):
        # Do not use components and root attributes at the same time
        used_attributes = any(getattr(self, '_{}'.format(it)).used for it in self.FIELDS)
        if self._components and (self._configs or used_attributes):
            raise ConanException("Cannot use components together with root values")

        if self._components:
            for it in self.FIELDS:
                getattr(self, '_{}'.format(it)).reset()
            # TODO: Order components according to requires
            # self._components = OrderedDict
            pass


class CppInfoConfig(BaseCppInfo):
    def __init__(self, pkg_cpp_info):
        super(CppInfoConfig, self).__init__()
        self._pkg_cpp_info = pkg_cpp_info

    def __str__(self):
        return str(self._pkg_cpp_info)

    @property
    def name(self):
        return self._pkg_cpp_info.name

    def get_name(self, generator):
        return self._pkg_cpp_info.get_name(generator)

    @property
    def rootpath(self):
        return self._pkg_cpp_info.rootpath


class CppInfoComponent(BaseCppInfo):
    COMPONENTS_SCOPE = '::'
    FIELDS = CppInfo.FIELDS + ['requires']

    def __init__(self, pkg_cpp_info, cpm_name):
        super(CppInfoComponent, self).__init__()
        self._pkg_cpp_info = pkg_cpp_info
        self.name = cpm_name
        self._fixed_name = cpm_name
        self._names_for_generator = {}
        self._requires = CppInfoField()

    def __str__(self):
        return self._fixed_name
        # return self.COMPONENTS_SCOPE.join([str(self._pkg_cpp_info), self._fixed_name])

    @property
    def rootpath(self):
        return self._pkg_cpp_info.rootpath

    @property
    def names(self):
        return self._names_for_generator

    def get_name(self, generator):
        return self.COMPONENTS_SCOPE.join([self._pkg_cpp_info.get_name(generator),
                                           self._names_for_generator.get(generator, self.name)])
