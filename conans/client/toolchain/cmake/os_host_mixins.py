class OSHostMixin(object):
    host_name = None

    def get_template_names(self):
        # It adds an alternative (more specific) using the host name
        parent_template_names = super(OSHostMixin, self).get_template_names()
        if self.host_name:
            template_names = []
            for it in parent_template_names:
                tpl_name = it.replace('{prefix}',
                                      '{{prefix}}_{os_host}'.format(os_host=self.host_name))
                template_names.append(tpl_name)
                template_names.append(it)
            return template_names
        return parent_template_names


class AndroidHostMixin(OSHostMixin):
    host_name = 'android'

    def get_filename(self):
        filename = super(AndroidHostMixin, self).get_filename()
        filename = filename.replace('{prefix}', '{{prefix}}_{}'.format(self.host_name))
        return filename


def get_mixin(os_host):
    # TODO: If we really want to let the user inject behaviour into our hierarchy of classes,
    #   then we can turn this into a factory and allow registration from outside
    host_name = os_host.replace(' ', '').lower()
    if host_name == AndroidHostMixin.host_name:
        return AndroidHostMixin
    else:
        mixin_class = type('MixinClass', (OSHostMixin,), {'host_name': host_name})
        return mixin_class
