import os
#from .cpp_info import CppInfo, CppInfoComponent, CppInfoConfig
from .deps_cpp_info import DepsCppInfo, DepsCppInfoComponent, DepsCppInfoConfig


class BaseGeneratorCppInfo(object):
    """ A wrapper to access cppinfo data from generators, main difference is that this one
        aggregates the data from components, configs,... according to docs
    """

    def __init__(self, deps_cpp_info):
        self._deps_cpp_info = deps_cpp_info

    def __getattr__(self, item):
        return getattr(self._deps_cpp_info, item)


class GeneratorCppInfo(BaseGeneratorCppInfo):
    def __init__(self, deps_cpp_info):
        assert isinstance(deps_cpp_info, DepsCppInfo), \
            "DepsCppInfo expected, got {}".format(type(deps_cpp_info))
        super(GeneratorCppInfo, self).__init__(deps_cpp_info)

    # Aggregate information from all the components (in order)


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
