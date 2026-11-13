from __future__ import annotations

import numpy as np
import pytest

from mckit.utils import (
    FLOAT_TOLERANCE,
    are_equal,
    compute_hash,
    filter_dict,
    get_decades,
    is_in,
    is_sorted,
    make_hashable,
    prettify_float,
    significant_digits,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (15.0, 1),
        (10.0, 1),
        (1.5, 0),
        (1.0, 0),
        (0.5, -1),
        (0.0011, -3),  # TODO dvp: check this strange values
        (0.001, -4),  # ...
        (0.01, -3),  # ...
        (0.1, -2),
        (1e-12, -13),
        (0.0, 0),
        (-1e-12, -13),
        (-0.01, -3),
        (-0.001, -4),
        (-0.0011, -3),
        (-0.5, -1),
        (-1.0, 0),
        (-1.5, 0),
        (-10.0, 1),
        (-15.0, 1),
    ],
)
def test_get_decades(value, expected):
    assert get_decades(value) == expected


@pytest.mark.parametrize(
    "value, reltol, resolution, expected",
    [
        (1.0, 1e-12, FLOAT_TOLERANCE, 0),
        (1.1, 1e-12, FLOAT_TOLERANCE, 1),
        (11.0, 1e-12, FLOAT_TOLERANCE, 0),
        (
            11.11,
            1e-12,
            FLOAT_TOLERANCE,
            2,
        ),  # TODO dvp: looks like the function should be called `digits_in_fraction`.
    ],
)
def test_significant_digits(value, reltol, resolution, expected):
    actual = significant_digits(value, reltol, resolution)
    assert actual == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (None, None, True),
        (None, "a", False),
        ("abc", "abc", True),
        (1, 1, True),
        (1, -1, False),
        (np.arange(10), np.arange(10), True),
        ([1, "a", np.arange(3)], [1, "a", np.arange(3)], True),
        ([1, "a", np.arange(3)], [2, "a", np.arange(3)], False),
        ([1, "a", np.arange(3)], [1, "a", np.arange(3), "a"], False),
    ],
)
def test_are_equal(a, b, expected):
    actual = are_equal(a, b)
    assert actual == expected


@pytest.mark.parametrize(
    "dictionary, drop_items, expected",
    [
        ({"a": 1, "b": 2}, "b", {"a": 1}),
        ({"a": 1, "b": 2, "c": 3}, frozenset(("b", "c")), {"a": 1}),
        ({"a": 1, "b": {"c": 3}}, "c", {"a": 1, "b": {}}),
        ({"a": 1, "b": {"c": 3}}, lambda x: x == "a", {"b": {"c": 3}}),
        ({"a": [1, 2], "b": "s"}, "c", {"a": [1, 2], "b": "s"}),
    ],
)
def test_deep_copy_dict(dictionary, drop_items, expected):
    actual = filter_dict(dictionary, drop_items)
    assert actual == expected


@pytest.mark.parametrize("values", [("abc",), ({1: {"a": 2}}, np.arange(10)), (None,)])
def test_make_hash(values):
    compute_hash(*values)


@pytest.mark.parametrize(
    "value, expected",
    [
        (1.0, "1"),
        (0.000000000001, "1e-12"),
        (0.00000000000101, "1.01e-12"),
        (5.00000000001, "5.00000000001"),
        (-2.828427124746, "-2.828427124746"),
    ],
)
def test_prettify_float(value, expected):
    actual = prettify_float(value)
    assert actual == expected


def test_are_equal_iterables_vs_not_iterable():
    assert are_equal([1, 2, 3], 3) is False
    assert are_equal([1, 2, 3], (1, 2, 3)) is True


def test_is_in():
    assert is_in(None, 1) is False
    assert is_in(3, 3) is True
    assert is_in(3, 4) is False


def test_is_in_with_different_containers():
    assert is_in("abc", "b") is True
    assert is_in((1, 2), 2) is True
    assert is_in({1, 2}, 2) is True
    assert is_in(lambda x: x > 0, 1) is True
    assert is_in(lambda x: x > 0, -1) is False


def test_make_hashable_unsupported_type():
    class Unhashable:
        __hash__ = None

    with pytest.raises(TypeError, match="hashable"):
        make_hashable(Unhashable())


def test_compute_hash_of_nothing():
    assert compute_hash() == 0


@pytest.mark.parametrize(
    "array, expected",
    [
        (np.array([1.0, 2.0, 3.0]), True),
        (np.array([1.0, 3.0, 2.0]), False),
        (np.array([1.0, 1.0]), False),
    ],
)
def test_is_sorted(array, expected):
    assert is_sorted(array) == expected
