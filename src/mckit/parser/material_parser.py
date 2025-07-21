from __future__ import annotations

from typing import TYPE_CHECKING

import sly

import mckit.parser.common.utils as cmn

from mckit.material import Composition, Element
from mckit.parser.common.lexer import Lexer as LexerBase
from mckit.parser.common.utils import drop_comments

# noinspection PyPep8Naming,PyUnboundLocalVariable,PyUnresolvedReferences,SpellCheckingInspection
if TYPE_CHECKING:
    from typing import ClassVar


class Lexer(LexerBase):
    tokens: ClassVar = {NAME, FRACTION, OPTION}
    ignore = " \t="
    OPTION = r"(?:(?:gas|estep|cond)\s*[ =]\s*\d+)|(?:(?:n|p|pn|e)lib\s*[ =]\s*\S+)"

    @_(r"m\d+")
    def NAME(self, t):
        t.value = int(t.value[1:])
        return t

    @_(r"\d+(?:\.\d+[cdepuy])?\s+[-+]?((\d+(\.\d*)?)|(\.\d+))([eE][-+]?\d+)?")
    def FRACTION(self, t):
        isotop_spec, frac = t.value.split()
        frac = float(frac)
        if "." in isotop_spec:
            isotope, lib = isotop_spec.split(".")
            isotope = int(isotope)
            lib = cmn.ensure_lower(lib)
            t.value = isotope, lib, frac
        else:
            isotope = int(isotop_spec)
            t.value = isotope, None, frac
        return t


# noinspection PyUnresolvedReferences
class Parser(sly.Parser):
    tokens = Lexer.tokens

    def build_composition(self, name, fractions, options=None) -> Composition:
        atomic = []
        weight = []

        for el, fraction in fractions:
            if fraction < 0.0:
                weight.append((el, -fraction))
            else:
                atomic.append((el, fraction))

        if options is None:
            options = {}

        options["name"] = name

        return Composition(atomic=atomic, weight=weight, **options)

    @_("composition_a")
    def composition(self, p):
        name, fractions, options = p.composition_a
        return self.build_composition(name, fractions, options)

    @_("NAME fractions options")
    def composition_a(self, p):
        return p.NAME, p.fractions, p.options

    @_("NAME fractions")
    def composition_a(self, p):
        return p.NAME, p.fractions, None

    @_("fractions fraction")
    def fractions(self, p):
        p.fractions.append(p.fraction)
        return p.fractions

    @_("fraction")
    def fractions(self, p):
        return [p.fraction]

    # @_('fraction_a EOL_COMMENT')
    # def fraction(self, p):
    #     name, lib, frac = p.fraction_a
    #     return Element(name, lib=lib, comment=p.EOL_COMMENT), frac
    #
    @_("FRACTION")
    def fraction(self, p):
        name, lib, frac = p.FRACTION
        return Element(name, lib=lib), frac

    @_("options option")
    def options(self, p):
        option, value = p.option
        p.options[option] = value
        return p.options

    @_("option")
    def options(self, p):
        option, value = p.option
        return {option: value}

    @_("OPTION")
    def option(self, p):
        text: str = p.OPTION
        if "=" in text:
            text = text.replace("=", " ", 1)
        option, value = text.split()
        option = cmn.ensure_upper(option)
        if option in ("GAS", "ESTEP", "COND"):
            value = int(value)
        return option, value


def parse(text) -> Composition:
    text = drop_comments(text)
    lexer = Lexer()
    parser = Parser()
    return parser.parse(lexer.tokenize(text))
