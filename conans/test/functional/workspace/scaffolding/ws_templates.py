# coding=utf-8

import textwrap

workspace_yml_template = textwrap.dedent(r"""
    editables:
        {%- for editable in editables %}
        {{editable.ref}}:
            path: {{ editable.local_path }}
            layout: {{ editable.layout_file }}            
        {%- endfor %}
    workspace_generator: cmake
    root: {{ root.ref }}
""")
