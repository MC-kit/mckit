"""Code to profile on large mcnp files.

Not using pytest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zipfile import ZipFile

from mckit.constants import MCNP_ENCODING
from mckit.parser.mcnp_input_sly_parser import from_text
from mckit.utils._resource import path_resolver

if TYPE_CHECKING:
    from mckit.parser.mcnp_input_sly_parser import ParseResult

data_filename_resolver = path_resolver("benchmarks")
with ZipFile(data_filename_resolver("data/4M.zip")) as data_archive:
    CLITE_TEXT = data_archive.read("clite.i").decode(encoding=MCNP_ENCODING)


def test_sly_mcnp_reading() -> None:
    result: ParseResult = from_text(CLITE_TEXT)
    assert result.title == "C-LITE VERSION 1 RELEASE 131031 ISSUED 31/10/2013 - Halloween edition"
    assert len(result.universe) == 150


if __name__ == "__main__":
    test_sly_mcnp_reading()
