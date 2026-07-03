"""Benchmark computationally intensive Shape class methods."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import heapq as hq
from zipfile import ZipFile

import pytest

from mckit import Shape, Universe
from mckit.box import Box
from mckit.parser import from_text

if TYPE_CHECKING:
    from mckit import Body

HERE = Path(__file__).parent
data = HERE / "data"

with ZipFile( data / "4M.zip") as data_archive:
    clite_text = data_archive.read("clite.i").decode(encoding="utf8")

clite_model = from_text(clite_text).universe


def sample_by_complexity(model: Universe, size=10) -> list[tuple[int, Body]]:
    def _key(x):
        return x.shape.complexity()

    complex_cells = sorted(hq.nlargest(size, model, key=_key), key=_key)

    return [(_key(cell), cell)  for cell in complex_cells]

sampled_by_complexity = sample_by_complexity(clite_model)

@pytest.mark.parametrize("complexity, cell", sampled_by_complexity)
def test_bounding_box(benchmark, complexity, cell) -> None:
    gb = Box([692.0, 27.0, -313.0], 3700.0, 1400.0, 4500.0)
    benchmark.extra_info["complexity"] = complexity
    benchmark.extra_info["cell"] = cell.name()
    shape = cell.shape
    benchmark.pedantic(Shape.bounding_box, args=(shape,), kwargs={"box": gb, "tol": 10.0})


def test_universe_bounding_box(benchmark) -> None:
    gb = Box([1500, 0, 0], 4000.0, 4000.0, 6000.0)
    box = benchmark.pedantic(
        Universe.bounding_box,
        args=(clite_model,),
        kwargs={"box": gb, "tol": 20.0, "skip_graveyard_cells": True},
    )
    assert box.center == pytest.approx([1744.0, -0.48828, 170.17], rel=1e-3)
    assert box.dimensions == pytest.approx([3511.8, 1251.0, 3292.5], rel=1e-3)


@pytest.mark.parametrize("complexity, cell", sampled_by_complexity)
def test_cell_volume(benchmark, complexity, cell) -> None:
    gb = Box([692.0, 27.0, -313.0], 4000.0, 2000.0, 5000.0)
    benchmark.extra_info["complexity"] = complexity
    benchmark.extra_info["cell"] = cell.name()
    shape = cell.shape
    benchmark.pedantic(Shape.volume, args=(shape,), kwargs={"box": gb, "min_volume": 10.0})


if __name__ == "__main__":
    pytest.main(["--benchmark-enable", "--benchmark-autosave"])
