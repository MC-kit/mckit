from __future__ import annotations

import io
import pickle


def pass_through_pickle(surf):
    with io.BytesIO() as f:
        pickle.dump(surf, f)
        f.seek(0)
        return pickle.load(f)  # noqa: S301 `pickle` and modules that wrap it can be unsafe
