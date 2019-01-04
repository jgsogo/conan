# coding=utf-8

import os
import textwrap
import unittest

from conans.client.tools.files import load
from conans.test.utils.tools import TestClient


class HTMLInfoOutputTest(unittest.TestCase):
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
        graph_file = os.path.join(self.client.current_folder, 'graph.html')
        self.client.run('info {} --graph="{}"'.format(self.reference, graph_file))
        self.assertEqual(self.client.out, "")
        self.maxDiff = None
        self.assertEqual(load(graph_file), html_expected)


html_expected = textwrap.dedent("""\
<html>

<head>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.18.1/vis.min.js"></script>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.18.1/vis.min.css" rel="stylesheet" type="text/css"/>
</head>

<body>
  <script type="text/javascript">
    function showhideclass(id) {
      var elements = document.getElementsByClassName(id)
      for (var i = 0; i < elements.length; i++) {
        elements[i].style.display = (elements[i].style.display != 'none') ? 'none' : 'block';
      }
    }
  </script>
  <style>
    @media print {
      .noPrint {
        display: none;
      }
    }
    .button {
      background-color: #5555cc;
      border: none;
      color: white;
      padding: 5px 10px;
      text-align: center;
      text-decoration: none;
      display: inline-block;
      font-size: 18px;
    }
  </style>
  <div style="width: 100%;">
    <div id="mynetwork" style="float:left; width: 75%;"></div>
    <div style="float:right;width:25%;">
      <div id="details"  style="padding:10;" class="noPrint">Package info: no package selected</div>
      <button onclick="javascript:showhideclass('controls')" class="button noPrint">
          Show / hide graph controls
      </button>
      <div id="controls" class="controls" style="padding:5; display:none"></div>
    </div>
  </div>
  <div style="clear:both"></div>



  <script type="text/javascript">
    var nodes = new vis.DataSet([
      {id: 0, label: 'virtual', shape: 'box', color: {background: 'White'}, fulllabel: '<h3>virtual</h3><ul><li><b>id</b>: 687a2c123c63ba4b15bd0cfdc92e9d28b2cb6f19</li><li><b>url</b>: <a href="None">None</a></li><li><b>homepage</b>: <a href="None">None</a></li><li><b>topics</b>: None</li><ul>'},
{id: 1, label: 'name/version', shape: 'box', color: {background: 'OrangeRed'}, fulllabel: '<h3>name/version@user/channel</h3><ul><li><b>id</b>: 794664fdfc24800f78fd1da13e94c85804afdf1e</li><li><b>url</b>: <a href="None">None</a></li><li><b>homepage</b>: <a href="None">None</a></li><li><b>topics</b>: None</li><ul>'},
{id: 2, label: 'p2/version', shape: 'box', color: {background: 'OrangeRed'}, fulllabel: '<h3>p2/version@user/channel</h3><ul><li><b>id</b>: 34d99cf99f0a753c406c8faee89ede1a37bdeb3d</li><li><b>url</b>: <a href="None">None</a></li><li><b>homepage</b>: <a href="None">None</a></li><li><b>topics</b>: None</li><ul>'},
{id: 3, label: 'p1/version', shape: 'box', color: {background: 'OrangeRed'}, fulllabel: '<h3>p1/version@user/channel</h3><ul><li><b>id</b>: 5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9</li><li><b>url</b>: <a href="None">None</a></li><li><b>homepage</b>: <a href="None">None</a></li><li><b>topics</b>: None</li><ul>'}
    ]);
    var edges = new vis.DataSet([
     { from: 0, to: 1 },
{ from: 1, to: 2 },
{ from: 2, to: 3 }
    ]);
    var container = document.getElementById('mynetwork');
    var controls = document.getElementById('controls');
    var data = {
      nodes: nodes,
      edges: edges
    };
    var options = {
      autoResize: true,
      locale: 'en',
      edges: {
        arrows: { to: {enabled: true}},
        smooth: { enabled: false}
      },
      nodes: {
          font: {'face': 'monospace', 'align': 'left'}
      },
      layout: {
        "hierarchical": {
          "enabled": true,
          "sortMethod": "directed",
          "direction": "UD",
          nodeSpacing: 200
        }
      },
      physics: {
          enabled: false,
      },
      configure: {
        enabled: true,
        filter: 'layout physics',
        showButton: false,
        container: controls
      }
    };
    var network = new vis.Network(container, data, options);
    network.on('click', function (properties) {
                           var ids = properties.nodes;
                           var clickedNodes = nodes.get(ids);
                           var control = document.getElementById("details");
                           if(clickedNodes[0])
                              control.innerHTML = clickedNodes[0].fulllabel;
                           else
                              control.innerHTML = "<b>Package info</b>: No package selected";
                         });
  </script>
</body>
</html>
""")