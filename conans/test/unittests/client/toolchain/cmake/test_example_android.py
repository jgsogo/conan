import unittest

from conans import CMakeToolchain, Settings
from conans.client.conf import get_default_settings_yml
from conans.client.tools import chdir, load
from conans.test.utils.mocks import MockSettings, ConanFileMock
from conans.test.utils.test_files import temp_folder


class ExampleAndroidTestCase(unittest.TestCase):

    def test_macos(self):
        settings = Settings.loads(get_default_settings_yml())
        settings.os = 'Android'
        settings.os.api_level = '23'
        settings.arch = 'x86_64'
        settings.compiler = 'clang'
        settings.compiler.version = '9'
        settings.compiler.libcxx = 'c++_shared'
        settings.build_type = 'Release'

        settings_build = Settings.loads(get_default_settings_yml())
        settings_build.os = 'Macos'
        settings_build.arch = 'x86_64'
        settings_build.compiler = 'apple-clang'
        settings_build.compiler.version = '11.0'
        settings_build.compiler.libcxx = 'libc++'
        settings_build.build_type = 'Release'
        settings_build.os = 'Macos'

        conanfile = ConanFileMock()
        conanfile.settings = settings
        conanfile.settings_build = settings_build

        tc = CMakeToolchain(conanfile)
        current_folder = temp_folder()
        with chdir(current_folder):
            tc.write_toolchain_files()
            content = load(tc.get_filename())
        print(content)
        # self.fail("AAA")
