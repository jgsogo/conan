from conans.client.build.cppstd_flags import cppstd_default
from conans.client.build.cppstd_flags import cppstd_flag, cppstd_from_settings
from conans.errors import ConanInvalidConfiguration, ConanInvalidCppstd

CPPSTD_98 = "98"
CPPSTD_11 = "11"
CPPSTD_14 = "14"
CPPSTD_17 = "17"
#CPPSTD_20 = "20"
#ALL_CPPSTD = (CPPSTD_98, CPPSTD_11, CPPSTD_14, CPPSTD_17, CPPSTD_20)
ALL_CPPSTD = (CPPSTD_98, CPPSTD_11, CPPSTD_14, CPPSTD_17)


def _as_list(sublist):
    if isinstance(sublist, (tuple, list)):
        return sublist
    else:
        return [sublist, ]


def _is_gcc_stable(flag):
    return not any([it in flag for it in ['x', 'y', 'z', 'a']])


def get_cppstd(conanfile):
    """ Returns the value of the 'cppstd' for the given settings and also if it is a
        stable/unstable implementation according to the compiler
    """
    value = cppstd_from_settings(conanfile.settings) or \
            cppstd_default(conanfile.settings)
    assert not 'gnu' in value, value  # TODO: No more complexity right now
    flag = cppstd_flag(conanfile.settings.compiler, conanfile.settings.compiler.version, value)
    stable = _is_gcc_stable(flag)
    return value, stable


def conanfile_configure(conanfile):
    try:
        conanfile.configure()
        conan_invalid_config(conanfile)
    except ConanInvalidCppstd as e:
        # If it is a _compile invalid configuration_ due to C++ standard, delay failure to build
        conanfile._conan_fail_build = e


def conanfile_build(conanfile):
    e = getattr(conanfile, '_conan_fail_build', None)
    if e:
        raise e
    conanfile.build()


def conan_invalid_config(conanfile):
    """ According to the information declared in the conanfile, this function raises if
        the 'cppstd' from the settings is not valid
    """
    cppstd_compatibility = getattr(conanfile, 'cppstd_compatibility', None)
    if cppstd_compatibility:
        cppstd_compatibility = [item for sublist in cppstd_compatibility for item in _as_list(sublist)]
        cppstd_value, _ = get_cppstd(conanfile)
        if cppstd_value not in cppstd_compatibility:
            raise ConanInvalidConfiguration("cppstd '{}' not valid".format(cppstd_value))


def iter_compatible_packages(conanfile):
    """ Given a conanfile, this function returns the list of 'infos' that are compatible:
        * iterate all the 'cppstd' for the current conanfile.info
        * for each compatible_package, iterate all the 'cppstd' available
    """
    # Only if settings has compiler
    if not conanfile.settings.get_safe('compiler'):
        return

    # Get the list of 'cppstd' values to iterate
    cppstd_compatibility = getattr(conanfile, 'cppstd_compatibility', None)
    if not cppstd_compatibility:
        cppstd_compatibility = [ALL_CPPSTD, ]  # All are one single group (compatible between them)

    def _cppstd_to_iterate():
        value, stable = get_cppstd(conanfile)
        if not stable:
            return []

        for sublist in cppstd_compatibility:
            sublist = _as_list(sublist)
            if value in sublist:
                stable_ones = []
                for item in sublist:
                    # Filter unstable/not-supported for the given compiler
                    flag = cppstd_flag(conanfile.settings.compiler,
                                       conanfile.settings.compiler.version, item)
                    stable = flag and _is_gcc_stable(flag)
                    if stable:
                        stable_ones.append(item)
                return stable_ones

    cppstd_to_iterate = _cppstd_to_iterate()
    # TODO: Is there an order? First the default, then the rest (later to newer)
    # TODO: Apply opt-out ==> empty list
    # TODO: Some of these can be marked as a failure in `configure()` by the user, we cannot get
    #   that information here, but it shouldn't be a big deal as those computed package-id won't
    #   ever be available.

    # Iterate current 'conanfile.info'
    for it in cppstd_to_iterate:
        p = conanfile.info.clone()
        p.settings.compiler.cppstd = it
        # Default 'cppstd' will always we assigned (it is also changed in the 'info' object)
        yield p

    # Iterate all the compatible_packages
    for compatible_package in conanfile.compatible_packages:
        yield compatible_package
        for it in cppstd_to_iterate:
            p = compatible_package.clone()
            p.settings.compiler.cppstd = it
            # Default 'cppstd' will always we assigned (it is also changed in the 'info' object)
            yield p

    # TODO: Avoid duplicates
