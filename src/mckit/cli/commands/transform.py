"""Apply transformation to a model."""

from __future__ import annotations

from pathlib import Path

from mckit.cli._logging import logger
from mckit.parser.mcnp_input_sly_parser import ParseResult, from_file
from mckit.parser.mcnp_section_parser import clean_mcnp_cards, split_to_cards
from mckit.parser.transformation_parser import parse as parse_transformation
from mckit.universe import Universe
from mckit.utils.indexes import IndexOfNamed, raise_on_duplicate_strategy

from .common import save_mcnp


def transform(
    output: Path,
    transformation: int,
    transformations: Path,
    source: Path,
    override: bool,
) -> None:
    logger.info("Running mckit transform")
    logger.debug("Working dir {}", Path().absolute())
    logger.info("Transforming model from {s}", s=source)
    if output.exists() and not override:
        raise FileExistsError(f"File {output} already exists. Remove it or use --override option")
    parse_result: ParseResult = from_file(source)
    src: Universe = parse_result.universe
    logger.debug("Loading transformations {} from {}", transformation, transformations)
    transformations_text = transformations.read_text()
    transformations_list = [
        parse_transformation(c.text) for c in clean_mcnp_cards(split_to_cards(transformations_text))
    ]
    transformations_index = IndexOfNamed.from_iterable(
        transformations_list,
        on_duplicate=raise_on_duplicate_strategy,
    )
    if transformation not in transformations_index:
        raise ValueError(f"Transformation {transformation} is not found in {transformations}")
    the_transformation = transformations_index[transformation]
    dst = src.transform(the_transformation)
    save_mcnp(dst, output, override)
    logger.success("Transformed model is saved to {}", output)
