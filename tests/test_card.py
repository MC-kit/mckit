from __future__ import annotations

import re

import pytest

from mckit.card import Card


class DummyCard(Card):
    def mcnp_words(self, pretty=False):
        return [f"{k}: {v}" for k, v in (self._extra or {}).items()]


@pytest.mark.parametrize(
    "a, b, expected_eq, expected_hash",
    [
        ({"a": 1}, {}, False, True),
        ({"a": 1}, {"a": 1}, True, True),
        ({"a": 1}, {"b": 1}, False, True),
        ({"a": 1}, {"a": 1, "b": 2}, False, True),
        ({"a": 1, "b": 2}, {"a": 1, "b": 2}, True, True),
        ({"a": 1, "b": 2}, {"a": 1}, False, True),
        ({"a": 1}, {"a": 2}, False, True),
        ({"name": 1, "a": 1}, {"name": 1, "a": 1}, True, True),
        ({"name": 1, "a": 1}, {"name": 2, "a": 1}, False, False),
    ],
)
def test_eq(a, b, expected_eq, expected_hash):
    c = a
    assert a == c  # need to execute __eq__ with comparison to itself
    c = b
    assert b == c
    da, db = DummyCard(**a), DummyCard(**b)
    actual = da == db
    assert actual == expected_eq
    assert not expected_eq or (expected_eq and expected_hash)
    assert (hash(da) == hash(db)) == expected_hash


def test_str():
    card = DummyCard(name=1, a=2)
    assert str(card) == "1: \"{'a': 2}\""


def test_anonymous():
    card = DummyCard()
    assert card.is_anonymous
    assert card.name() is None
    assert hash(card) == 0


def test_original_and_rename():
    card = DummyCard(name=1, original="old text", comment_above="note")
    assert card.has_original
    assert card.original == "old text"
    assert card.has_comment_above
    assert card.comment_above == "note"
    card.rename(2)
    assert card.name() == 2
    assert not card.has_original  # rename drops the original option


def test_add_comment_and_match_comment():
    card = DummyCard(name=1)
    assert not card.match_comment("zzz")  # no comments yet
    card.add_comment("some text here")
    assert card.comment == ["some text here"]
    assert card.match_comment("some text")
    assert not card.match_comment("absent")
    assert card.match_comment(re.compile(r"text\s+here"))
    assert not card.match_comment(re.compile(r"absent"))
    assert card.match_comment(lambda line: line.startswith("some"))
    assert not card.match_comment(lambda line: False)


def test_eq_with_other_types():
    card = DummyCard(name=1)
    assert card != "not a card"
