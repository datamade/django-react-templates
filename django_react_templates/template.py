import os
import json
import subprocess

from django.template import TemplateSyntaxError, Template
from django.template.base import UNKNOWN_SOURCE, Origin
from django.template.context import make_context
from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy
from django.utils.html import conditional_escape

from django_react_templates.parser import ReactParser, ReactLexer, ReactDebugLexer


class ReactTemplate(Template):
    def __init__(self, template_string, origin=None, name=None, engine=None, tmpfile=None):
        # Copy the initialization routine of the parent Template to avoid
        # compiling the nodelist up front (we want to wait until render())
        if engine is None:
            from django_react_templates import ReactBackend
            engine = ReactBackend.get_default()
        if origin is None:
            origin = Origin(UNKNOWN_SOURCE)
        self.name = name
        self.origin = origin
        self.engine = engine
        self.source = str(template_string)

        self.tmpfile = tmpfile

    def render(self, context=None, request=None):
        django_context = make_context(
            context,
            request,
            autoescape=self.engine.autoescape
        )
        react_context = {k: conditional_escape(v) for k, v in django_context.flatten().items()}
        if request is not None:
            react_context['request'] = 'TODO: Pass in Request object'
            if react_context.get('view'):
                react_context['view'] = 'TODO: Serialize view attributes'
            react_context['csrf_token'] = str(csrf_token_lazy(request))

        current_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_path)

        try:
            completed_process = subprocess.run(
                [
                    'node',
                    os.path.join(current_dir, 'scripts', 'render.js'),
                    self.origin.name,
                    json.dumps(react_context)
                ],
                capture_output=True,
                check=True,
                encoding='utf-8'
            )
        except subprocess.CalledProcessError as exc:
            raise TemplateSyntaxError(exc.stderr)
        finally:
            if self.tmpfile is not None:
                self.tmpfile.close()

        # Set source code and parsed nodelist for Django render
        self.source = completed_process.stdout
        self.nodelist = self.compile_nodelist()
        return super().render(django_context)

    def compile_nodelist(self):
        """
        Override the parent compile_nodelist function to use a custom parser
        and custom lexers.
        """
        if self.engine.debug:
            lexer = ReactDebugLexer(self.source)
        else:
            lexer = ReactLexer(self.source)

        tokens = lexer.tokenize()
        parser = ReactParser(
            tokens, self.engine.template_libraries, self.engine.template_builtins,
            self.origin,
        )

        try:
            return parser.parse()
        except Exception as e:
            if self.engine.debug:
                e.template_debug = self.get_exception_info(e, e.token)
            raise
