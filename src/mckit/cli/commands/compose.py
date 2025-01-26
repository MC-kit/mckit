"""Сборка модели из конвертов и входяших в них юниверсов по заданной спецификации."""

from __future__ import annotations

import sys

from functools import reduce
from pathlib import Path

import numpy as np

import mckit as mk

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from mckit import Transformation
from mckit.cli._logging import logger
from mckit.parser.mcnp_input_sly_parser import ParseResult, from_file
from mckit.utils import filter_dict

from .common import save_mcnp


def compose(output, fill_descriptor_path, source, override):
    logger.info("Loading model from {s}", s=source)
    parse_result: ParseResult = from_file(source)
    envelopes = parse_result.universe
    source = Path(source)
    universes_dir = source.absolute().parent
    assert universes_dir.is_dir()
    logger.info("Loading fill-descriptor from {f}", f=fill_descriptor_path)
    with fill_descriptor_path.open("rb") as fid:
        fill_descriptor = tomllib.load(fid)

    universes = load_universes(fill_descriptor, universes_dir)
    named_transformations = load_named_transformations(fill_descriptor)

    comps = {}

    for k, v in universes.items():
        u, _ = v
        cps = u.get_compositions()
        comps[k] = set(cps)

    common = reduce(set.union, comps.values())
    envelopes.set_common_materials(common)
    cells_index = {cell.name(): cell for cell in envelopes}

    for i, spec in universes.items():
        universe, transformation = spec
        universe.set_common_materials(common)
        cell = cells_index[i]
        cell.options = filter_dict(cell.options, "original")
        cell.options["FILL"] = {"universe": universe}
        if transformation is not None:
            # if isinstance(transformation, tk_items.Array):
            if isinstance(transformation, list):
                transformation1 = np.fromiter(map(float, iter(transformation)), dtype=np.double)
                try:
                    translation = transformation1[:3]
                    if len(transformation1) > 3:
                        rotation = transformation1[3:]
                    else:
                        rotation = None
                    transformation2 = mk.Transformation(
                        translation=translation,
                        rotation=rotation,
                        indegrees=True,  # Assuming that on decompose we store a transformation in degrees as well
                    )
                except ValueError as ex:
                    raise ValueError(
                        f"Failed to process FILL transformation in cell #{cell.name()} of universe #{universe.name()}"
                    ) from ex
                cell.options["FILL"]["transform"] = transformation2
            # elif isinstance(transformation, tk_items.Integer):
            elif isinstance(transformation, int):
                assert named_transformations is not None, (
                    "There are no named transformations in the fill descriptor file"
                )
                transformation1 = named_transformations[int(transformation)]
                cell.options["FILL"]["transform"] = transformation1
            else:
                raise NotImplementedError(
                    f"Unexpected type of transformation parameter {type(transformation)}"
                )
    save_mcnp(envelopes, output, override)


def load_universes(
    fill_descriptor, universes_dir
) -> dict[int, tuple[mk.Universe, int | list[float]]]:
    filler_path_map: dict[int, tuple[Path, mk.Universe]] = {}
    cell_filler_map: dict[int, tuple[mk.Universe, int | list[float]]] = {}

    for k, v in fill_descriptor.items():
        if isinstance(v, dict) and "universe" in v:
            cell_name = int(k)
            universe_name = int(v["universe"])
            transformation = v.get("transform", None)
            universe_path = Path(v["file"])
            if universe_name in filler_path_map:
                prev_path, prev_universe = filler_path_map[universe_name]
                if prev_path == universe_path:
                    universe = prev_universe
                else:
                    raise ValueError(
                        f'\n \
                        Filler number {universe_name} specifies different paths to load \n \
                        "{prev_path}" and "{universe_path}"'
                    )
            else:
                if universe_path.exists():
                    load_path = universe_path
                else:
                    load_path = universes_dir / universe_path
                if not load_path.exists():
                    raise FileNotFoundError(universe_path)
                logger.info("Loading file {u}", u=load_path)
                parse_result: ParseResult = from_file(load_path)
                universe = parse_result.universe
                universe.rename(name=universe_name)
                filler_path_map[universe_name] = (universe_path, universe)

            cell_filler_map[cell_name] = (universe, transformation)

    return cell_filler_map


def load_named_transformations(fill_descriptor) -> dict[int, Transformation] | None:
    transformations = fill_descriptor.get("named_transformations", None)
    if transformations:
        named_transformations = {}
        for k, v in transformations.items():
            name = int(k[2:])
            transform_params = np.fromiter(map(float, v), dtype=float)
            translation = transform_params[:3]
            if transform_params.size == 9:
                rotation = transform_params[3:]
            else:
                rotation = None
            transform = Transformation(
                translation=translation, rotation=rotation, indegrees=True, name=name
            )
            named_transformations[name] = transform
        return named_transformations
    return None
