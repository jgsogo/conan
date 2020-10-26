from conans.client.build.compiler_flags import architecture_flag
from conans.client.tools import cpu_count
from conans.errors import ConanException


class BaseToolchain(object):

    def __init__(self, conanfile, **kwargs):
        self._conanfile = conanfile

        # To find the generated cmake_find_package finders
        self.cmake_prefix_path = "${CMAKE_BINARY_DIR}"
        self.cmake_module_path = "${CMAKE_BINARY_DIR}"

        try:
            # This is only defined in the cache, not in the local flow
            # TODO: Maybe this is something for the build-helper then
            self.install_prefix = self._conanfile.package_folder.replace("\\", "/")
        except AttributeError:
            # FIXME: In the local flow, we don't know the package_folder
            self.install_prefix = None

    def get_template_names(self):
        compiler = str(self._conanfile.settings.compiler).lower().replace(' ', '')

        return [
            '{}/toolchain_{}.cmake'.format(self._conanfile.settings_build.os, compiler),
            'toolchain_{}.cmake'.format(compiler),
        ]

    @property
    def shared_libs(self):
        try:
            return "ON" if self._conanfile.options.shared else "OFF"
        except ConanException:
            return None

    @property
    def fpic(self):
        fpic = self._conanfile.options.get_safe("fPIC")
        if fpic is None:
            return None
        os_ = self._conanfile.settings.get_safe("os")
        if os_ and "Windows" in os_:
            self._conanfile.output.warn("Toolchain: Ignoring fPIC option defined for Windows")
            return None
        shared = self._conanfile.options.get_safe("shared")
        if shared:
            self._conanfile.output.warn("Toolchain: Ignoring fPIC option defined "
                                        "for a shared library")
            return None
        return fpic


