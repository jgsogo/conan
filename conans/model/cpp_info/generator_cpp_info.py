from .cpp_info import BaseCppInfo
from .deps_cpp_info import DepsCppInfo


class BaseGeneratorCppInfo(object):
    """ A wrapper to access cppinfo data from generators, main difference is that this one
        aggregates the data from components, configs,... according to docs
    """

    def __init__(self, deps_cpp_info):
        self._deps_cpp_info = deps_cpp_info

    def __str__(self):
        return str(self._deps_cpp_info)

    def __getattr__(self, item):
        return getattr(self._deps_cpp_info, item)


class GeneratorCppInfo(BaseGeneratorCppInfo):
    def __init__(self, deps_cpp_info):
        assert isinstance(deps_cpp_info, DepsCppInfo), \
            "DepsCppInfo expected, got {}".format(type(deps_cpp_info))
        super(GeneratorCppInfo, self).__init__(deps_cpp_info)

    def __getattr__(self, item):
        if item in BaseCppInfo._path_fields + BaseCppInfo._non_path_fields:
            if self._deps_cpp_info.components:
                # Aggregate information from all the components (in order)
                ret = []
                for _, cmp in self._deps_cpp_info.components.items():
                    ret += getattr(cmp, item)
                return ret
        return super(GeneratorCppInfo, self).__getattr__(item)


"""
class GeneratorCppInfoConfig(BaseGeneratorCppInfo):
    def __init__(self, pkg_deps_cpp_info, deps_cpp_info):
        assert isinstance(deps_cpp_info, DepsCppInfoConfig), \
            "DepsCppInfoConfig expected, got {}".format(type(deps_cpp_info))
        super(GeneratorCppInfoConfig, self).__init__(deps_cpp_info)
        self._pkg_deps_cpp_info = pkg_deps_cpp_info

    # TODO: Use fields assigned in the 'config' cpp_info, fallback to main ones if not explicit


class GeneratorCppInfoComponent(BaseGeneratorCppInfo):

    def __init__(self, deps_cpp_info):
        assert isinstance(deps_cpp_info, DepsCppInfoComponent), \
            "DepsCppInfoComponent expected, got {}".format(type(deps_cpp_info))
        super(GeneratorCppInfoComponent, self).__init__(deps_cpp_info)

    # Retrieves only 'my' fields
"""
