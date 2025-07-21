from __future__ import annotations

from typing import TYPE_CHECKING

import re

import pytest
import sly

import mckit.parser.common as cmn

from mckit.parser.common.lexer import LexError
from mckit.parser.common.lexer import Lexer as LexerBase

if TYPE_CHECKING:
    from typing import ClassVar


# noinspection PyUnboundLocalVariable,PyPep8Naming,PyUnresolvedReferences
class DerivedLexer(LexerBase):
    tokens: ClassVar = {FRACTION, FLOAT, INTEGER, ZERO}

    FRACTION = r"\d+(?:\.\d+[a-z])"

    @_(cmn.FLOAT)
    def FLOAT(self, token):
        return self.on_float(token)

    @_(cmn.INTEGER)
    def INTEGER(self, token):
        return self.on_float(token)

    ZERO = r"0"


@pytest.mark.parametrize(
    "text, expected_types, expected_values",
    [
        ("1 0 3.14", ["INTEGER", "ZERO", "FLOAT"], [1, 0, 3.14]),
        ("3.14 3.14c", ["FLOAT", "FRACTION"], [3.14, "3.14c"]),
        ("1 0 1e-4", ["INTEGER", "ZERO", "FLOAT"], [1, 0, 1e-4]),
    ],
)
def test_derived_lexer(text, expected_types, expected_values):
    lexer = DerivedLexer()
    tokens = list(lexer.tokenize(text))
    result = [t.type for t in tokens]
    assert result == expected_types
    result = [t.value for t in tokens]
    assert result == expected_values


@pytest.mark.parametrize(
    "text, msg_contains",
    [
        ("1~ 0 3.14", "column 2"),
        ("\n1 0 3.14 ~", "at line 2, column 10"),
        ("\n1 0 3.14 ~", r"\s{9}\^"),
        ("\n1 0 3.14 0~", r"\s{10}\^"),
        ("~", "column 1\n~\n\\^"),
    ],
)
def test_bad_path(text, msg_contains):
    lexer = DerivedLexer()
    with pytest.raises(LexError, match=msg_contains):
        _ = list(lexer.tokenize(text))


# noinspection PyUnboundLocalVariable,PyPep8Naming,PyUnresolvedReferences
class MyLexer(LexerBase):
    literals: ClassVar = {":", "(", ")"}
    ignore = " \t"
    reflags = re.IGNORECASE | re.MULTILINE

    tokens: ClassVar = {NAME, FLOAT, INTEGER, ZERO}

    NAME = r"\d?[A-Za-z-]+"

    @_(cmn.FLOAT)
    def FLOAT(self, token):
        return self.on_float(token)

    @_(cmn.INTEGER)
    def INTEGER(self, token):
        return self.on_integer(token)

    ZERO = r"0"


@pytest.mark.parametrize(
    "text, expected_types, expected_values",
    [
        ("AAA 1 0 3.14", ["NAME", "INTEGER", "ZERO", "FLOAT"], ["AAA", 1, 0, 3.14]),
        ("1B 1 0 3.14", ["NAME", "INTEGER", "ZERO", "FLOAT"], ["1B", 1, 0, 3.14]),
    ],
)
def test_good_path(text, expected_types, expected_values):
    lexer = MyLexer()
    tokens = list(lexer.tokenize(text))
    result = [t.type for t in tokens]
    assert result == expected_types
    result = [t.value for t in tokens]
    assert result == expected_values


# noinspection PyUnresolvedReferences
class MyParser(sly.Parser):
    tokens = MyLexer.tokens

    @_("NAME number parameters")
    def expression(self, p):
        return p.NAME, p.number, p.parameters

    @_("NAME ZERO")
    def expression(self, p):
        return p.NAME, 0, None

    @_("INTEGER")
    def number(self, p):
        return p.INTEGER

    @_("parameters FLOAT")
    def parameters(self, p):
        res = p.parameters
        res.append(p.FLOAT)
        return res

    @_("FLOAT")
    def parameters(self, p):
        return [p.FLOAT]


@pytest.mark.parametrize(
    "text, expected",
    [("AAA 1 1.2 3.4", ("AAA", 1, [1.2, 3.4])), ("A-Z 0", ("A-Z", 0, None))],
)
def test_parser_with_derived_lexer(text, expected):
    lexer = MyLexer()
    parser = MyParser()
    actual = parser.parse(lexer.tokenize(text))
    assert actual == expected


if __name__ == "__main__":
    pytest.main()
