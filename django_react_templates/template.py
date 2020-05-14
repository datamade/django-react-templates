import os
import json
import subprocess

from django.template import TemplateSyntaxError
from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy
from django.utils.html import conditional_escape


class ReactTemplate:
    def __init__(self, template_path, tmpfile=None):
        self.template_path = template_path
        self.tmpfile = tmpfile

    def render(self, context=None, request=None):
        if context is None:
            context = {}
        else:
            context = {k: conditional_escape(v) for k, v in context.items()}
        if request is not None:
            context['request'] = 'TODO: Pass in Request object'
            if context.get('view'):
                context['view'] = 'TODO: Serialize view attributes'
            context['csrf_input'] = str(csrf_input_lazy(request))
            context['csrf_token'] = str(csrf_token_lazy(request))

        current_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_path)

        try:
            completed_process = subprocess.run(
                ['node', os.path.join(current_dir, 'scripts', 'index.js'), self.template_path],
                input=json.dumps(context),
                capture_output=True,
                check=True,
                universal_newlines=True
            )
        except subprocess.CalledProcessError as exc:
            raise TemplateSyntaxError(exc.stderr)
        finally:
            if self.tmpfile is not None:
                self.tmpfile.close()

        return completed_process.stdout
