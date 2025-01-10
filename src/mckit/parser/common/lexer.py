from __future__ import annotations

from typing import TYPE_CHECKING

import re

import sly


# noinspection PyProtectedMember
from sly.lex import LexError

IS_INTEGER_REGEX = re.compile(r"[-+]?\d+$")

if TYPE_CHECKING:
    from typing import ClassVar


# noinspection PyUnresolvedReferences,SpellCheckingInspection,PyTypeChecker
class Lexer(sly.Lexer):
    tokens: ClassVar = set()  # Should be defined in all subclasses of sly.Lexer
    literals: ClassVar = {":", "(", ")"}  # ---
    ignore = " \t&"  # most common for MCNP text parsers
    reflags = re.IGNORECASE | re.MULTILINE  # ---

    @staticmethod
    def on_float(token, use_zero=True, use_integer=True):
        if use_integer and IS_INTEGER_REGEX.match(token.value) is not None:
            token = Lexer.on_integer(token, use_zero)
        else:
            token.value = float(token.value)
        return token

    @staticmethod
    def on_integer(token, use_zero=True):
        token.value = int(token.value)
        if use_zero and token.value == 0:
            token.type = "ZERO"
        else:
            token.type = "INTEGER"
        return token

    @_(r"\n+")
    def ignore_newline(self, token):
        self.lineno += len(token.value)

    def get_start_of_line(self, token):
        return self.text.rfind("\n", 0, token.index)

    def get_end_of_line(self, token):
        next_cr = self.text.find("\n", token.index)
        if next_cr < 0:
            next_cr = len(self.text)
        return next_cr

    @staticmethod
    def column(token, prev_cr):
        return token.index - prev_cr

    def find_column(self, token):
        prev_cr = self.get_start_of_line(token)
        return Lexer.column(token, prev_cr)

    def error(self, token):
        prev_cr = self.get_start_of_line(token)
        next_cr = self.get_end_of_line(token)
        column = Lexer.column(token, prev_cr)
        msg = (
            f"Illegal character '{token.value[0]}', at line {self.lineno}, column {self.find_column(token)}\n"
            f"{self.text[prev_cr + 1 : next_cr]}\n" + " " * (column - 1) + "^"
        )
        raise LexError(msg, token.value, token.index)
