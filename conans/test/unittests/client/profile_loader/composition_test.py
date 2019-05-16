# coding=utf-8

import os
import textwrap
import unittest

from conans.client.cache.cache import ClientCache
from conans.client.migrations_settings import settings_1_14_0
from conans.client.profile_loader import profile_from_args
from conans.test.utils.test_files import temp_folder
from conans.test.utils.tools import TestBufferConanOutput
from conans.util.files import save


class ProfileComposition(unittest.TestCase):
    def setUp(self):
        self.tmp_folder = temp_folder()
        self.cache = ClientCache(self.tmp_folder, TestBufferConanOutput())
        save(self.cache.settings_path, settings_1_14_0)

    def test_profile_composition(self):
        # https://github.com/conan-io/conan/issues/5141
        save(os.path.join(self.cache.profiles_path, "default"),
             textwrap.dedent("""
                [settings]
                os=Linux
             """))
        save(os.path.join(self.cache.profiles_path, "droid32"),
             textwrap.dedent("""
                include(default)
                include(android/ndk-r18b)
                include(android/gradle/arch_selector_armeabi-v7a)
             """))
        save(os.path.join(self.cache.profiles_path, "android/ndk-r18b"),
             textwrap.dedent("""
                # ndk r18b profile
                # include(default)
                include(android/settings-only-ndk-r18b)
                
                [build_requires]
                nlo-android-toolchain/r18b@xxx/stable
             """))
        save(os.path.join(self.cache.profiles_path, "android/settings-only-ndk-r18b"),
             textwrap.dedent("""
                [settings]
                os=Android
                os.link_libcxx=static
                compiler=clang
                compiler.version=7.0
                compiler.libcxx=libc++
             """))
        save(os.path.join(self.cache.profiles_path, "android/gradle/arch_selector_armeabi-v7a"),
             textwrap.dedent("""
                [settings]
                os.api_level=19
                arch=armv7
             """))

        r = profile_from_args(["droid32", ], [], [], [], cwd=self.tmp_folder, cache=self.cache)
        #print(r.settings)
        #for it, v in r.settings.items():
        #    print("{}: {}".format(it, v))
        self.assertEqual(r.settings["os"], "Android")
        self.assertEqual(r.settings["os.link_libcxx"], "static")
        self.assertEqual(r.settings["os.api_level"], "19")
        self.assertEqual(r.settings["arch"], "armv7")
        self.assertEqual(r.settings["compiler"], "clang")
        self.assertEqual(r.settings["compiler.version"], "7.0")
        self.assertEqual(r.settings["compiler.libcxx"], "libc++")

