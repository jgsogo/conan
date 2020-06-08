from conans.errors import ConanException
from .cpp_info import BaseCppInfo
from .cpp_info_view import CppInfoView, CppInfoViewConfig


class BaseCppInfoViewAggregated(object):
    """ Some generators need the information of the current 'cpp_info' and all its
        required ones. This aggregation over 'cpp_info' view append the information from
        all the dependencies when returning values.
    """

    _expected_class = None
    AGGREGATE_FIELDS = BaseCppInfo.FIELDS + list(CppInfoView.FIELDS_PATH_MAPPING.keys())

    def __init__(self, cpp_info_view):
        assert isinstance(cpp_info_view, self._expected_class), "Instance is '{}'".format(
            type(cpp_info_view))
        self._cpp_info_view = cpp_info_view
        self._requirements = []

    def add_requirement(self, require_cpp_info_view):
        assert isinstance(require_cpp_info_view, self._expected_class), "Instance is '{}'".format(
            type(require_cpp_info_view))
        assert require_cpp_info_view not in self._requirements, "Diamonds have to resolved outside"
        self._requirements.append(require_cpp_info_view)

    @property
    def components(self):
        raise ConanException("Do not requests 'components' for an aggregated view, they should"
                             " be used only with a targets approach.")

    def __getattr__(self, item):
        if item in self.AGGREGATE_FIELDS:
            # Aggregate fields from all requirements
            ret = getattr(self._cpp_info_view, item)
            for it in self._requirements:
                ret += getattr(it, item)
            return ret
        else:
            return getattr(self._cpp_info_view, item)


class CppInfoViewAggregated(BaseCppInfoViewAggregated):
    _expected_class = CppInfoView

    def __init__(self, cpp_info_view):
        super(CppInfoViewAggregated, self).__init__(cpp_info_view)
        self._configs = {k: CppInfoViewConfigAggregated(v) for k, v in
                         cpp_info_view.get_configs().items()}

    def add_requirement(self, require_cpp_info_view):
        super(CppInfoViewAggregated, self).add_requirement(require_cpp_info_view)

        for k, v in require_cpp_info_view.get_configs().items():
            # Skip configs from requirements that doesn't match one here
            if k in self._configs:
                self._configs[k].add_requirement(v)

    def __getattr__(self, item):
        if item in self._configs:
            return self._configs.get(item)
        else:
            return super(CppInfoViewAggregated, self).__getattr__(item)


class CppInfoViewConfigAggregated(BaseCppInfoViewAggregated):
    _expected_class = CppInfoViewConfig
