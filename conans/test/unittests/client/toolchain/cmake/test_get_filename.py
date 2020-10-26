import unittest
from collections import namedtuple

from parameterized import parameterized

from conans.client.toolchain.cmake import CMakeToolchain
from conans.client.toolchain.cmake.generators_mixins import NinjaMixin


class GetFilenameTestCase(unittest.TestCase):

    @parameterized.expand([('Unix Makefiles', 'unixmakefiles'),
                           ('Xcode', 'xcode'),
                           ('Ninja', NinjaMixin.generator_name),
                           ('UnknownGen', 'unknowngen')])
    def test_generator_mixin_host_windows(self, generator, generator_name):
        settings_class = namedtuple('settings', ['os', ], )
        conanfile_class = namedtuple('conanfile', ['settings', 'settings_build'])

        conanfile = conanfile_class(settings=settings_class(os='Windows'),
                                    settings_build=settings_class(os='Macos'))
        tc = CMakeToolchain(conanfile, generator=generator)
        filename = tc.get_filename()
        if generator == 'Ninja':
            self.assertEquals('toolchain_{}.cmake'.format(generator_name), filename)
        else:
            self.assertEquals('toolchain.cmake'.format(generator_name), filename)

    @parameterized.expand([('Unix Makefiles', 'unixmakefiles'),
                           ('Xcode', 'xcode'),
                           ('Ninja', NinjaMixin.generator_name),
                           ('UnknownGen', 'unknowngen')])
    def test_generator_mixin_host_android(self, generator, generator_name):
        settings_class = namedtuple('settings', ['os', ], )
        conanfile_class = namedtuple('conanfile', ['settings', 'settings_build'])

        conanfile = conanfile_class(settings=settings_class(os='Android'),
                                    settings_build=settings_class(os='Macos'))
        tc = CMakeToolchain(conanfile, generator=generator)
        filename = tc.get_filename()
        if generator == 'Ninja':
            self.assertEquals('toolchain_android_{}.cmake'.format(generator_name), filename)
        else:
            self.assertEquals('toolchain_android.cmake'.format(generator_name), filename)
