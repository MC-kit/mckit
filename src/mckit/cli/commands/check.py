"""Проверяет корректность модели и выдает статистику."""

from __future__ import annotations

from typing import Any, Callable

from collections.abc import Iterable
from pathlib import Path

from mckit import Universe
from mckit.card import Card
from mckit.cli.logging import logger
from mckit.parser.mcnp_input_sly_parser import ParseResult, from_file
from mckit.universe import collect_transformations


def check_duplicates(iterable: Iterable[Any] | None, label: str, key: Callable[[Any], Any]) -> None:
    if iterable is None:
        print(f"No {label}s are found")  # - don't use logger here, should go to stdout
    else:
        visited = set()
        for c in iterable:
            k = key(c)
            if k in visited:
                print(f"Duplicate of {label} {k} is found")
            else:
                visited.add(k)
        print(f"Total of {label}s: {len(visited)}")


def check(source):
    result = 0
    logger.info("Check model {}", source)
    source = Path(source)
    parse_result: ParseResult = from_file(source)
    model = parse_result.universe
    logger.debug("Read the model okay")
    universes = model.get_universes()
    check_duplicates(universes, "universe", Universe.name)
    cells = []
    surfaces = []
    transformations = []
    compositions = []
    for u in universes:
        cells.extend(u)
        surfaces.extend(u.get_surfaces(inner=False))
        transformations_to_add = collect_transformations(u)
        if transformations_to_add:
            transformations.extend(transformations_to_add)
        compositions.extend(u.get_compositions())
    if not transformations:
        transformations = None
    if not compositions:
        compositions = None
    check_duplicates(cells, "cell", Card.name)
    check_duplicates(surfaces, "surface", Card.name)
    check_duplicates(transformations, "transformation", Card.name)
    check_duplicates(compositions, "composition", Card.name)
    return result
