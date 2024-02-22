"""
 Read and parse MCNP file text.
"""

from __future__ import annotations

from typing import Callable, TextIO

from collections.abc import Iterable, Iterator
from itertools import repeat
from pathlib import Path

from attr import attrib, attrs
from mckit.card import Card
from mckit.constants import MCNP_ENCODING
from mckit.parser.cell_parser import Body
from mckit.parser.cell_parser import parse as parse_cell
from mckit.parser.common import (
    CellNotFoundError,
    CellStrictIndex,
    CompositionStrictIndex,
    ParseError,
    SurfaceStrictIndex,
    TransformationStrictIndex,
)
from mckit.parser.material_parser import Composition
from mckit.parser.material_parser import parse as parse_composition
from mckit.parser.surface_parser import Surface
from mckit.parser.surface_parser import parse as parse_surface
from mckit.parser.transformation_parser import Transformation
from mckit.parser.transformation_parser import parse as parse_transformation
from mckit.universe import Universe, produce_universes
from mckit.utils.indexes import Index

from .mcnp_section_parser import Card as TextCard
from .mcnp_section_parser import InputSections, Kind, distribute_cards, parse_sections_text


@attrs
class ParseResult:
    universe: Universe = attrib()
    cells: list[Body] = attrib()
    cells_index: CellStrictIndex = attrib()
    surfaces: list[Surface] = attrib()
    surfaces_index: SurfaceStrictIndex = attrib()
    compositions: list[Composition] | None = attrib()
    compositions_index: CompositionStrictIndex | None = attrib()
    transformations: list[Transformation] | None = attrib()
    transformations_index: TransformationStrictIndex | None = attrib()
    sections: InputSections = attrib()

    @property
    def title(self):
        return self.sections.title


def from_file(path: str | Path) -> ParseResult:
    if isinstance(path, str):
        path = Path(path)
    with path.open("r", encoding=MCNP_ENCODING) as fid:
        return from_stream(fid)


def from_stream(stream: TextIO) -> ParseResult:
    text = stream.read()
    return from_text(text)


def from_text(text: str) -> ParseResult:
    sections: InputSections = parse_sections_text(text)
    if sections.data_cards:
        # fmt: off
        text_compositions, text_transformations, _1, _2, _3 = distribute_cards(
            sections.data_cards
        )  # type: list[TextCard], list[TextCard], list[TextCard], list[TextCard], list[TextCard],
        # fmt: on
        transformations = parse_transformations(text_transformations)
        transformations_index = TransformationStrictIndex.from_iterable(transformations)
        compositions = parse_compositions(text_compositions)
        compositions_index = CompositionStrictIndex.from_iterable(compositions)
    else:
        transformations = None
        transformations_index = None
        compositions = None
        compositions_index = None

    surfaces = (
        None
        if sections.surface_cards is None
        else parse_surfaces(sections.surface_cards, transformations_index)
    )
    surfaces_index = None if surfaces is None else SurfaceStrictIndex.from_iterable(surfaces)
    cells, cells_index = parse_cells(
        sections.cell_cards, surfaces_index, compositions_index, transformations_index
    )
    universe = produce_universes(
        cells
    )  # TODO dvp: apply title from sections to the topmost universe
    return ParseResult(
        universe=universe,
        cells=cells,
        cells_index=cells_index,
        surfaces=surfaces,
        surfaces_index=surfaces_index,
        compositions=compositions,
        compositions_index=compositions_index,
        transformations=transformations,
        transformations_index=transformations_index,
        sections=sections,
    )


def join_comments(text_cards: Iterable[TextCard]):
    def _iter():
        comment: str | None = None
        for card in text_cards:
            if card.is_comment:
                assert comment is None, f"Comment is already set {comment[:70]}"
                comment = card.text
            else:
                assert (
                    not card.is_comment
                ), f"Pair of comment is found, second one is: {comment[:70]}"
                yield card, comment
                comment = None

    return list(_iter())


def parse_section(
    text_cards: Iterable[TextCard], expected_kind: Kind, parser: Callable[[str], Card]
) -> Iterator[Card]:
    text_cards_with_comments = join_comments(text_cards)

    for text_card, comment in text_cards_with_comments:
        assert text_card.kind is expected_kind
        try:
            card = parser(text_card.text)
        except (ValueError, ParseError) as ex:
            raise ValueError(f"Failed to parse card '{text_card}'") from ex
        if comment:
            card.options["comment_above"] = comment
        # card.options['original'] = text_card.text
        yield card


def parse_transformations(text_cards: Iterable[TextCard]) -> list[Transformation]:
    return list(parse_section(text_cards, Kind.TRANSFORMATION, parse_transformation))


def parse_compositions(text_cards: Iterable[TextCard]) -> list[Composition]:
    return list(parse_section(text_cards, Kind.MATERIAL, parse_composition))


def parse_surfaces(text_cards: Iterable[TextCard], transformations: Index) -> list[Surface] | None:
    def parser(text: str):
        return parse_surface(text, transformations=transformations)

    return list(parse_section(text_cards, Kind.SURFACE, parser))


def extract_number(text_card: TextCard):
    return int(text_card.text.split(maxsplit=1)[0])


class MissedCellsError(RuntimeError):
    def __init__(self, missed_cells: list[int]):
        self.missed_cells = missed_cells
        msg = f"Not found cells: {missed_cells}"
        super().__init__(msg)

    @classmethod
    def from_text_cards(cls, missed_cells: Iterable[TextCard]):
        missed_cells_numbers: list[int] = list(map(extract_number, missed_cells))
        return cls(missed_cells_numbers)


def parse_cells(
    text_cards: list[TextCard],
    surfaces: Index,
    compositions: Index,
    transformations: Index,
) -> tuple[list[Body], CellStrictIndex]:
    text_cards_with_comments = join_comments(text_cards)
    size = len(text_cards_with_comments)
    cells_index = CellStrictIndex()
    cells_to_process = list(range(size))
    cells = list(repeat(None, size))

    def parser(text: str):
        return parse_cell(
            text,
            cells=cells_index,
            surfaces=surfaces,
            compositions=compositions,
            transformations=transformations,
        )

    while cells_to_process:
        cells_to_process_length = len(cells_to_process)
        new_cells_to_process = []
        for i in cells_to_process:
            text_card, comment = text_cards_with_comments[i]
            assert text_card.kind is Kind.CELL
            try:
                card: Body = parser(text_card.text)
                assert card is not None, "Failed to process cell %s" % text_card.text[:70]
            except CellNotFoundError:
                new_cells_to_process.append(i)
                continue
            if comment:
                card.options["comment_above"] = comment
            card.options["original"] = text_card.text
            cells[i] = card
            cells_index[card.name()] = card
        if cells_to_process_length == len(new_cells_to_process):
            missed_cells_cards = [text_cards[i] for i in new_cells_to_process]
            raise MissedCellsError.from_text_cards(missed_cells_cards)
        cells_to_process = new_cells_to_process

    if any(c is None for c in cells):
        cells = list(filter(lambda c: c is not None, cells))

    return cells, cells_index
