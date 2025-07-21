from __future__ import annotations

from typing import TYPE_CHECKING

import sly

import mckit.parser.common.utils as pu  # parse utils

from mckit.parser.common import Lexer as LexerBase
from mckit.parser.common import TransformationStrictIndex
from mckit.parser.common.utils import drop_c_comments, extract_comments
from mckit.surface import Surface, create_surface
from mckit.utils.indexes import Index

if TYPE_CHECKING:
    from typing import ClassVar

SURFACE_TYPES = {
    "P",
    "PX",
    "PY",
    "PZ",
    "S",
    "SO",
    "SX",
    "SY",
    "SZ",
    "CX",
    "CY",
    "CZ",
    "C/X",
    "C/Y",
    "C/Z",
    "KX",
    "KY",
    "KZ",
    "K/X",
    "K/Y",
    "K/Z",
    "TX",
    "TY",
    "TZ",
    "SQ",
    "GQ",
    "X",
    "Y",
    "Z",
    "RPP",
    "RCC",
    "BOX",
}


def intern_surface_type(word: str):
    word = pu.ensure_upper(word)
    word, res = pu.internalize(word, SURFACE_TYPES)
    if not res:
        raise pu.ParseError(f"{word} is not a valid surface type")
    return word


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyUnresolvedReferences,SpellCheckingInspection
class Lexer(LexerBase):
    tokens: ClassVar = {MODIFIER, SURFACE_TYPE, FLOAT, INTEGER}

    MODIFIER = r"^\s{,5}(\*|\+)"
    SURFACE_TYPE = r"[a-z]+(?:/[a-z]+)?"
    FLOAT = pu.FLOAT
    INTEGER = pu.INTEGER

    @_(r"[a-z]+(?:/[a-z]+)?")
    def SURFACE_TYPE(self, t):
        t.value = intern_surface_type(t.value)
        return t

    @_(pu.FLOAT)
    def FLOAT(self, t):
        return LexerBase.on_float(t, use_zero=False)

    @_(pu.INTEGER)
    def INTEGER(self, t):
        return LexerBase.on_integer(t, use_zero=False)


# noinspection PyUnresolvedReferences
class Parser(sly.Parser):
    tokens = Lexer.tokens

    def __init__(self, transformations: Index):
        sly.Parser.__init__(self)
        self._transformations = transformations

    @property
    def transformations(self):
        return self._transformations

    def build_surface(
        self, name: int, kind: str, params: list[float], transform, modifier
    ) -> Surface:
        options = {"name": name}
        if transform is not None:
            transformation = self.transformations[transform]
            if transformation:
                options["transform"] = transformation
        if modifier is not None:
            options["modifier"] = modifier
        return create_surface(kind, *params, **options)

    @_("MODIFIER  name surface_description")
    def surface(self, p):
        (
            kind,
            params,
            transform,
        ) = p.surface_description  # type: str, List[float], Optional[int]
        return self.build_surface(p.name, kind, params, transform, p.MODIFIER)

    @_("name surface_description")
    def surface(self, p):
        (
            kind,
            params,
            transform,
        ) = p.surface_description  # type: str, List[float], Optional[int]
        return self.build_surface(p.name, kind, params, transform, None)

    @_("INTEGER")
    def name(self, p):
        return p.INTEGER

    @_("transform SURFACE_TYPE surface_params")
    def surface_description(self, p) -> tuple[str, list[float], int | None]:
        return p.SURFACE_TYPE, p.surface_params, p.transform

    @_("SURFACE_TYPE surface_params")
    def surface_description(self, p) -> tuple[str, list[float], int | None]:
        return p.SURFACE_TYPE, p.surface_params, None

    @_("INTEGER")
    def transform(self, p):
        return p.INTEGER

    @_("surface_params float")
    def surface_params(self, p) -> list[float]:
        surface_params: list[float] = p.surface_params
        surface_params.append(p.float)
        return surface_params

    @_("float")
    def surface_params(self, p) -> list[float]:
        return [p.float]

    @_("FLOAT")
    def float(self, p):
        return p.FLOAT

    @_("INTEGER")
    def float(self, p) -> float:
        return float(p.INTEGER)


def parse(text: str, transformations: Index | None = None) -> Surface:
    if transformations is None:
        transformations = TransformationStrictIndex()
    else:
        assert isinstance(transformations, Index)
    text = drop_c_comments(text)
    text, comments, trailing_comments = extract_comments(text)
    lexer = Lexer()
    parser = Parser(transformations)
    result = parser.parse(lexer.tokenize(text))
    if trailing_comments:
        result.options["comment"] = trailing_comments
    return result
