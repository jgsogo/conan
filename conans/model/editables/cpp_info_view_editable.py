
from conans.model.cpp_info.cpp_info_view import CppInfoView, CppInfoViewConfig, CppInfoViewComponents
from conans.model.cpp_info.cpp_info_view import _getter_abs_paths
from collections import OrderedDict
import six

"""
Editable packages add a layer of indirection on top of 'CppInfoView' objects to inject
the values for the fields defined in the layout files

This layer must be added to the base 'conanfile.cpp_info' object, but also to the
components and configs if they exists.
"""


class BaseCppInfoViewEditableMeta(type):
    def __init__(cls, *args, **kwargs):
        for outter, inner in CppInfoView.FIELDS_PATH_MAPPING.items():
            setattr(cls, outter, property(_getter_abs_paths(inner)))

        super(BaseCppInfoViewEditableMeta, cls).__init__(*args, **kwargs)


@six.add_metaclass(BaseCppInfoViewEditableMeta)
class BaseCppInfoViewEditable(object):
    _expected_class = None
    OVERRIDEN_FIELDS = list(CppInfoView.FIELDS_PATH_MAPPING.values())

    def __init__(self, cpp_info_view, editable_data):
        assert isinstance(cpp_info_view, self._expected_class), "Got '{}' type".format(type(cpp_info_view))
        self._cpp_info_view = cpp_info_view
        self._editable_data = editable_data

    def __str__(self):
        return str(self._cpp_info_view)

    def __getattr__(self, item):
        if item in self.OVERRIDEN_FIELDS:
            return self._editable_data.get(item, [])
        else:
            return getattr(self._cpp_info_view, item)


class CppInfoViewEditable(BaseCppInfoViewEditable):
    _expected_class = CppInfoView

    def __init__(self, cpp_info_view, editable_data):
        super(CppInfoViewEditable, self).__init__(cpp_info_view, editable_data)
        assert isinstance(cpp_info_view, CppInfoView), "Got '{}' type".format(type(cpp_info_view))

        self.components = OrderedDict()
        for k, v in self._cpp_info_view.components.items():
            # TODO: Get from 'editable_data' the members that belong to this component
            editable_data_for_component = {}
            self.components[k] = CppInfoViewComponents(v, editable_data_for_component)

        self._configs = {}
        for k, v in self._cpp_info_view.get_configs().items():
            if k == '__len__':
                continue  # TODO: How that 'len' arrives here
            editable_data_for_config = {}
            self._configs[k] = CppInfoViewConfig(v, editable_data_for_config)

    def get_configs(self):
        return self._configs


class CppInfoViewEditableComponents(BaseCppInfoViewEditable):
    _expected_class = CppInfoViewComponents


class CppInfoViewEditableConfig(BaseCppInfoViewEditable):
    _expected_class = CppInfoViewConfig

