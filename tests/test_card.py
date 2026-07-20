from __future__ import annotations

import pytest

from mckit.card import Card


class DummyCard(Card):
    def mcnp_words(self, pretty=False):
        return [f"{k}: {v}" for k, v in self.options]


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
