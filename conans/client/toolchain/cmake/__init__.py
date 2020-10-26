from collections import defaultdict

from conans.client.build.cmake_flags import get_generator
from conans.client.tools import OrderedDict
from .base_toolchain import BaseToolchain
from .generators_mixins import get_mixin as get_generator_mixin
from .os_build_mixins import get_mixin as get_os_build_mixin
from .os_host_mixins import get_mixin as get_os_host_mixin


class CMakeToolchain(object):
    template_name = None
    filename = None
    template_name_prefix = 'toolchain'
    template_name_extension = '.cmake'

    def __init__(self, conanfile, generator=None, **kwargs):
        ToolchainClass = self._get_toolchain_class(conanfile, generator)
        # xbuild = cross_building(conanfile, skip_x64_x86=True)
        self._toolchain = ToolchainClass(conanfile, **kwargs)
        self.variables = Variables()
        self.preprocessor_definitions = Variables()

    @staticmethod
    def _get_toolchain_class(conanfile, generator):
        # This function is responsible of:
        #   1. build dynamically the class to instantiate

        base_mixins = []
        # 1) Build the class to instantiate
        #   - build os
        os_build = str(conanfile.settings_build.os)
        base_mixins.append(get_os_build_mixin(os_build))

        #   - host os
        os_host = str(conanfile.settings.os)
        base_mixins.append(get_os_host_mixin(os_host))

        #   - generator: provided or guess
        generator = generator or get_generator(conanfile=conanfile)
        base_mixins.append(get_generator_mixin(generator))

        base_mixins.append(BaseToolchain)
        return type('ToolchainClass', tuple(base_mixins), {})

    def get_template_names(self):
        if self.template_name:
            return [self.template_name, ]
        else:
            template_names = self._toolchain.get_template_names()
            return [
                it.format(prefix=self.template_name_prefix, extension=self.template_name_extension)
                for it in template_names]

    def get_filename(self):
        return self.filename or self._toolchain.get_filename().format(
            prefix=self.template_name_prefix, extension=self.template_name_extension)

    def write_toolchain_files(self):
        template_names = self.get_template_names()
        context = {
            'tc': self._toolchain,
            'variables': self.variables,
            'preprocessor_definitions': self.preprocessor_definitions
        }


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
