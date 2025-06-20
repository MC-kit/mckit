from __future__ import annotations

import re

from collections.abc import Iterable

C_COMMENT = r"(^|(?<=\n))\s{0,5}[cC]([ ][^\n]*)?\n?"
RE_C_COMMENT = re.compile(C_COMMENT, re.MULTILINE)
EOL_COMMENT = r"\$.*[^\n]*"
RE_EOL_COMMENT = re.compile(EOL_COMMENT, re.MULTILINE)
LINE = r"(?P<text>\s*[^ $][^$]*)?(?:\s*\$\s*(?P<comment>.*))?"  # text should contain at list one non-space character
RE_LINE = re.compile(LINE)
# FLOAT = r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?"
FLOAT = r"[+-]?((\d+\.?\d*)|(\.\d+))(?:[ed][-+]?\d+)?"
INTEGER = r"\d+"
RE_EMPTY_LINE = re.compile(r"\s*")


def ensure_lower(text: str):
    if not text.islower():
        return text.lower()
    return text


def ensure_upper(text: str):
    if not text.isupper():
        return text.upper()
    return text


def drop_c_comments(text: str) -> str:
    has_comments = RE_C_COMMENT.search(text)
    if has_comments:
        return RE_C_COMMENT.sub("", text)
    return text


def drop_eol_comments(text: str) -> str:
    if RE_EOL_COMMENT.search(text) is not None:
        return RE_EOL_COMMENT.sub("", text)
    return text


def drop_comments(text: str) -> str:
    return drop_eol_comments(drop_c_comments(text))


def extract_comments(text) -> tuple[str, dict[int, tuple[str, ...]] | None, list[str] | None]:
    lines = text.split("\n")
    cleaned_text: list[str] = []
    comments: list[tuple[int, list[str]]] = []
    trailing_comment: list[str] = []

    def add_trailing_to_previous_item():
        nonlocal comments, trailing_comment
        if trailing_comment:
            if len(comments) == 0:
                comments.append((1, trailing_comment))
            else:
                comments[-1][1].extend(trailing_comment)
            trailing_comment = []

    for i, line in enumerate(lines):
        if RE_EMPTY_LINE.fullmatch(line):
            cleaned_text.append(line)
        else:
            match = RE_LINE.fullmatch(line)
            assert match is not None
            groupdict = match.groupdict()
            t = groupdict["text"]
            c = groupdict["comment"]
            if t:
                cleaned_text.append(t)
                add_trailing_to_previous_item()
                if c is not None:
                    comments.append((i + 1, [c]))  # lexer counts lines from 1
            else:
                assert c is not None, "If there's no text, then at least comment should present"
                trailing_comment.append(c)

    assert cleaned_text, "There should be some  text in a card"

    res_comments = {k: tuple(v) for k, v in comments} if comments else None

    return "\n".join(cleaned_text), res_comments, trailing_comment if trailing_comment else None


class ParseError(ValueError):
    """Parsing exception."""


def internalize(word: str, words: Iterable[str]) -> tuple[str, bool]:
    """Replaces given `word` with the equal word from the list `words` to reuse the object for repeating small words."""
    for w in words:
        if w == word:
            return w, True
    return word, False
