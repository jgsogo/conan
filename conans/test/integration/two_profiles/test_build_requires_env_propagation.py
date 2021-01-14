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

        class Recipe(ConanFile):
            build_requires = 'breq/version'
            def build(self):
                for key, val in os.environ.items():
                    self.output.info(">> {}={}".format(key, val))
    """)

    def test_build_requires_environment(self):
        t = TestClient()
        t.save({
            'build_requires.py': self.build_requires,
            'consumer.py': self.consumer
        })
        t.run('create build_requires.py breq/version@ --profile=default')
        t.run('create consumer.py consumer/version@ --profile:build=default --profile:host=default')
        print(t.out)
