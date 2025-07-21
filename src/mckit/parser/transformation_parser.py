from __future__ import annotations

from typing import TYPE_CHECKING

import sly

import mckit.parser.common.utils as cmn

from mckit.parser.common import Lexer as LexerBase
from mckit.parser.common.utils import drop_c_comments, extract_comments
from mckit.transformation import Transformation

if TYPE_CHECKING:
    from typing import ClassVar


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyUnresolvedReferences,SpellCheckingInspection
class Lexer(LexerBase):
    tokens: ClassVar = {NAME, FLOAT, INTEGER}

    NAME = r"\s{0,5}\*?tr\d+"

    @_(r"\s{0,5}\*?tr\d+")
    def NAME(self, t):
        if t.value[0].isspace():
            t.value = t.value.lstrip()
        if t.value[0] == "*":
            in_degrees = True
            name = int(t.value[3:])
        else:
            in_degrees = False
            name = int(t.value[2:])
        t.value = name, in_degrees
        return t

    @_(cmn.FLOAT)
    def FLOAT(self, t):
        return LexerBase.on_float(t, use_zero=False)

    @_(cmn.INTEGER)
    def INTEGER(self, t):
        return LexerBase.on_integer(t, use_zero=False)


# noinspection PyUnresolvedReferences
class Parser(sly.Parser):
    tokens = Lexer.tokens

    @_("NAME transform_params")
    def transformation(self, p):
        name, in_degrees = p.NAME
        translation, rotation, inverted = p.transform_params
        return Transformation(
            translation=translation,
            rotation=rotation,
            indegrees=in_degrees,
            inverted=inverted,
            name=name,
        )

    @_("translation rotation")
    def transform_params(self, p):
        rotation, inverted = p.rotation
        return p.translation, rotation, inverted

    @_("translation")
    def transform_params(self, p):
        return p.translation, None, False

    @_("float float float")
    def translation(self, p):
        return list(p)

    # TODO dvp: check what to do, if transformation is specified with default values using the MCNP J shortcuts?

    @_("float float float float float float float float float INTEGER")
    def rotation(self, p):
        m = p[9]
        if m not in {-1, 1}:
            msg = f"Invalid M option value {m}"
            raise ValueError(msg)
        return list(p)[:-1], m == -1

    @_(
        "float float float float float float float float float",
        "float float float float float float",
        "float float float float float",
        "float float float",
    )
    def rotation(self, p):
        return list(p), False

    @_("FLOAT")
    def float(self, p):
        return p.FLOAT

    @_("INTEGER")
    def float(self, p):
        return float(p.INTEGER)


def parse(text: str) -> Transformation:
    text = drop_c_comments(text)
    text, comments, trailing_comments = extract_comments(text)
    lexer = Lexer()
    parser = Parser()
    result: Transformation = parser.parse(lexer.tokenize(text))
    if trailing_comments:
        result.options["comment"] = trailing_comments
    return result
