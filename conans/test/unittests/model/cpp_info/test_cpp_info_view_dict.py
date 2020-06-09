import unittest

import six

from conans.errors import ConanException
from conans.model.cpp_info.cpp_info import CppInfo
from conans.model.cpp_info.cpp_info_view import CppInfoView
from conans.model.cpp_info.cpp_info_view_dict import CppInfoViewDict


class CppInfoViewDictTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create the cpp_info objects
        lib1 = CppInfo("lib1", "lib1_rootpath")
        lib1.components["cmp1"].libs = ["lib1_cmp1"]
        lib1.components["cmp1"].includedirs = ["lib1_cmp1_includes"]
        lib1.components["cmp2"].libs = ["lib1_cmp2"]
        lib1.components["cmp2"].includedirs = ["lib1_cmp2_includes"]
        lib1.clean_data()

        lib2 = CppInfo("lib2", "lib2_rootpath")
        lib2.libs = ["lib2"]
        lib2.includedirs = ["lib2_includes"]
        lib2.clean_data()

        lib3 = CppInfo("lib3", "lib3_rootpath")
        lib3.libs = ["lib3"]
        lib3.includedirs = ["lib3_includes"]
        lib3.debug.libs = ["lib3_debug"]
        lib3.debug.includedirs = ["lib3_debug_includes"]
        lib3.clean_data()

        cls.deps = CppInfoViewDict()
        cls.deps.add("lib1", CppInfoView(lib1, "lib1_version"))
        cls.deps.add("lib2", CppInfoView(lib2, "lib2_version"))
        cls.deps.add("lib3", CppInfoView(lib3, "lib3_version"))

    def test_no_basic_fields(self):
        with six.assertRaisesRegex(self, ConanException,
                                   "Cannot retrieve 'rootpath' from a list of cpp_info"):
            self.deps.rootpath
        with six.assertRaisesRegex(self, ConanException,
                                   "Cannot retrieve 'components' from a list of cpp_info"):
            self.deps.components

    def test_access_dependency(self):
        self.assertListEqual(self.deps["lib1"].components["cmp1"].libs, ["lib1_cmp1"])
        self.assertListEqual(self.deps["lib2"].libs, ["lib2"])
        self.assertListEqual(self.deps["lib3"].libs, ["lib3"])
        self.assertListEqual(self.deps["lib3"].debug.libs, ["lib3", "lib3_debug"])

    def test_aggregated_fields(self):
        self.assertListEqual(self.deps.libs, ['lib1_cmp1', 'lib1_cmp2', 'lib2', 'lib3'])
        self.assertListEqual(self.deps.include_paths,
                             ['lib1_rootpath/lib1_cmp1_includes', 'lib1_rootpath/lib1_cmp2_includes',
                              'lib2_rootpath/lib2_includes', 'lib3_rootpath/lib3_includes'])

    def test_configs_aggregated_fields(self):
        self.assertListEqual(self.deps.debug.libs,
                             ['lib1_cmp1', 'lib1_cmp2', 'lib2', 'lib3', 'lib3_debug'])
