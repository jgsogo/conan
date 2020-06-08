from collections import OrderedDict, defaultdict


class BaseDepsCppInfo(object):

    def __init__(self):
        self._dependencies = OrderedDict()

    def add(self, dep_cpp_info):
        self._dependencies[str(dep_cpp_info)] = dep_cpp_info

    @property
    def dependencies(self):
        return self._dependencies.items()

    @property
    def deps(self):
        return self._dependencies.keys()

    @property
    def rootpath(self):
        # TODO: This makes no sense, which is the rootpath of several deps?
        # raise RuntimeError("Maybe we are here because we are 'aggregating' configs? For configs it makes sense, all of them has the same rootpath")
        return ""

    @property
    def filter_empty(self):
        # TODO: Work on this
        return all(it._remove_missing_paths for it in self._dependencies.values())

    def __getitem__(self, item):
        return self._dependencies[item]

    def __getattr__(self, item):
        ret = []
        for _, dep in self._dependencies.items():
            ret += getattr(dep, item)
        return ret


class DepsCppInfo(BaseDepsCppInfo):
    def __init__(self):
        super(DepsCppInfo, self).__init__()
        self._configs = defaultdict(DepsCppInfoConfigs)

    def add(self, dep_cpp_info):
        super(DepsCppInfo, self).add(dep_cpp_info)
        for config, dep_cpp_info_config in dep_cpp_info.get_configs().items():
            self._configs[config].add(dep_cpp_info_config)

    @property
    def configs(self):
        return self._configs

    def get_configs(self):
        # TODO: Avoid this duplicity: get_configs and configs
        return self._configs


class DepsCppInfoConfigs(BaseDepsCppInfo):
    pass
