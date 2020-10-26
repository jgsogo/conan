class GeneratorMixin(object):
    generator_name = None

    def get_template_names(self):
        tpl_names = super(GeneratorMixin, self).get_template_names()
        if self.generator_name:
            return ['{{prefix}}_{}{{extension}}'.format(self.generator_name), ] + tpl_names
        return tpl_names


class NinjaMixin(GeneratorMixin):
    generator_name = 'ninja'

    def get_filename(self):
        filename = super(NinjaMixin, self).get_filename()
        filename = filename.replace('{prefix}', '{{prefix}}_{}'.format(self.generator_name))
        return filename


def get_mixin(generator):
    # TODO: If we really want to let the user inject behaviour into our hierarchy of classes,
    #   then we can turn this into a factory and allow registration from outside
    generator_name = generator.replace(' ', '').lower()
    if generator_name == NinjaMixin.generator_name:
        return NinjaMixin
    else:
        mixin_class = type('MixinClass', (GeneratorMixin,), {'generator_name': generator_name})
        return mixin_class
