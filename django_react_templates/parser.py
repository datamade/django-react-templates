import re

from django.utils.functional import SimpleLazyObject
from django.template import base


# Copy _lazy_re_compile since Django does not guarantee its API:
# https://github.com/django/django/commit/c4cba148d8356596da80c4d93a96fb335e4b0b6b
def _lazy_re_compile(regex, flags=0):
    """Lazily compile a regex with flags."""
    def _compile():
        # Compile the regex if it was not passed pre-compiled.
        if isinstance(regex, str):
            return re.compile(regex, flags)
        else:
            assert not flags, (
                'flags must be empty if regex is passed pre-compiled'
            )
            return regex
    return SimpleLazyObject(_compile)


# Override the definition of constant_string in django.template.base in order to
# allow for HTML-escaped single and double quotes in constants
constant_string = r"""
(?:%(i18n_open)s%(strdq)s%(i18n_close)s|
%(i18n_open)s%(strsq)s%(i18n_close)s|
%(strdq)s|
%(strsq)s)
""" % {
    'strdq': r'("[^"\\]*(?:\\.[^"\\]*)*"|&quot;.*&quot;|\\".*\\")',  # double-quoted string
    'strsq': r"('[^'\\]*(?:\\.[^'\\]*)*'|&\#x27;.*&\#x27;|\\'.*\\')",  # single-quoted string
    'i18n_open': re.escape("_("),
    'i18n_close': re.escape(")"),
}
constant_string = constant_string.replace("\n", "")

filter_raw_string = r"""
^(?P<constant>%(constant)s)|
^(?P<var>[%(var_chars)s]+|%(num)s)|
 (?:\s*%(filter_sep)s\s*
     (?P<filter_name>\w+)
         (?:%(arg_sep)s
             (?:
              (?P<constant_arg>%(constant)s)|
              (?P<var_arg>[%(var_chars)s]+|%(num)s)
             )
         )?
 )""" % {
    'constant': constant_string,
    'num': r'[-+\.]?\d[\d\.e]*',
    'var_chars': r'\w\.',
    'filter_sep': re.escape(base.FILTER_SEPARATOR),
    'arg_sep': re.escape(base.FILTER_ARGUMENT_SEPARATOR),
}

filter_re = _lazy_re_compile(filter_raw_string, re.VERBOSE)


class ReactFilterExpression(base.FilterExpression):
    """
    Patch the default FilterExpression to parse HTML-escaped expressions in tags.
    """
    def __init__(self, token, parser):
        self.token = token
        matches = filter_re.finditer(token)
        var_obj = None
        filters = []
        upto = 0
        for match in matches:
            start = match.start()
            if upto != start:
                raise base.TemplateSyntaxError(
                    "Could not parse some characters: "
                    "%s|%s|%s" %
                    (token[:upto], token[upto:start],
                    token[start:])
                )
            if var_obj is None:
                var, constant = match['var'], match['constant']
                if constant:
                    try:
                        var_obj = ReactVariable(constant).resolve({})
                    except base.VariableDoesNotExist:
                        var_obj = None
                elif var is None:
                    raise base.TemplateSyntaxError(
                        "Could not find variable at "
                        "start of %s." % token
                    )
                else:
                    var_obj = ReactVariable(var)
            else:
                filter_name = match['filter_name']
                args = []
                constant_arg, var_arg = match['constant_arg'], match['var_arg']
                if constant_arg:
                    args.append((False, ReactVariable(constant_arg).resolve({})))
                elif var_arg:
                    args.append((True, ReactVariable(var_arg)))
                filter_func = parser.find_filter(filter_name)
                self.args_check(filter_name, filter_func, args)
                filters.append((filter_func, args))
            upto = match.end()
        if upto != len(token):
            raise base.TemplateSyntaxError(
                "Could not parse the remainder: '%s' "
                "from '%s'" % (token[upto:], token)
            )

        self.filters = filters
        self.var = var_obj


class ReactVariable(base.Variable):
    def __init__(self, var):
        if isinstance(var, str):
            # Format HTML-escaped quotes
            var = var.replace('&quot;', '"').replace('&#x27;', "'")

            # Format escaped opening/closing quotes
            if var.startswith('\\"') and var.endswith('\\"'):
                var = '"%s"' % var[2:-2]
            elif var.startswith("\\'") and var.endswith("\\'"):
                var = "'%s'" % var[2:-2]

        super().__init__(var)


class ReactParser(base.Parser):
    def compile_filter(self, token):
        return ReactFilterExpression(token, self)


class ReactLexer(base.Lexer):
    def create_token(self, token_string, position, lineno, in_tag):
        """
        Override parent method to ignore variable blocks.
        """
        if in_tag and token_string.startswith(base.BLOCK_TAG_START):
            # The [2:-2] ranges below strip off *_TAG_START and *_TAG_END.
            # We could do len(BLOCK_TAG_START) to be more "correct", but we've
            # hard-coded the 2s here for performance. And it's not like
            # the TAG_START values are going to change anytime, anyway.
            block_content = token_string[2:-2].strip()
            if self.verbatim and block_content == self.verbatim:
                self.verbatim = False
        if in_tag and not self.verbatim:
            if token_string.startswith(base.VARIABLE_TAG_START):
                # Treat variables as text.
                return base.Token(base.TokenType.TEXT, token_string, position, lineno)
            if token_string.startswith(base.BLOCK_TAG_START):
                if block_content[:9] in ('verbatim', 'verbatim '):
                    self.verbatim = 'end%s' % block_content
                return base.Token(base.TokenType.BLOCK, block_content, position, lineno)
            elif token_string.startswith(base.COMMENT_TAG_START):
                content = ''
                if token_string.find(base.TRANSLATOR_COMMENT_MARK):
                    content = token_string[2:-2].strip()
                return base.Token(base.TokenType.COMMENT, content, position, lineno)
        else:
            return base.Token(base.TokenType.TEXT, token_string, position, lineno)


class ReactDebugLexer(ReactLexer, base.DebugLexer):
    pass
