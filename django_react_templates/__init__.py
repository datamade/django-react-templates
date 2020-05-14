import tempfile
import os

from django.template.backends.base import BaseEngine
from django.template import Origin, TemplateDoesNotExist

from .template import ReactTemplate


class ReactBackend(BaseEngine):
    # Templates will be read from this subdirectory by default
    app_dirname = 'react'

    def __init__(self, params):
        params = params.copy()
        # TODO: Read or remove options
        options = params.pop('OPTIONS').copy()
        super().__init__(params)

    def get_template(self, template_name):
        # TODO: Implement template caching
        tried = []
        for template_file in self.iter_template_filenames(template_name):
            if not os.path.exists(template_file):
                tried.append((
                    Origin(template_file, template_name, self),
                    'Source does not exist',
                ))
            else:
                return ReactTemplate(template_file)
        raise TemplateDoesNotExist(template_name, tried=tried, backend=self)

    def from_string(self, template_code):
        """
        Return a compiled ReactTemplate object for the given template code.
        """
        tmpfile = tempfile.NamedTemporaryFile(mode='w')
        tmpfile.write(str(template_code))
        tmpfile.seek(0)
        return ReactTemplate(tmpfile.name, tmpfile=tmpfile)
