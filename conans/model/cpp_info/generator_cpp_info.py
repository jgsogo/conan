from .cpp_info import BaseCppInfo
from .dep_cpp_info import DepCppInfo


class GeneratorCppInfo(object):
    """ A wrapper to access cppinfo data from generators, main difference is that this one
        aggregates the data from components
    """
    _AGGREGATE_FIELDS = BaseCppInfo.FIELDS + list(DepCppInfo.FIELDS_PATH_MAPPING.keys())

    def __init__(self, deps_cpp_info):
        assert isinstance(deps_cpp_info, DepCppInfo), \
            "DepsCppInfo expected, got {}".format(type(deps_cpp_info))
        self._deps_cpp_info = deps_cpp_info

    def __str__(self):
        return str(self._deps_cpp_info)

    def __getattr__(self, item):
        if item in GeneratorCppInfo._AGGREGATE_FIELDS:
            if self._deps_cpp_info.components:
                # Aggregate information from all the components (in order)
                ret = []
                for _, cmp in self._deps_cpp_info.components.items():
                    ret += getattr(cmp, item)
                return ret
        return getattr(self._deps_cpp_info, item)
