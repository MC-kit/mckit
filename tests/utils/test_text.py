from __future__ import annotations

import re

import pytest

from mckit.utils import match_comment


@pytest.mark.parametrize(
    "comment, search, expected", [(["$ sphere"], "sphere", True), (["$ sphere"], "cube", False)]
)
def test_match_str(comment, search, expected):
    actual = match_comment(comment, search)
    assert actual == expected


@pytest.mark.parametrize(
    "comment, search, expected",
    [(["$ sphere"], r"sph[a-z]", True), (["$ sphere"], r"sph[^a-z]", False)],
)
def test_match_pattern(comment, search, expected):
    pattern = re.compile(search)
    actual = match_comment(comment, pattern)
    assert actual == expected


@pytest.mark.parametrize(
    "comment, search, expected", [(["$ sphere"], "sphere", True), (["$ sphere"], "cube", False)]
)
def test_match_callable(comment, search, expected):
    def _call(s: str) -> bool:
        return search in s

    actual = match_comment(comment, _call)
    assert actual == expected


def test_match_unknown_predicate():
    comment = ["$ sphere"]
    with pytest.raises(ValueError, match="Predicate of unknown type"):
        match_comment(comment, 1)
