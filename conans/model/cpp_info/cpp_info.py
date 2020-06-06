from conans.model.build_info import DEFAULT_INCLUDE, DEFAULT_LIB, DEFAULT_RES, DEFAULT_BIN, DEFAULT_BUILD, DEFAULT_FRAMEWORK
from conans.errors import ConanException
from collections import defaultdict


class _keydefaultdict(defaultdict):
    def __missing__(self, key):
        ret = self[key] = self.default_factory(key)
        return ret



class CppInfo(object):
    """ This is the object provided in 'package_info' as 'self.cpp_info', but also
        the one offered for the components in 'self.cpp_info.components["cmp"]
    """

    def __init__(self, name, rootpath, allow_configs=True):
        self._allow_configs = allow_configs
        self.rootpath = rootpath
        self.name = name
        self._fixed_name = name
        self._names_for_generator = {}
        self._components = _keydefaultdict(lambda key: CppInfoComponent(key, rootpath))
        self._configs = {}

        # path fields
        self.includedirs = [DEFAULT_INCLUDE, ]
        self.libdirs = [DEFAULT_LIB, ]
        self.resdirs = [DEFAULT_RES, ]
        self.bindirs = [DEFAULT_BIN, ]
        self.builddirs = [DEFAULT_BUILD, ]
        self.frameworkdirs = [DEFAULT_FRAMEWORK, ]
        self.build_modules = []

        # non path fields
        self.libs = []
        self.defines = []
        self.cflags = []
        self.cxxflags = []
        self.sharedlinkflags = []
        self.exelinkflags = []
        self.frameworks = []
        self.system_libs = []

    def __str__(self):
        # Package name of component name as it is assigned in the dictionary
        return self._fixed_name

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
            config = self._configs.setdefault(config, CppInfoConfig(self.name, self.rootpath))
            return config

    def clean_data(self):
        # Do not use components and root attributes at the same time
        default = CppInfo("_", "_")
        if self._components and\
            (self._configs
             or self.includedirs != default.includedirs
             or self.libdirs != default.libdirs
             or self.resdirs != default.resdirs
             or self.bindirs != default.bindirs
             or self.builddirs != default.builddirs
             or self.frameworkdirs != default.frameworkdirs
             or self.build_modules != default.build_modules
             or self.libs != default.libs
             or self.defines != default.defines
             or self.cflags != default.cflags
             or self.cxxflags != default.cxxflags
             or self.sharedlinkflags != default.sharedlinkflags
             or self.exelinkflags != default.exelinkflags
             or self.frameworks != default.frameworkdirs
             or self.system_libs != default.system_libs):
            raise ConanException("Cannot use components together with root values")

        # Clean fields so we can iterate them safely
        if self._components:
            self.includedirs = self.libdirs = self.resdirs = self.bindirs = self.builddirs \
                = self.frameworkdirs = self.build_modules = []
            self.libs = self.defines = self.cflags = self.cxxflags = self.sharedlinkflags \
                = self.exelinkflags = self.frameworks = self.system_libs = []

            for cmp in self._components.values():
                cmp.clean_data()

            # TODO: Order components according to requires
        else:
            self._components = None


class CppInfoConfig(CppInfo):
    def __init__(self, *args, **kwargs):
        super(CppInfoConfig, self).__init__(allow_configs=False, *args, **kwargs)

    @CppInfo.components.getter
    def components(self):
        raise ConanException("Components cannot define components inside")


class CppInfoComponent(CppInfo):

    def __init__(self, *args, **kwargs):
        super(CppInfoComponent, self).__init__(allow_configs=False, *args, **kwargs)
        self.requires = []

    @CppInfo.components.getter
    def components(self):
        raise ConanException("Components cannot define components inside")
