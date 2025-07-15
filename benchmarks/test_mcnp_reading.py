"""Tests with benchmarks on large mcnp files.

To use it install plugin pytest-benchmark (https://pytest-benchmark.readthedocs.io/en/latest/index.html#)
    conda install pytest-benchmark
    or
    pip install pytest-benchmark
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mckit.parser.mcnp_input_sly_parser import from_text

if TYPE_CHECKING:
    from mckit.parser.mcnp_input_sly_parser import ParseResult


def test_sly_mcnp_reading(benchmark, clite_text) -> None:
    """Benchmark parsing MCNP model using SLY package."""
    result: ParseResult = benchmark(from_text, clite_text)
    assert result.title == "C-LITE VERSION 1 RELEASE 131031 ISSUED 31/10/2013 - Halloween edition"
    assert len(result.universe) == 150


if __name__ == "__main__":
    pytest.main(["--benchmark-enable"])
