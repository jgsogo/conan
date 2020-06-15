from conans.errors import ConanException

from .cpp_info_view_dict import CppInfoViewDict


class CppInfoViewAggregated(CppInfoViewDict):

    def __init__(self, cpp_info_view):
        super(CppInfoViewAggregated, self).__init__()
        self._cpp_info_view = cpp_info_view
        super(CppInfoViewAggregated, self).add(str(cpp_info_view), cpp_info_view)

    def __getattr__(self, item):
        try:
            return super(CppInfoViewAggregated, self).__getattr__(item)
        except ConanException:
            return getattr(self._cpp_info_view, item)
