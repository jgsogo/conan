import unittest
import textwrap
from test.assets.genconanfile import GenConanfile
from test.utils.tools import TestClient


class SemverDirectModeTestCase(unittest.TestCase):

    def test_new_transitive_dep(self):
        t = TestClient()
        t.save({
            'libA.py': GenConanfile(),
            'libB.py': textwrap.dedent("""
                from conans import ConanFile

                class Recipe(ConanFile):
                    name = 'libB'
                    def requirements(self):
                        if self.version == '1.1.2':
                            self.requires('libA/1.1.1')
            """),
            'consumer1.py': GenConanfile().with_require("libB/1.1.1"),
            'consumer2.py': GenConanfile().with_require("libB/1.1.2")
        })

        t.run('config set general.default_package_id_mode=semver_direct_mode')
        t.run('create libA.py libA/1.1.1@')
        t.run('create libA.py libA/1.1.2@')

        # libB with different requirements, has different packageID
        t.run('create libB.py libB/1.1.1@')
        self.assertIn('libB/1.1.1:5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9 - Build', t.out)
        t.run('create libB.py libB/1.1.2@')
        self.assertIn('libB/1.1.2:8a4d75100b721bfde375a978c780bf3880a22bab - Build', t.out)

        t.run('info consumer1.py -n id')
        consumer1_id = 'dcee0041c9d2e1a6ad19c66f2d72e4cb05cc58b7'
        self.assertEquals(t.out, textwrap.dedent("""\
            libB/1.1.1
                ID: 5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9
            consumer1.py
                ID: {}
        """.format(consumer1_id)))

        t.run('info consumer2.py -n id')
        consumer2_id = 'c82c995f9c68743187a126142d30eec6217a202d'
        self.assertEquals(t.out, textwrap.dedent("""\
            libA/1.1.1
                ID: 5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9
            libB/1.1.2
                ID: 8a4d75100b721bfde375a978c780bf3880a22bab
            consumer2.py
                ID: {}
        """.format(consumer2_id)))

        # FIXME: The new requirement (even if it is not a direct requirement) is modifying the
        #   computing package_id of the 'consumer'. This is because the computation of the
        #   options-sha that is taking into account all the requirements and not only the
        #   direct ones. This is not happenning for requires-sha, here only the direct requirements
        #   are being taken into account.
        self.assertNotEqual(consumer1_id, consumer2_id)  # FIXME: Known bug
