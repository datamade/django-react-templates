import pytest

from django.urls import reverse
from django.template import TemplateSyntaxError
from django.template.defaulttags import URLNode

from django_react_templates.template import ReactTemplate


def test_template_init():
    template = ReactTemplate('foo')
    assert not hasattr(template, 'nodelist')


def test_template_compile_nodelist():
    template = ReactTemplate('{% url &quot;client&quot; %}')
    nodelist = template.compile_nodelist()
    assert len(nodelist) == 1
    assert isinstance(nodelist[0], URLNode)


def test_template_render(mock_subprocess_run, template_string):
    template = ReactTemplate(template_string)
    output = template.render()
    mock_subprocess_run.assert_called_once()
    assert output == reverse('client')


def test_template_render_closes_tmpfile(engine, mock_subprocess_run, template_string):
    template = engine.from_string(template_string)
    assert template.tmpfile.closed is False
    template.render()
    assert template.tmpfile.closed is True


def test_template_render_error_closes_tmpfile(engine, mocker, template_string):
    mocker.patch('subprocess.run', side_effect=TemplateSyntaxError('foo'), autospec=True)
    template = engine.from_string(template_string)
    assert template.tmpfile.closed is False
    with pytest.raises(TemplateSyntaxError):
        template.render()
    assert template.tmpfile.closed is True
