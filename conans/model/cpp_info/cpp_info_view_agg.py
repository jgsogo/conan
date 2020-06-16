from conans.errors import ConanException

from .cpp_info_view_dict import CppInfoViewDict


class CppInfoViewAggregated(object):
    def __init__(self, deps, **fallback):
        self._deps = deps
        self._fallback = fallback

    def __getattr__(self, item):
        try:
            return getattr(self._deps, item)
        except ConanException:
            if item in self._fallback:
                return self._fallback.get(item)
            raise ConanException("Field '{}' not available in CppInfoViewAggregated".format(item))

    def __getitem__(self, item):
        return getattr(self._deps, item)

    def get_configs(self):
        configs = {}
        for it, config in self._deps.get_configs().items():
            agg = CppInfoViewAggregated(config, **self._fallback)
            configs[it] = agg
        return configs
