from django_react_templates.parser import ReactFilterExpression


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
    assert nodelist[0].render({}) == template_string
