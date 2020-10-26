from collections import defaultdict

from conans.client.tools import cross_building, OrderedDict
from .android import CMakeAndroidToolchain
from .generic import CMakeGenericToolchain
from ...build.cmake_flags import get_generator


def CMakeToolchain(conanfile, generator, **kwargs):
    # This function is responsible of:
    #   1. build dynamically the class to instantiate
    #   2. get/compute the template to use
    #   3. instantiate and render

    base_mixins = []
    # 1) Build the class to instantiate
    #   - generator: provided or guess
    generator = generator or get_generator(conanfile=conanfile)
    #   - coordinates: xbuilding, os:host
    xbuild = cross_building(conanfile, skip_x64_x86=True)
    os_host = conanfile.settings.os

    toolchain = None

    # 2) Return the class that will sel
    tc = CMakeToolchainRenderer(toolchain)
    return tc


class Variables(OrderedDict):
    _configuration_types = None  # Needed for py27 to avoid infinite recursion

    def __init__(self):
        super(Variables, self).__init__()
        self._configuration_types = {}

    def __getattribute__(self, config):
        try:
            return super(Variables, self).__getattribute__(config)
        except AttributeError:
            return self._configuration_types.setdefault(config, dict())

    @property
    def configuration_types(self):
        # Reverse index for the configuration_types variables
        ret = defaultdict(list)
        for conf, definitions in self._configuration_types.items():
            for k, v in definitions.items():
                ret[k].append((conf, v))
        return ret


class CMakeToolchainRenderer(object):
    template_name = None

    def __init__(self, toolchain):
        self._toolchain = toolchain
        self.variables = Variables()
        self.preprocessor_definitions = Variables()

    def get_template_names(self):
        if self.template_name:
            return [self.template_name, ]
        return self._toolchain.get_template_names()

    def write_toolchain_files(self):
        template_names = self.get_template_names()
        context = {
            'tc': self._toolchain,
            'variables': self.variables,
            'preprocessor_definitions': self.preprocessor_definitions
        }
