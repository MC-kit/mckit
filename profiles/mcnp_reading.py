"""Code to profile reading of a large mcnp file.

Not using pytest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path
from zipfile import ZipFile

from mckit.parser.mcnp_input_sly_parser import from_text

if TYPE_CHECKING:
    from mckit.parser.mcnp_input_sly_parser import ParseResult

HERE = Path(__file__).parent
DATA = HERE.parent / "benchmakrs/data"

with ZipFile(DATA / "4M.zip") as data_archive:
    CLITE_TEXT = data_archive.read("clite.i").decode(encoding="cp1251")


def demo_sly_mcnp_reading() -> None:
    result: ParseResult = from_text(CLITE_TEXT)
    assert result.title == "C-LITE VERSION 1 RELEASE 131031 ISSUED 31/10/2013 - Halloween edition"
    assert len(result.universe) == 150


if __name__ == "__main__":
    demo_sly_mcnp_reading()
