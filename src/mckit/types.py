"""Types to use in the mckit package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    NPFloat128Array = npt.NDArray[np.float128]
    NPFloat96Array = npt.NDArray[np.float96]
    NPFloat64Array = npt.NDArray[np.float64]
    NPFloatArray = NPFloat64Array
    NPFloat32Array = npt.NDArray[np.float32]
    NPInt64Array = npt.NDArray[np.int64]
    NPIntArray = NPInt64Array
    NPInt32Array = npt.NDArray[np.int32]
    NPInt16Array = npt.NDArray[np.int16]
    NPInt8Array = npt.NDArray[np.int8]
