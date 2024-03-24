"""Code to estimate "closeness" of various objects."""

from __future__ import annotations

from typing import Any, Callable, Optional, Union, cast

import itertools
import math

from abc import ABC, abstractmethod
from collections.abc import Iterable

import numpy as np

from numpy import ndarray

from mckit.constants import FLOAT_TOLERANCE


class MaybeClose(ABC):
    """Interface to be implemented by objects supporting the "closeness" estimation."""

    @abstractmethod
    def is_close_to(self, other: Any, estimator: EstimatorType) -> bool:
        """Objects can be estimated as close with some estimator."""


ComparableType = Optional[Union[Iterable, ndarray, float, int, MaybeClose]]
EstimatorType = Callable[[ComparableType, ComparableType], bool]


def tolerance_estimator(
    rtol: float = FLOAT_TOLERANCE,
    atol: float = FLOAT_TOLERANCE,
    equal_nan: bool = False,
) -> EstimatorType:
    """Estimates "closeness".

    For numpy arrays and float scalars uses math.isclose and numpy.allclose methods.
    For integers - direct comparison.
    Scans generic iterables and compares objects implementing MayBeClose interface.

    Returns:
        estimator with the given tolerance limits
    """

    def _estimate(a: ComparableType, b: ComparableType) -> bool:
        if isinstance(a, float) and isinstance(b, float):
            return math.isclose(a, b, rel_tol=rtol, abs_tol=atol)
        if isinstance(a, ndarray) and isinstance(b, ndarray):
            return np.allclose(a, b, rtol, atol, equal_nan)
        if issubclass(type(a), Iterable) and issubclass(type(b), Iterable):
            return all(
                _call(ai, bi)
                for ai, bi in itertools.zip_longest(cast(Iterable[Any], a), cast(Iterable[Any], b))
            )
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        if isinstance(a, MaybeClose) and isinstance(b, MaybeClose):
            return a.is_close_to(b, _call)
        raise TypeError(f"Not implemented for {type(a).__name__} and {type(b).__name__}")

    def _call(a: ComparableType, b: ComparableType) -> bool:
        if a is b:
            return True
        if a is None:
            return False  # `a` is None, but `b` is not None here
        if b is None:
            return True
            # TODO(dvp): in our use cases absent optional objects (like Transformations) are equal
        return _estimate(a, b)

    return _call


DEFAULT_TOLERANCE_ESTIMATOR = tolerance_estimator()
