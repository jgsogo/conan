import unittest
from collections import namedtuple

from parameterized import parameterized

from conans.client.toolchain.cmake import CMakeToolchain
from conans.client.toolchain.cmake.generators_mixins import NinjaMixin


class GetTemplateNamesTestCase(unittest.TestCase):

    @parameterized.expand([('Unix Makefiles', 'unixmakefiles'),
                           ('Xcode', 'xcode'),
                           ('Ninja', NinjaMixin.generator_name),
                           ('UnknownGen', 'unknowngen')])
    def test_generator_mixin(self, generator, generator_name):
        settings_class = namedtuple('settings', ['os', ], )
        conanfile_class = namedtuple('conanfile', ['settings', 'settings_build'])

        conanfile = conanfile_class(settings=settings_class(os='Windows'),
                                    settings_build=settings_class(os='Macos'))
        tc = CMakeToolchain(conanfile, generator=generator)
        template_names = tc.get_template_names()
        self.assertListEqual(template_names, [
            'macos/toolchain_windows_{}.cmake'.format(generator_name),
            'macos/toolchain_{}.cmake'.format(generator_name),
            'macos/toolchain_windows.cmake',
            'macos/toolchain.cmake',
            'toolchain_windows_{}.cmake'.format(generator_name),
            'toolchain_{}.cmake'.format(generator_name),
            'toolchain_windows.cmake',
            'toolchain.cmake',
        ])
