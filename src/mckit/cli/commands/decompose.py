"""Разложение модели на составляющие юниверсы.

Читает модель, извлекает юниверсы первого уровня и сохраняет их
в каталог universes под именем uN.i, где N - номер юниверса.
Также сохраняет общую модель (без юниверсов) под именем envelopes.i
Создает спецификацию для последующей сборки модели в виде TOML файла.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import tomli_w as tw

from mckit import Universe
from mckit.cli.logging import logger
from mckit.parser.mcnp_input_sly_parser import ParseResult, from_file
from mckit.universe import collect_transformations

from .common import save_mcnp


def get_default_output_directory(source):
    return Path(Path(source).with_suffix(".universes").name)


def move_universe_attribute_to_comments(universe):
    no = universe.name()
    for cell in universe:
        cell.options.pop("U", None)
        comm = cell.options.get("comment", [])
        comm.append(f"U={no}")
        cell.options["comment"] = comm


def decompose(output, fill_descriptor_path, source, override):
    logger.info("Running mckit decompose")
    logger.debug("Working dir {}", Path().absolute())
    logger.info("Processing {}", source)
    logger.debug("Loading model from {}", source)
    source = Path(source)
    if output is None:
        output = get_default_output_directory(source)
    else:
        output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    parse_result: ParseResult = from_file(source)
    model: Universe = parse_result.universe
    named_transformations = list(collect_transformations(model))
    already_processed_universes = set()
    # TODO dvp: check ordering of items in resulting file
    fill_descriptor = {
        "title": parse_result.title,
        "source": source.name,
        "comment": model.comment if model.comment else "",
        "created": datetime.now(),
    }
    for c in model:
        fill = c.options.pop("FILL", None)
        if fill:
            universe = fill["universe"]
            words = [f"FILL={universe.name()}"]
            transform = fill.get("transform", None)
            if transform:
                words[0] = "*" + words[0]
                words.append("(")
                words.extend(transform.get_words())
                words.append(")")
            comm = c.options.get("comment", [])
            comm.append("".join(words))
            c.options["comment"] = comm
            descriptor = {}
            universe_name = universe.name()
            fn = f"u{universe_name}.i"
            descriptor["universe"] = universe_name
            if transform:
                name = transform.name()
                if name is None:
                    # The transformation is anonymous, so, store its specification
                    # omitting redundant '*', TR0 words, and interleaving space tokens
                    descriptor["transform"] = transform.mcnp_words()[2:][1::2]
                else:
                    descriptor["transform"] = name
            descriptor["file"] = fn
            fill_descriptor[str(c.name())] = descriptor
            if universe_name not in already_processed_universes:
                move_universe_attribute_to_comments(universe)
                save_mcnp(universe, output / fn, override)
                logger.debug("The universe {} has been saved to {}", universe_name, fn)
                already_processed_universes.add(universe_name)

    named_transformations_descriptor = {}
    named_transformations = sorted(named_transformations, key=lambda x: x.name())
    for t in named_transformations:
        named_transformations_descriptor[f"tr{t.name()}"] = t.mcnp_words()[2:][1::2]
    fill_descriptor["named_transformations"] = named_transformations_descriptor

    fdp = output / fill_descriptor_path
    with fdp.open("wb") as fid:
        tw.dump(fill_descriptor, fid)
    logger.debug("Fill descriptor is saved in {}", fdp)
    envelopes_path = output / "envelopes.i"
    save_mcnp(model, envelopes_path, override)
    logger.debug("The envelopes are saved to {}", envelopes_path)
