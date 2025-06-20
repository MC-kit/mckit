from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path
from zipfile import ZipFile

import pytest

from mckit.constants import MCNP_ENCODING

if TYPE_CHECKING:
    from collections.abc import Callable

HERE = Path(__file__).parent
DATA = HERE / "data"


@pytest.fixture(scope="session")
def data() -> Callable[[str], Path]:
    """Benchmarks data folder."""
    return lambda x: DATA / x


@pytest.fixture(scope="session")
def clite_text(data) -> str:
    """C-lite model text.

    Returns:
        Loaded text of a C-lite model.
    """
    with ZipFile(data("data/4M.zip")) as data_archive:
        return data_archive.read("clite.i").decode(encoding=MCNP_ENCODING)
