from abc import ABCMeta, abstractproperty
from conans.model.cpp_info import CppInfoViewAggregated
import six


@six.add_metaclass(ABCMeta)
class Generator(object):

    def __init__(self, conanfile):
        self.conanfile = conanfile
        self.normalize = True
        self._deps_build_info = conanfile.deps_cpp_info
        self._deps_env_info = conanfile.deps_env_info
        self._env_info = conanfile.env_info
        self._deps_user_info = conanfile.deps_user_info

    @property
    def deps_cpp_info(self):
        """ Cpp info from all the dependencies """
        return self.conanfile.deps_cpp_info

    @property
    def root_cpp_info(self):
        """ Cpp for the conanfile itself """
        return self.conanfile.cpp_info

    @property
    def cpp_info(self):
        """ Cpp info aggregated for the conanfile itself and the dependencies """
        # TODO: Cache property
        cpp_info_agg = CppInfoViewAggregated(self.root_cpp_info)
        for key, value in self.deps_cpp_info.dependencies.items():
            cpp_info_agg.add(key, value)
        return cpp_info_agg

    @property
    def deps_build_info(self):
        # TODO: Remove, prefer 'self.deps_cpp_info'
        return self.deps_cpp_info

    @property
    def deps_env_info(self):
        return self._deps_env_info

    @property
    def deps_user_info(self):
        return self._deps_user_info

    @property
    def env_info(self):
        return self._env_info

    @property
    def settings(self):
        return self.conanfile.settings

    @abstractproperty
    def content(self):
        raise NotImplementedError()

    @abstractproperty
    def filename(self):
        raise NotImplementedError()

    def sorted_components(self, cpp_info):
        return cpp_info._get_sorted_components()
