import re

from django.utils.functional import SimpleLazyObject
from django.template.base import (Parser, FilterExpression, Variable,
                                  VariableDoesNotExist, TemplateSyntaxError,
                                  NodeList, TextNode,
                                  FILTER_SEPARATOR, FILTER_ARGUMENT_SEPARATOR)


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
    'filter_sep': re.escape(FILTER_SEPARATOR),
    'arg_sep': re.escape(FILTER_ARGUMENT_SEPARATOR),
}

filter_re = _lazy_re_compile(filter_raw_string, re.VERBOSE)


class ReactFilterExpression(FilterExpression):
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
                raise TemplateSyntaxError("Could not parse some characters: "
                                          "%s|%s|%s" %
                                          (token[:upto], token[upto:start],
                                           token[start:]))
            if var_obj is None:
                var, constant = match['var'], match['constant']
                if constant:
                    try:
                        var_obj = ReactVariable(constant).resolve({})
                    except VariableDoesNotExist:
                        var_obj = None
                elif var is None:
                    raise TemplateSyntaxError("Could not find variable at "
                                              "start of %s." % token)
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
            raise TemplateSyntaxError("Could not parse the remainder: '%s' "
                                      "from '%s'" % (token[upto:], token))

        self.filters = filters
        self.var = var_obj


class ReactVariable(Variable):
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


class ReactParser(Parser):
    def compile_filter(self, token):
        return ReactFilterExpression(token, self)

    def parse(self, parse_until=None):
        """
        Override parent parse() method to ignore variable blocks ("{{ vjar }}")
        """
        if parse_until is None:
            parse_until = []
        nodelist = NodeList()
        while self.tokens:
            token = self.next_token()
            # Use the raw values here for TokenType.* for a tiny performance boost.
            if token.token_type.value in [0, 1]:  # TokenType.TEXT or TokenType.VAR
                self.extend_nodelist(nodelist, TextNode(token.contents), token)
            elif token.token_type.value == 2:  # TokenType.BLOCK
                try:
                    command = token.contents.split()[0]
                except IndexError:
                    raise self.error(token, 'Empty block tag on line %d' % token.lineno)
                if command in parse_until:
                    # A matching token has been reached. Return control to
                    # the caller. Put the token back on the token list so the
                    # caller knows where it terminated.
                    self.prepend_token(token)
                    return nodelist
                # Add the token to the command stack. This is used for error
                # messages if further parsing fails due to an unclosed block
                # tag.
                self.command_stack.append((command, token))
                # Get the tag callback function from the ones registered with
                # the parser.
                try:
                    compile_func = self.tags[command]
                except KeyError:
                    self.invalid_block_tag(token, command, parse_until)
                # Compile the callback into a node object and add it to
                # the node list.
                try:
                    compiled_result = compile_func(self, token)
                except Exception as e:
                    raise self.error(token, e)
                self.extend_nodelist(nodelist, compiled_result, token)
                # Compile success. Remove the token from the command stack.
                self.command_stack.pop()
        if parse_until:
            self.unclosed_block_tag(parse_until)
        return nodelist
