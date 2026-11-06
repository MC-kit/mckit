from __future__ import annotations

import numpy as np
import pytest

from mckit.utils.tolerance import DEFAULT_TOLERANCE_ESTIMATOR, MaybeClose, tolerance_estimator

SOME_ARRAY = np.arange(3, dtype=float)


@pytest.mark.parametrize(
    "a, b, expected, msg",
    [
        (1.0, 1.0 + 1.0e-12, False, "#1 1.0e-12 is to be distinguished"),
        (1.0, 1.0 + 1.0e-13, True, "#2 1.0e-13 is not to be distinguished"),
        (
            SOME_ARRAY,
            SOME_ARRAY + 1.0e-11,
            False,
            "#3 on ndarray 1.0e-11 is to be distinguished",
        ),
        (
            SOME_ARRAY,
            SOME_ARRAY + 1.0e-13,
            True,
            "#4 on ndarray 1.0e-12 is not to be distinguished",
        ),
        ((1.0, SOME_ARRAY), (1.0, SOME_ARRAY), True, "#5 iterables"),
        ([1.0, 2.0], [1.0, 2.0], True, "#7 lists"),
        (1, 1, True, "#6 Integers"),
    ],
)
def test_tolerance_estimator(a, b, expected, msg):
    actual = DEFAULT_TOLERANCE_ESTIMATOR(a, b)
    assert actual == expected, msg


def test_none_cases():
    estimate = DEFAULT_TOLERANCE_ESTIMATOR
    assert estimate(None, None) is True  # identity
    assert estimate(None, 1.0) is False  # a is None, b is not
    assert estimate(1.0, None) is True  # absent optional objects are equal


def test_integer_comparison_on_distinct_objects():
    estimate = DEFAULT_TOLERANCE_ESTIMATOR
    a = 10**40
    b = 2 * 5 * 10**39
    assert a == b
    assert a is not b, "Test precondition: the object identity must not hold"
    assert estimate(a, b) is True
    assert estimate(10**40, 10**40 + 10) is False


class FakeMaybeClose(MaybeClose):
    def __init__(self, result: bool):
        self._result = result

    def is_close_to(self, other, estimator) -> bool:
        return self._result


def test_maybe_close_objects():
    estimate = DEFAULT_TOLERANCE_ESTIMATOR
    assert estimate(FakeMaybeClose(True), FakeMaybeClose(False)) is True
    assert estimate(FakeMaybeClose(False), FakeMaybeClose(True)) is False


def test_not_implemented_types():
    with pytest.raises(TypeError, match="Not implemented for float and int"):
        DEFAULT_TOLERANCE_ESTIMATOR(1.0, 1)


def test_custom_tolerance_estimator():
    estimate = tolerance_estimator(rtol=0.1, atol=0.1)
    assert estimate(1.0, 1.0 + 0.05) is True
    assert estimate(1.0, 2.0) is False


if __name__ == "__main__":
    pytest.main()
