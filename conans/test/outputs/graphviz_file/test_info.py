# coding=utf-8

import os
import textwrap
import unittest

from conans.client.tools.files import load
from conans.test.utils.tools import TestClient


class GraphvizInfoOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Lib(ConanFile):
            {body}
        """)

    def setUp(self):
        self.client = TestClient()
        self.client.run("profile new --detect default")

        p1 = "p1/version@user/channel"
        files = {'conanfile.py': self.conanfile.format(body="pass")}
        self.client.save(files)
        self.client.run("export . {}".format(p1))

        p2 = "p2/version@user/channel"
        files = {'conanfile.py': self.conanfile.format(body='requires = "{}"'.format(p1))}
        self.client.save(files)
        self.client.run("export . {}".format(p2))

        self.reference = "name/version@user/channel"
        files = {'conanfile.py': self.conanfile.format(body='requires = "{}"'.format(p2))}
        self.client.save(files)
        self.client.run("export . {}".format(self.reference))

    def test_basic(self):
        graph_file = os.path.join(self.client.current_folder, 'graph.dot')
        self.client.run('info {} --graph="{}"'.format(self.reference, graph_file))
        self.assertEqual(self.client.out, "")
        lines = load(graph_file).splitlines()
        self.assertEqual(lines[0], "digraph {")
        self.assertEqual(lines[-1], "}")
        self.assertListEqual(sorted([it.strip() for it in lines[1:-1]]),
                             ['"name/version@user/channel" -> {"p2/version@user/channel"}',
                              '"p2/version@user/channel" -> {"p1/version@user/channel"}',
                              '"virtual" -> {"name/version@user/channel"}', ])
