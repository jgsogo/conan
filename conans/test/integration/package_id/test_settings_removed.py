import textwrap
from conans.test.utils.tools import TestClient

class TestSettingsRemoved:
    conanfile = textwrap.dedent("""
            from conans import ConanFile

            class Recipe(ConanFile):
                settings = "os", "arch", "compiler", "build_type"

                def package_id(self):
                    del self.info.settings.compiler
        """)

    profile = textwrap.dedent("""
        [settings]
        os=Macos
        arch=x86_64
        compiler=apple-clang
        compiler.version=12.0
        compiler.libcxx=libc++
        build_type=Release
    """)

    consumer = textwrap.dedent("""
        [settings]
        os=Macos
        arch=x86_64
        build_type=Release
    """)

    def test_remove_in_package_id(self):
        t = TestClient()
        t.save({'conanfile.py': self.conanfile,
                'pr_generate': self.profile,
                'pr_consumer': self.consumer})

        pkg_id = '801752c0480319b8e090188c566245a78e9abcf4'
        t.run('create conanfile.py tool/version@ --profile=pr_generate')
        assert 'tool/version:{}'.format(pkg_id) in t.out
        t.run('create conanfile.py tool/version@ --profile=pr_generate -s compiler.version=11.0')
        assert 'tool/version:{}'.format(pkg_id) in t.out

        t.run('info tool/version@ --profile=pr_generate')
        t.run('info tool/version@ --profile=pr_consumer')
        print(t.out)
