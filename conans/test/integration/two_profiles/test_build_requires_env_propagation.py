import textwrap
from conans.test.utils.tools import TestClient

class TestBuildRequiresEnvPropagation:
    build_requires = textwrap.dedent("""
        import os
        from conans import ConanFile

        class Recipe(ConanFile):
            settings = "os"

            def package_info(self):
                self.env_info.CC = os.path.join(self.package_folder, "bin", "aarch64-none-elf-gcc")
                self.env_info.CC_LD = os.path.join(self.package_folder, "bin", "aarch64-none-elf-gcc")
                self.env_info.CXX = os.path.join(self.package_folder, "bin", "aarch64-none-elf-g++")
                self.env_info.CXX_LD = os.path.join(self.package_folder, "bin", "aarch64-none-elf-g++")
                self.env_info.AR = os.path.join(self.package_folder, "bin", "aarch64-none-elf-ar")
    """)

    consumer = textwrap.dedent("""
        import os
        from conans import ConanFile
        from conan.tools.meson import Meson, MesonToolchain

        class Recipe(ConanFile):
            def generate(self):
                tc = MesonToolchain(self)
                tc.generate()

            def build(self):
                for key, val in os.environ.items():
                    self.output.info(">> {}={}".format(key, val))
    """)

    profile_host = textwrap.dedent("""
        include(default)
        [build_requires]
        breq/version
    """)

    def test_build_requires_environment(self):
        t = TestClient()
        t.save({
            'build_requires.py': self.build_requires,
            'consumer.py': self.consumer,
            'profile_host': self.profile_host
        })
        t.run('create build_requires.py breq/version@ --profile=default')
        t.run('create consumer.py consumer/version@ --profile:build=default --profile:host=profile_host')
        t.run(
            'install consumer.py --profile:build=default --profile:host=profile_host')
        # assert 'consumer/version: >> CC_LD=' in t.out
        print(t.out)
