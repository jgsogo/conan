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

    @property
    def names(self):
        return self._names_for_generator

    def get_name(self, generator):
        return self._names_for_generator.get(generator, self.name)

    @property
    def components(self):
        return self._components

    def __getattr__(self, config):
        if not self._allow_configs:
            raise AttributeError("Invalid attribute '{}'".format(config))
        else:
            config = self._configs.setdefault(config, CppInfo(self.name, self.rootpath))
            return config


class CppInfoComponent(CppInfo):

    def __init__(self, *args, **kwargs):
        super(CppInfoComponent, self).__init__(allow_configs=False, *args, **kwargs)
        self.requires = []

    @CppInfo.components.getter
    def components(self):
        raise ConanException("Components cannot define components inside")
