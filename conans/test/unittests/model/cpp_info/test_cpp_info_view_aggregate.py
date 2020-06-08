import unittest

import six

from conans.errors import ConanException
from conans.model.cpp_info.cpp_info import CppInfo
from conans.model.cpp_info.cpp_info_view import CppInfoView
from conans.model.cpp_info.cpp_info_view_agg import CppInfoViewAggregated


class CppInfoViewAggregateTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create the cpp_info objects
        app = CppInfo("app", "app_rootpath")
        app.libs = ["app"]
        app.includedirs = ["app_includes"]
        app.debug.libs = ["app_debug"]

        lib = CppInfo("lib", "lib_rootpath")
        lib.libs = ["lib"]
        lib.includedirs = ["lib_includes"]
        lib.debug.libs = ["lib_debug"]

        req = CppInfo("req", "req_rootpath")
        req.libs = ["req"]
        req.includedirs = ["req_includes"]
        req.debug.libs = ["req_debug"]

        # Create the views
        app_view = CppInfoView(app, "app_version", "app_description")
        lib_view = CppInfoView(lib, "lib_version", "lib_description")
        req_view = CppInfoView(req, "req_version", "req_description")

        # Aggregate
        cls.req_agg = CppInfoViewAggregated(req_view)
        cls.lib_agg = CppInfoViewAggregated(lib_view)
        cls.lib_agg.add_requirement(req_view)
        cls.app_agg = CppInfoViewAggregated(app_view)
        cls.app_agg.add_requirement(lib_view)
        cls.app_agg.add_requirement(req_view)

    def test_no_components(self):
        with six.assertRaisesRegex(self, ConanException, "Do not requests 'components'"):
            self.app_agg.components

    def test_basic_fields(self):
        self.assertEqual(self.req_agg.rootpath, "req_rootpath")
        self.assertEqual(self.lib_agg.rootpath, "lib_rootpath")
        self.assertEqual(self.app_agg.rootpath, "app_rootpath")

        self.assertEqual(self.req_agg.version, "req_version")
        self.assertEqual(self.lib_agg.version, "lib_version")
        self.assertEqual(self.app_agg.version, "app_version")

        self.assertEqual(self.req_agg.get_name("cmake"), "req")
        self.assertEqual(self.lib_agg.get_name("cmake"), "lib")
        self.assertEqual(self.app_agg.get_name("cmake"), "app")

    def test_include_paths(self):
        self.assertListEqual(self.req_agg.include_paths, ['req_rootpath/req_includes'])
        self.assertListEqual(self.lib_agg.include_paths,
                             ['lib_rootpath/lib_includes', 'req_rootpath/req_includes'])
        self.assertListEqual(self.app_agg.include_paths,
                             ['app_rootpath/app_includes', 'lib_rootpath/lib_includes',
                              'req_rootpath/req_includes'])

    def test_configs(self):
        self.assertListEqual(self.req_agg.libs, ['req'])
        self.assertListEqual(self.req_agg.debug.libs, ['req', 'req_debug'])

        self.assertListEqual(self.lib_agg.libs, ['lib', 'req'])
        self.assertListEqual(self.lib_agg.debug.libs, ['lib', 'lib_debug', 'req', 'req_debug'])

        self.assertListEqual(self.app_agg.libs, ['app', 'lib', 'req'])
        self.assertListEqual(self.app_agg.debug.libs,
                             ['app', 'app_debug', 'lib', 'lib_debug', 'req', 'req_debug'])


class CppInfoViewAggregateAssymetricTestCase(unittest.TestCase):
    """ The requirement has a config that doesn't exist in the main package """

    def test_requirement_config(self):
        app = CppInfo("app", "app_rootpath")
        app.libs = ["app"]

        lib = CppInfo("lib", "lib_rootpath")
        lib.libs = ["lib"]
        lib.debug.libs = ["lib_debug"]

        # Create the views
        app_view = CppInfoView(app, "app_version", "app_description")
        lib_view = CppInfoView(lib, "lib_version", "lib_description")

        # Aggregate
        lib_agg = CppInfoViewAggregated(lib_view)
        app_agg = CppInfoViewAggregated(app_view)
        app_agg.add_requirement(lib_view)

        self.assertEqual(app_agg.libs, ['app', 'lib'])
        self.assertEqual(lib_agg.debug.libs, ['lib', 'lib_debug'])
        self.assertEqual(app_agg.debug.libs, ['app', 'lib', 'lib_debug'])
