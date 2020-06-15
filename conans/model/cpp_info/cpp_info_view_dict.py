from collections import OrderedDict, defaultdict

from conans.errors import ConanException
from .cpp_info import BaseCppInfo, CppInfoConfig
from .cpp_info_view import CppInfoView, CppInfoViewConfig


class _CppInfoViewConfigPlaceholder(CppInfoViewConfig):
    """ This class creates an empty 'config' """

    def __init__(self, pkg_cpp_info_view):
        cpp_info_view = CppInfoConfig(pkg_cpp_info_view._cpp_info)
        super(_CppInfoViewConfigPlaceholder, self).__init__(pkg_cpp_info_view, cpp_info_view)


class BaseCppInfoViewDict(object):
    _expected_class = None
    AGGREGATE_FIELDS = BaseCppInfo.FIELDS + list(CppInfoView.FIELDS_PATH_MAPPING.keys())

    def __init__(self):
        self._dependencies = OrderedDict()

    def add(self, ref_name, cpp_info_view):
        assert isinstance(cpp_info_view, self._expected_class), "Got type '{}'".format(
            type(cpp_info_view))
        assert ref_name not in self._dependencies, "'{}' already added".format(ref_name)
        assert ref_name == str(cpp_info_view), "'{}' != '{}'".format(ref_name, str(cpp_info_view))
        self._dependencies[ref_name] = cpp_info_view

    @property
    def components(self):
        raise ConanException("Do not requests 'components' for an aggregated view, they should"
                             " be used only with a targets approach.")

    def __getitem__(self, item):
        return self._dependencies.get(item)

    def __getattr__(self, item):
        if item in self.AGGREGATE_FIELDS:
            # Aggregate fields from all dependencies
            ret = []
            for _, dep in self._dependencies.items():
                ret += getattr(dep, item)
            return ret
        else:
            raise ConanException("Cannot retrieve '{}' from a list of cpp_info".format(item))


class CppInfoViewDict(BaseCppInfoViewDict):
    """ Stores an ordered dict of CppInfoView objects and offers some convenient methods """
    _expected_class = CppInfoView

    def __init__(self):
        super(CppInfoViewDict, self).__init__()
        self._configs = defaultdict(CppInfoViewConfigDict)

    def add(self, ref_name, cpp_info_view):
        for k, v in cpp_info_view.get_configs().items():
            if k not in self._configs:
                # All dependencies up to this one need to mock this new config.
                for dep_name, dep in self._dependencies.items():
                    fake_config = _CppInfoViewConfigPlaceholder(dep)
                    self._configs[k].add(dep_name, fake_config)
            self._configs[k].add(ref_name, v)

        super(CppInfoViewDict, self).add(ref_name, cpp_info_view)

        configs_for_added = list(cpp_info_view.get_configs().keys())
        for k in self._configs.keys():
            if k not in configs_for_added:
                # Need to mock this config for the added requirement
                fake_config = _CppInfoViewConfigPlaceholder(cpp_info_view)
                self._configs[k].add(ref_name, fake_config)

    def get_configs(self):
        return self._configs

    def __getattr__(self, item):
        if item in self._configs:
            return self._configs.get(item)
        else:
            return super(CppInfoViewDict, self).__getattr__(item)


class CppInfoViewConfigDict(BaseCppInfoViewDict):
    _expected_class = CppInfoViewConfig

    def __getitem__(self, item):
        raise ConanException("Do not try to return individual dependencies from configs")
