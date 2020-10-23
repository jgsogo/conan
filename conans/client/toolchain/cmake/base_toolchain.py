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
        conanfile = self._conanfile
        return [
            '{}/toolchain_{}.cmake'.format(conanfile.settings_build.os, conanfile.settings.os),
            'toolchain_{}.cmake'.format(conanfile.settings.os),
            'toolchain.cmake',
        ]
