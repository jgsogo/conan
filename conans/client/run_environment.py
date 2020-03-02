

class BaseRunEnvironment(object):
    def __init__(self, conanfile):
        self.conanfile = conanfile


class RunEnvironment(BaseRunEnvironment):
    """
    - PATH: pointing to the bin/ directories of the requires
    - LD_LIBRARY_PATH: requires lib_paths for Linux
    - DYLD_LIBRARY_PATH: requires lib_paths for OSx
    - DYLD_FRAMEWORK_PATH: requires framework_paths for OSX
    """
    @property
    def vars(self):
        lib_paths = bin_paths = framework_paths = []

        for dep in self.conanfile.deps_cpp_info.deps:
            lib_paths.extend(self.conanfile.deps_cpp_info[dep].lib_paths)
            bin_paths.extend(self.conanfile.deps_cpp_info[dep].bin_paths)
            framework_paths.extend(self.conanfile.deps_cpp_info[dep].framework_paths)

        ret = {"DYLD_LIBRARY_PATH": lib_paths,
               "LD_LIBRARY_PATH": lib_paths,
               "PATH": bin_paths}
        if framework_paths:
            ret["DYLD_FRAMEWORK_PATH"] = framework_paths
        return ret


class RunBuildEnvironment(BaseRunEnvironment):
    @property
    def vars(self):
        return self.conanfile.deps_env_info.vars
