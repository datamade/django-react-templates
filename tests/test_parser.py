from django.template import base
from django.template.context import make_context

from django_react_templates.parser import ReactFilterExpression, ReactToken


def test_single_quote_filterexpression():
    token = "&#x27;home&#x27;"
    filter_ex = ReactFilterExpression(token, None)
    assert filter_ex.var == 'home'


def test_escaped_single_quote_filterexpression():
    token = "\\'home\\'"
    filter_ex = ReactFilterExpression(token, None)
    assert filter_ex.var == 'home'


def test_double_quote_filterexpression():
    token = "&quot;home&quot;"
    filter_ex = ReactFilterExpression(token, None)
    assert filter_ex.var == 'home'


def test_escaped_double_quote_filterexpression():
    token = '\\"home\\"'
    filter_ex = ReactFilterExpression(token, None)
    assert filter_ex.var == 'home'


def test_parser_ignores_django_variable_tags(parse):
    template_string = "{{ variable }}"
    nodelist = parse(template_string)
    assert len(nodelist) == 1
    assert nodelist[0].render(make_context({})) == template_string


def test_templatetag_trans(parse):
    template_string = "{% load i18n %}{% trans &#x27;This text should be translated.&#x27; %}"
    nodelist = parse(template_string)
    assert len(nodelist) == 2
    assert nodelist[1].render(make_context({})) == 'This text should be translated.'


def test_reacttoken_split_contents_single_quote():
    token = ReactToken(
        base.TokenType.BLOCK,
        '{% trans &#x27;This text should be translated.&#x27; %}'
    )
    assert token.split_contents() == [
        '{%', 'trans', "&#x27;This text should be translated.&#x27;", '%}'
    ]


def test_reacttoken_split_contents_double_quote():
    token = ReactToken(
        base.TokenType.BLOCK,
        '{% trans &quot;This text should be translated.&quot; %}'
    )
    assert token.split_contents() == [
        '{%', 'trans', "&quot;This text should be translated.&quot;", '%}'
    ]
