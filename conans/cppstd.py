from conans.client.build.cppstd_flags import cppstd_default
from conans.client.build.cppstd_flags import cppstd_flag, cppstd_from_settings
from conans.errors import ConanInvalidConfiguration

CPPSTD_98 = "98"
CPPSTD_11 = "11"
CPPSTD_14 = "14"
CPPSTD_17 = "17"
CPPSTD_20 = "20"
_CPPSTD_ALL = [(CPPSTD_98, CPPSTD_11, CPPSTD_14, CPPSTD_17, CPPSTD_20),]


def _as_list(sublist):
    if isinstance(sublist, (tuple, list)):
        return sublist
    else:
        return [sublist, ]


def get_cppstd(conanfile):
    """ Returns the value of the 'cppstd' for the given settings and also if it is a
        stable/unstable implementation according to the compiler
    """
    value = cppstd_from_settings(conanfile.settings) or \
            cppstd_default(str(conanfile.settings.compiler),
                           str(conanfile.settings.compiler.version))
    value = value.replace('gnu', '')
    flag = cppstd_flag(conanfile.settings.compiler, conanfile.settings.compiler.version, value)
    stable = bool(True)
    return value, stable


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
    # Get the list of 'cppstd' values to iterate
    cppstd_compatibility = getattr(conanfile, 'cppstd_compatibility', None)
    if not cppstd_compatibility:
        cppstd_compatibility = _CPPSTD_ALL

    def _cppstd_to_iterate():
        value, stable = get_cppstd(conanfile)
        if not stable:
            return []

        for sublist in cppstd_compatibility:
            sublist = _as_list(sublist)
            if value in sublist:
                return sublist  # TODO: Filter unstable/not-supported for the given compiler

    cppstd_to_iterate = _cppstd_to_iterate()
    # TODO: Is there an order? First the default, then the rest (later to newer)
    # TODO: Apply opt-out ==> empty list

    # Get the default, its value will be 'None' in the info object
    default = cppstd_default(str(conanfile.settings.compiler),
                             str(conanfile.settings.compiler.version))
    default = default.replace('gnu', '')

    # Iterate current 'conanfile.info'
    for it in cppstd_to_iterate:
        p = conanfile.info.clone()
        if it == default:
            p.settings.compiler.cppstd = None
        else:
            p.settings.compiler.cppstd = it
        yield p

    # Iterate all the compatible_packages
    for compatible_package in conanfile.compatible_packages:
        yield compatible_package
        for it in cppstd_to_iterate:
            p = compatible_package.clone()
            if it == default:
                p.settings.compiler.cppstd = None
            else:
                p.settings.compiler.cppstd = it
            yield p

    # TODO: Avoid duplicates
