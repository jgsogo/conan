from collections import OrderedDict


class DepsCppInfo(object):
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

    def __getitem__(self, item):
        return self._dependencies[item]
