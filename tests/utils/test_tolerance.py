from __future__ import annotations

import numpy as np
import pytest

from mckit.utils.tolerance import DEFAULT_TOLERANCE_ESTIMATOR

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
        (1, 1, True, "#6 Integers"),
    ],
)
def test_tolerance_estimator(a, b, expected, msg):
    actual = DEFAULT_TOLERANCE_ESTIMATOR(a, b)
    assert actual == expected, msg


if __name__ == "__main__":
    pytest.main()
