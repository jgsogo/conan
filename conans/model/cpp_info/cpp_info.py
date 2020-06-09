from collections import defaultdict, OrderedDict
from copy import copy

import six

from conans.errors import ConanException
from conans.model.build_info import DEFAULT_INCLUDE, DEFAULT_LIB, DEFAULT_RES, DEFAULT_BIN, \
    DEFAULT_BUILD, DEFAULT_FRAMEWORK
from conans.util.conan_v2_mode import conan_v2_behavior


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
              "build_modules", "srcdirs", "libs", "defines", "cflags", "cxxflags", "sharedlinkflags",
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
        self._srcdirs = CppInfoField()

        # non path fields
        self._libs = CppInfoField()
        self._defines = CppInfoField()
        self._cflags = CppInfoField()
        self._cxxflags = CppInfoField()
        self._sharedlinkflags = CppInfoField()
        self._exelinkflags = CppInfoField()
        self._frameworks = CppInfoField()
        self._system_libs = CppInfoField()

    @property
    def cppflags(self):
        conan_v2_behavior("'cpp_info.cppflags' is deprecated, use 'cxxflags' instead")
        return self.cxxflags

    @cppflags.setter
    def cppflags(self, value):
        conan_v2_behavior("'cpp_info.cppflags' is deprecated, use 'cxxflags' instead")
        self.cxxflags = value

    def clean_data(self):
        pass


class CppInfo(BaseCppInfo):
    def __init__(self, ref_name, rootpath):
        super(CppInfo, self).__init__()
        self.rootpath = rootpath
        self.sysroot = ""  # TODO: Not documented! Probably something to remove
        self.name = ref_name
        self._ref_name = ref_name
        self._names_for_generator = {}
        self._components = _keydefaultdict(lambda key: CppInfoComponent(self, key))
        self._configs = {}

    def __str__(self):
        # Package name of component name as it is initially assigned
        return self._ref_name

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
            # Validate data in components
            for it in self._components.values():
                it.clean_data()

            # Order the components: topological sort
            ordered = OrderedDict()
            components = copy(self._components)
            while len(ordered) != len(self._components):
                for cmp_name, cmp in components.items():
                    if cmp_name not in [r for itcmp in components.values() for r in itcmp.requires]:
                        ordered[cmp_name] = cmp
                        del components[cmp_name]
                        break
                else:
                    raise ConanException("There is a loop in component requirements")
            self._components = ordered


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
        return self.COMPONENTS_SCOPE.join([str(self._pkg_cpp_info), self._fixed_name])

    @property
    def rootpath(self):
        return self._pkg_cpp_info.rootpath

    @property
    def names(self):
        return self._names_for_generator

    def get_name(self, generator):
        return self.COMPONENTS_SCOPE.join([self._pkg_cpp_info.get_name(generator),
                                           self._names_for_generator.get(generator, self.name)])

    def clean_data(self):
        super(CppInfoComponent, self).clean_data()
        if self._fixed_name in self._requires.values:
            raise ConanException("Component '{}' requires itself".format(self._fixed_name))
        if any(it.startswith(self.COMPONENTS_SCOPE) for it in self._requires.values):
            raise ConanException(
                "Leading character '::' not allowed in {} requires".format(self._fixed_name))


def cmp_cppinfo_components(lhs, rhs):
    """ CppInfoComponent objects have an intrinsic ordering based on the 'requires' field: 'lhs'
        is less than 'rhs' if the 'rhs' is contained in the requires listed in 'rhs'.
    """
    _, lhs = lhs
    _, rhs = rhs
    assert isinstance(lhs, CppInfoComponent), "Got '{}'".format(lhs)
    assert isinstance(rhs, CppInfoComponent), "Got '{}'".format(rhs)
    if rhs._fixed_name in lhs.requires:
        return -1
    elif lhs._fixed_name in rhs.requires:
        return 1
    else:
        return 0
