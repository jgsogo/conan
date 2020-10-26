class OSBuildMixin(object):
    def get_template_names(self):
        # It adds an alternate name (more specific) using the build-os name
        os_build = str(self._conanfile.settings_build.os).lower()
        template_names = super(OSBuildMixin, self).get_template_names()
        build_template_names = []
        for it in template_names:
            build_template_names.append('{os}/{tpl_name}'.format(os=os_build, tpl_name=it))
        return build_template_names + template_names


def get_mixin(os_build):
    # TODO: If we really want to let the user inject behaviour into our hierarchy of classes,
    #   then we can turn this into a factory and allow registration from outside
    os_build_mixins = {}
    return os_build_mixins.get(os_build, OSBuildMixin)
