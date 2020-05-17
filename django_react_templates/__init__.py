import tempfile
import functools
import os

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.backends.django import DjangoTemplates
from django.core.exceptions import ImproperlyConfigured

from .template import ReactTemplate


class ReactBackend(DjangoTemplates):
    # Templates will be read from this subdirectory by default
    app_dirname = 'react'

    def __init__(self, params):
        params = params.copy()
        options = params.get('OPTIONS', {})
        super().__init__(params)

        self.debug = options.get('debug', settings.DEBUG)
        self.autoescape = options.get('autoescape', True)

        self.template_builtins = self.engine.template_builtins
        self.template_libraries = self.engine.template_libraries
        self.template_context_processors = self.engine.template_context_processors
        self.string_if_invalid = ''

    def get_template(self, template_name):
        tried = []
        for template_file in self.iter_template_filenames(template_name):
            origin = Origin(template_file, template_name, self)
            if not os.path.exists(template_file):
                tried.append((origin, 'Source does not exist'))
            else:
                with open(template_file, 'r') as tf:
                    return ReactTemplate(tf.read(), origin, template_name, self)
        raise TemplateDoesNotExist(template_name, tried=tried, backend=self)

    def from_string(self, template_code):
        """
        Return a compiled ReactTemplate object for the given template code.
        """
        # Make sure a temporary version of the file exists, since ReactTemplate
        # will require an existing file to compile ES code
        tmpfile = tempfile.NamedTemporaryFile(mode='w')
        tmpfile.write(str(template_code))
        tmpfile.seek(0)

        origin = Origin(tmpfile.name, tmpfile.name, self)
        return ReactTemplate(template_code, origin, tmpfile.name, self, tmpfile)

    @classmethod
    @functools.lru_cache
    def get_default(cls):
        from django.template import engines
        for engine in engines.all():
            if isinstance(engine, cls):
                return engine.engine
        raise ImproperlyConfigured('No ReactBackend is configured.')
