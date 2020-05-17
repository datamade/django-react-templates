from subprocess import CompletedProcess

import pytest

from django_react_templates import ReactBackend
from django_react_templates.parser import ReactParser, ReactLexer


@pytest.fixture
def engine():
    return ReactBackend({
        'NAME': 'react',
        'DIRS': ['react/'],
        'APP_DIRS': True,
        'OPTIONS': {}
    })


@pytest.fixture
def parse(engine):
    def parse_template_string(template_string):
        lexer = ReactLexer(template_string)
        tokens = lexer.tokenize()
        parser = ReactParser(tokens, engine.template_libraries, engine.template_builtins)
        return parser.parse()
    return parse_template_string


@pytest.fixture
def template_string():
    return '{% url &quot;client&quot; %}'


@pytest.fixture
def mock_subprocess_run(mocker, template_string):
    completed_process = CompletedProcess('foo', 0, template_string)
    return mocker.patch('subprocess.run', return_value=completed_process, autospec=True)
