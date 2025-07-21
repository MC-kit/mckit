import numpy as np

R = 400
"""Major radius to measure toroidal coil thickness at."""

d = 50
"""Thickness of toroidal coil at R."""

n = 16
"""Number of toroidal coil segments."""

a = d / (2 * np.pi * R)
"""Toroidal coil sector width in rotations."""

b = 1 / n - a
"""Toroidal coil gap width in rotations."""


def calc_theta(_a, _b, _n):
    """Compute VEC and KMESH values for cylinder mesh for TRT."""
    alpha = _a * np.pi
    _vec = [
        np.cos(alpha),
        np.sin(alpha),
        0.0,
    ]  # TODO dvp: not sin() is positive and this gives correct result
    _theta = np.array([_a, _a + _b])
    for i in range(_n - 1):
        prev_b = _theta[-1]
        _theta = np.append(_theta, [prev_b + _a, prev_b + _a + _b])
    assert _theta[-1] == 1.0
    return _vec, _theta


if __name__ == "__main__":
    vec, theta = calc_theta(a, b, n)
    print("vec", " ".join(map(str, vec)))
    print("kmesh", " ".join(map(str, theta)))
