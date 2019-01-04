# coding=utf-8

import os
import textwrap
import unittest

from conans.client.tools.files import load
from conans.test.utils.tools import TestClient


class HTMLSearchOutputTest(unittest.TestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Lib(ConanFile):
            settings = "build_type"
            
            description = "{}"
        """)

    def setUp(self):
        self.client = TestClient()
        files = {'conanfile.py': self.conanfile.format("old description")}
        self.client.save(files)
        self.reference = "zlib/1.0@user/channel"
        self.client.run("create . {} -s build_type=Release".format(self.reference))

        # To get outdated packages
        files = {'conanfile.py': self.conanfile.format("new description")}
        self.client.save(files)
        self.client.run("create . {} -s build_type=Debug".format(self.reference))

    def test_basic(self):
        table_filename = os.path.join(self.client.current_folder, 'table.html')
        self.client.run('search {} --table="{}"'.format(self.reference, table_filename))
        self.assertEqual(self.client.out, "")
        self.assertEqual(load(table_filename), table_html_content)


table_html_content = textwrap.dedent("""\
<style>
    table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
.selected {
    border: 3px solid black;
}
</style>
<script type="text/javascript">
    function handleEvent(id) {
        selected = document.getElementsByClassName('selected');
        if (selected[0]) selected[0].className = '';
        cell = document.getElementById(id);
        cell.className = 'selected';
        elem = document.getElementById('SelectedPackage');
        elem.innerHTML = id;
    }

</script>
<h1>zlib/1.0@user/channel</h1>
    
<h2>'None':</h2>
<table>
<tr>
<th></th>
<th>Debug</th>
<th>Release</th>
</tr>
<tr>
<td>None None None</td>
<td bgcolor=#00ff00 id="5a67a79dbc25fd0fa149a0eb7a20715189a0d988" onclick=handleEvent("5a67a79dbc25fd0fa149a0eb7a20715189a0d988")></td>
<td bgcolor=#ffff00 id="4024617540c4f240a6a5e8911b0de9ef38a11a72" onclick=handleEvent("4024617540c4f240a6a5e8911b0de9ef38a11a72")></td>
</tr>
</table>
<br>Selected: <div id="SelectedPackage"></div>
<br>Legend<br><table><tr><td bgcolor=#ffff00>&nbsp;&nbsp;&nbsp;&nbsp;</td<td>Outdated from recipe</td></tr><tr><td bgcolor=#00ff00>&nbsp;&nbsp;&nbsp;&nbsp;</td><td>Updated</td></tr><tr><td>&nbsp;&nbsp;&nbsp;&nbsp;</td><td>Non existing</td></tr></table>""")
