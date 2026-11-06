from __future__ import annotations

from typing import Any

import re

# noinspection PyPackageRequirements
from lark import Lark, Token, Transformer, v_args
from lark.exceptions import LarkError

import mckit.parser.common.utils as cmn

from mckit.body import Body, Shape
from mckit.material import Material
from mckit.parser.common import (
    CellStrictIndex,
    CompositionStrictIndex,
    SurfaceStrictIndex,
    TransformationStrictIndex,
)
from mckit.transformation import Transformation
from mckit.utils import filter_dict
from mckit.utils.indexes import Index

CELL_WORDS = {"U", "MAT", "LAT", "TMP", "RHO", "VOL", "PMT", "FCL"}


def intern_cell_word(word: str):
    word = cmn.ensure_upper(word)
    word, res = cmn.internalize(word, CELL_WORDS)
    if not res:
        raise cmn.ParseError(f"'{word}' is not a valid word for cell specification")
    return word


# noinspection bad-argument-type
def parse(
    text: str,
    cells: Index | None = None,
    surfaces: Index | None = None,
    transformations: Index | None = None,
    compositions: Index | None = None,
) -> Body:
    """Parse an MCNP cell specification.

    Parameters
    ----------
    text
        Cell specification.
    cells
        Should be one of CellStrictIndex, CellDummyIndex, IgnoringIndex.
        It is used to treat cell complements, like body.
    surfaces
        Should be one of SurfaceStrictIndex, SurfaceDummyIndex, IgnoringIndex.
    transformations
        Should be one of TransformationStrictIndex, TransformationDummyIndex, IgnoringIndex.
    compositions
        Should be one of CompositionStrictIndex, CompositionDummyIndex, IgnoringIndex.

    Returns
    -------
    Body: representation of an MCNP cell.

    Raises
    ------
    ValueError: on invalid cell specification.
    """
    cells, surfaces, transformations, compositions = (
        x[1]() if x[0] is None else x[0]
        for x in zip(
            [cells, surfaces, transformations, compositions],
            [
                CellStrictIndex,
                SurfaceStrictIndex,
                TransformationStrictIndex,
                CompositionStrictIndex,
            ],
            strict=False,
        )
    )
    original = text
    text = cmn.drop_c_comments(text)
    text, _comments, trailing_comments = cmn.extract_comments(text)
    name, pos = _extract_name(text)
    if like_match := _LIKE_HEADER_PATTERN.match(text, pos):
        # noinspection unresolved-references
        reference_body = cells[int(like_match.group("reference"))]
        options = filter_dict(reference_body.options, "original", "comment", "comment_above")
        options.update(_collect_attributes(text, like_match.end(), transformations))
        options["name"] = name
        geometry: list[Any] | Body = reference_body
    else:
        material_options, pos = _extract_material(text, pos, compositions)
        geometry, pos = _extract_geometry(text, pos, surfaces, cells)
        options = {**material_options}
        options.update(_collect_attributes(text, pos, transformations))
        options["name"] = name
    if trailing_comments:
        options["comment"] = trailing_comments
    if original:
        options["original"] = original
    return Body(geometry, **options)


def _extract_name(text: str) -> tuple[int, int]:
    match = _CELL_NAME_PATTERN.match(text)
    if match is None:
        raise cmn.ParseError(
            f"Cell specification must start with a cell number, got '{text.strip()}'"
        )
    return int(match.group("name")), match.end()


def _extract_material(text: str, pos: int, compositions: Index) -> tuple[dict[str, Any], int]:
    """Extract material number and density.

    Either the material number is 0 and density is omitted,
    or a composition number is followed with density.
    """
    match = _NUMBER_VALUE_PATTERN.match(text, pos)
    if match is None:
        raise cmn.ParseError(f"Cell specification must define material, got '{text[pos:].strip()}'")
    raw = match.group(1)
    value, is_int = _clean_number(raw)
    if not is_int:
        raise cmn.ParseError(f"Invalid material specification '{raw}'")
    if value == 0.0:
        return {}, match.end()
    composition = compositions[int(value)]
    density_match = _NUMBER_VALUE_PATTERN.match(text, match.end())
    if density_match is None:
        raise cmn.ParseError(f"Composition #{int(value)}: missed density specification")
    density = float(density_match.group(1))
    if density > 0:
        material = Material(composition=composition, concentration=density * 1e24)
    else:
        material = Material(composition=composition, density=-density)
    return {"MAT": material}, density_match.end()


def _extract_geometry(text: str, pos: int, surfaces: Index, cells: Index) -> tuple[list[Any], int]:
    keyword_match = _CELL_KEYWORD_PATTERN.search(text, pos)
    geometry_end = keyword_match.start() if keyword_match else len(text)
    geometry_text = text[pos:geometry_end]
    if not geometry_text.strip():
        raise cmn.ParseError(f"Cell specification must define geometry, got '{text.strip()}'")
    return _parse_geometry(geometry_text, surfaces, cells), geometry_end


def _collect_attributes(text: str, pos: int, transformations: Index) -> dict[str, Any]:
    options: dict[str, Any] = {}
    while True:
        keyword_match = _CELL_KEYWORD_PATTERN.search(text, pos)
        if keyword_match is None:
            junk = text[pos:]
            if junk.strip(): # pragma: no cover
                raise cmn.ParseError(
                    f"Could not parse cell attributes specification: '{junk.strip()}'"
                )
            break
        pos = keyword_match.end()
        next_keyword_match = _CELL_KEYWORD_PATTERN.search(text, pos)
        segment_end = next_keyword_match.start() if next_keyword_match else len(text)
        segment = text[pos:segment_end]
        key = cmn.ensure_upper(keyword_match.group("key"))
        handler = _ATTRIBUTE_HANDLERS[key]
        options.update(
            handler(key, segment, keyword_match.group("star") is not None, transformations)
        )
        pos = segment_end
    return options


# noinspection PyUnusedLocal
def _int_attribute(key: str, segment: str, _star: bool, _transformations: Index) -> dict[str, Any]:
    match = _INT_VALUE_PATTERN.match(segment)
    if match is None:
        raise cmn.ParseError(f"Cell attribute '{key}' should be specified with an integer value")
    return {intern_cell_word(key): int(match.group(1))}


# noinspection PyUnusedLocal
def _float_attribute(
    key: str, segment: str, _star: bool, _transformations: Index
) -> dict[str, Any]:
    match = _NUMBER_VALUE_PATTERN.match(segment)
    if match is None:
        raise cmn.ParseError(f"Cell attribute '{key}' should be specified with a float value")
    return {intern_cell_word(key): float(match.group(1))}


# noinspection PyUnusedLocal
def _fcl_attribute(_key: str, segment: str, _star: bool, _transformations: Index) -> dict[str, Any]:
    #
    #  FCL card: Forced Collision
    #  See MCNP 6.3.1 Theory... 5.12.9, p.566
    #  Example: FCL:N=0.5
    #
    number_matches = list(_NUMBER_PATTERN.finditer(segment))
    if not number_matches:
        raise cmn.ParseError(f"FCL attribute '{segment.strip()}' should specify a float value")
    prefixed = segment[: number_matches[0].start()]
    particles = re.findall(r"[NPE]", prefixed, re.IGNORECASE)
    if len(particles) != 1:
        raise cmn.ParseError(f"FCL attribute '{segment.strip()}' should specify a single particle")
    return {"FCL" + cmn.ensure_upper(particles[0]): float(number_matches[0].group())}


def _imp_attribute(_key: str, segment: str, _star: bool, _transformations: Index) -> dict[str, Any]:
    #
    #  See MCNP, vol.I, p.3-7
    #  Example: IMP:E,P,N 1 1 0.
    #
    number_matches = list(_NUMBER_PATTERN.finditer(segment))
    if not number_matches:
        raise cmn.ParseError(f"IMP attribute '{segment.strip()}' should specify importance values")
    prefixed = segment[: number_matches[0].start()]
    particles = [cmn.ensure_upper(p) for p in re.findall(r"[NPE]", prefixed, re.IGNORECASE)]
    floats = [float(match.group()) for match in number_matches]
    while len(floats) < len(particles):
        floats.append(floats[-1])
    return {"IMP" + p: v for p, v in zip(particles, floats, strict=False)}


def _trcl_attribute(_key: str, segment: str, star: bool, transformations: Index) -> dict[str, Any]:
    params_match = _PARAMS_PARENS_PATTERN.match(segment)
    if params_match is not None:
        transformation = _build_transformation(
            _collect_numbers(params_match.group("params"), 0), star
        )
        return {"TRCL": transformation}
    index_match = _INT_VALUE_PATTERN.match(segment)
    if index_match is None:
        raise cmn.ParseError(f"TRCL attribute '{segment.strip()}' is not valid")
    return {"TRCL": transformations[int(index_match.group(1))]}


def _fill_attribute(_key: str, segment: str, star: bool, transformations: Index) -> dict[str, Any]:
    universe_match = _INT_VALUE_PATTERN.match(segment)
    if universe_match is None:
        raise cmn.ParseError(f"FILL attribute '{segment.strip()}' should specify a universe number")
    universe = int(universe_match.group(1))
    params_match = _PARAMS_PARENS_PATTERN.match(segment, universe_match.end())
    if params_match is not None:
        numbers = _collect_numbers(params_match.group("params"), 0)
        if len(numbers) == 1 and numbers[0][1]:
            # A single plain integer refers to a named transformation.
            transformation = transformations[int(numbers[0][0])]
        else:
            transformation = _build_transformation(numbers, star)
        return {"FILL": {"universe": universe, "transform": transformation}}
    return {"FILL": {"universe": universe}}


def _build_transformation(numbers: list[tuple[float, bool]], in_degrees: bool) -> Transformation:
    translation, rotation, inverted = _collect_transform_params(numbers)
    return Transformation(
        translation=translation,
        rotation=rotation,
        indegrees=in_degrees,
        inverted=inverted,
    )


def _collect_transform_params(
    numbers: list[tuple[float, bool]],
) -> tuple[list[float], list[float] | None, bool]:
    """Extract translation and rotation vectors.

    The first 3 numbers are translation, the rest are rotation,
    optionally followed with an integer M option (only -1 or 1).
    """
    if len(numbers) < 3:
        raise cmn.ParseError("Cell transformation requires a translation vector of 3 numbers")
    translation = [value for value, _is_int in numbers[:3]]
    tail = numbers[3:]
    if not tail:
        return translation, None, False
    if len(tail) not in _ROTATION_LENGTHS | {10}:
        raise cmn.ParseError(f"Invalid number of transformation rotation parameters: {len(tail)}")
    if len(tail) == 10:  # 9 rotation numbers followed with the M option
        value, is_int = tail[-1]
        if not is_int:
            raise cmn.ParseError("The M option should be specified as an integer")
        assert value in {-1.0, 1.0}, f"Invalid value for transformation M parameter {int(value)}"
        return translation, [value for value, _is_int in tail[:-1]], value == -1.0
    return translation, [value for value, _is_int in tail], False


def _collect_numbers(text: str, pos: int) -> list[tuple[float, bool]]:
    """Find numbers in the card part.

    Returns
    -------
        List of pairs: value and flag, whether the number is written as a plain integer.
    """
    matches = _NUMBER_PATTERN.finditer(text, pos=pos)
    return [_clean_number(match.group()) for match in matches]


def _clean_number(raw: str) -> tuple[float, bool]:
    value = float(raw)
    return value, _PURE_INTEGER_PATTERN.match(raw) is not None


# noinspection method-may-be-static
@v_args(inline=True)
class GeometryTransformer(Transformer):
    """Builds reverse Polish notation for a cell geometry specification.

    The elements are Shape objects wrapping surfaces or bodies,
    operations are 'I' for intersection, 'U' for union and 'C' for complement.
    """

    def __init__(self, surfaces: Index, cells: Index):
        super().__init__()
        self._surfaces = surfaces
        self._cells = cells

    def element_num(self, token: Token) -> list[Any]:
        number = int(token)
        opc = "S" if number > 0 else "C"
        return [Shape(opc, self._surfaces[abs(number)])]

    def element_complement_num(self, token: Token) -> list[Any]:
        return [Shape("C", self._cells[int(token)])]

    def element_complement(self, geometry: list[Any]) -> list[Any]:
        return [*geometry, "C"]

    def factor(self, arg: list[Any]) -> list[Any]:
        return arg

    def term(self, *factors: list[Any]) -> list[Any]:
        rpn = [*factors[0]]
        for factor in factors[1:]:
            rpn += factor
            rpn.append("I")
        return rpn

    def expr(self, *terms: list[Any]) -> list[Any]:
        rpn = [*terms[0]]
        for term in terms[1:]:
            rpn += term
            rpn.append("U")
        return rpn

    def start(self, geometry: list[Any]) -> list[Any]:
        return geometry


_GEOMETRY_LARK = Lark.open_from_package(
    "mckit.parser",
    "cell-geometry.lark",
    parser="lalr",
    search_paths=("grammars",),
    # for performance
    propagate_positions=False,
    keep_all_tokens=False,
)


def _parse_geometry(geometry_text: str, surfaces: Index, cells: Index) -> list[Any]:
    try:
        tree = _GEOMETRY_LARK.parse(geometry_text)
    except LarkError as ex:
        raise cmn.ParseError(
            f"Could not parse cell geometry specification '{geometry_text.strip()}'"
        ) from ex
    return GeometryTransformer(surfaces, cells).transform(tree)


_CELL_NAME_PATTERN = re.compile(r"\s*(?P<name>\d+)")

_LIKE_HEADER_PATTERN = re.compile(r"\s*LIKE\b[\s=,]*(?P<reference>\d+)[\s=,]*BUT\b", re.IGNORECASE)

_CELL_KEYWORD_PATTERN = re.compile(
    r"(?P<star>\*)?\s*(?P<key>LIKE|BUT|TRCL|FILL|FCL|IMP|PMT1|PMT2|U|MAT|LAT|PMT|TMP|RHO|VOL)\b",
    re.IGNORECASE,
)

_NUMBER_PATTERN = re.compile(cmn.FLOAT, re.IGNORECASE)

_PURE_INTEGER_PATTERN = re.compile(r"[-+]?\d+$")

_NUMBER_VALUE_PATTERN = re.compile(r"[\s=,]*(" + cmn.FLOAT + r")", re.IGNORECASE)

_INT_VALUE_PATTERN = re.compile(r"[\s=,]*([+-]?\d+)")

_PARAMS_PARENS_PATTERN = re.compile(r"[\s=,]*\((?P<params>[^()]*)\)")

_ROTATION_LENGTHS = frozenset({3, 5, 6, 9})


# noinspection PyUnusedLocal
def _like_misplaced(
    _key: str, _segment: str, _star: bool, _transformations: Index
) -> dict[str, Any]:
    raise cmn.ParseError("Misplaced 'LIKE' keyword: a cell can not have both geometry and LIKE")


# noinspection PyUnusedLocal
def _but_misplaced(
    _key: str, _segment: str, _star: bool, _transformations: Index
) -> dict[str, Any]:
    raise cmn.ParseError("Misplaced 'BUT' keyword: 'BUT' is allowed only after 'LIKE <n> BUT'")


_ATTRIBUTE_HANDLERS = {
    "U": _int_attribute,
    "MAT": _int_attribute,
    "LAT": _int_attribute,
    "PMT": _int_attribute,
    "PMT1": _int_attribute,
    "PMT2": _float_attribute,
    "TMP": _float_attribute,
    "RHO": _float_attribute,
    "VOL": _float_attribute,
    "FCL": _fcl_attribute,
    "IMP": _imp_attribute,
    "TRCL": _trcl_attribute,
    "FILL": _fill_attribute,
    "LIKE": _like_misplaced,
    "BUT": _but_misplaced,
}
