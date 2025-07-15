from __future__ import annotations

import numpy as np

from mckit.utils import get_decades, significant_digits


def run_significant_digits(a: np.ndarray) -> None:
    map(significant_digits, a)


def test_significant_digits(benchmark) -> None:
    values = (np.random.default_rng().random(1000) - 0.5) * 1000.0
    benchmark(run_significant_digits, values)


def run_get_decades(a: np.ndarray) -> None:
    return np.fromiter(map(get_decades, a), np.int16)


def test_get_decades(benchmark) -> None:
    values = (np.random.default_rng().random(1000) - 0.5) * 1000.0
    benchmark(run_get_decades, values)


# Name (time in ms)        Min     Max    Mean  StdDev  Median     IQR  Outliers       OPS  Rounds  Iterations
# test_get_decades      2.8199  5.4146  2.9415  0.2459  2.8766  0.0728     12;45  339.9577     331           1
