from __future__ import annotations

from typing import cast

import re

from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path

import numpy as np
import numpy.typing as npt


# noinspection package-requirements
from lark import Lark, TextSlice, Token, Transformer, v_args

from mckit import FMesh

FloatArray = npt.NDArray[np.float64]
Matrix = FloatArray
Cube = list[Matrix]

SpatialBin = tuple[tuple[str, str, str], Matrix, Matrix]
SpatialBins = tuple[tuple[str, str, str], Cube, Cube]
EnergyBin = tuple[
    tuple[str, str, str, str],
    Cube,
    Cube,
]
EnergyBins = tuple[
    tuple[str, str, str, str],
    list[Cube],
    list[Cube],
]


@dataclass
class TallyParseResult:
    name: int
    comment: str
    particle: str
    result: FloatArray
    error: FloatArray
    bins: dict[str, FloatArray]
    geom: str | None = None
    axis: FloatArray | None = None
    origin: FloatArray | None = None
    vec: FloatArray | None = None


@dataclass
class ParseResult:
    code: str
    version: str
    build: str
    date: str
    title: str
    histories: int
    tallies: list[TallyParseResult] = field(default_factory=list)


_MTL_OFFSET = len(" Mesh Tally Number")


def parse(text: str) -> ParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
        ... of MCNP meshtal file.
    """
    start = 0
    end = text.find(" Mesh Tally Number", start)
    parse_result = parse_header(text[:end])
    while end != -1:
        start = end
        end = text.find(" Mesh Tally Number", start + _MTL_OFFSET)
        parse_result.tallies.append(parse_tally(TextSlice(text, start, None if end == -1 else end)))
        # TODO @dvp: use multithreading
        # TODO @dvp: check if TextSlice works without copying of large amount of texts on multithreading
    return parse_result


line_1_pattern = re.compile(
    r"^(?P<code>\w+)\s+version\s+(?P<version>[.0-9/:]+).*ld=(?P<build>\w+)\s+probid =\s+(?P<probid>[.0-9/: ]+)\s*$"
)


def parse_header(text: str) -> ParseResult:
    """Parses MCNP meshtal file header.

    Parameters
    ----------
    text
    ... of MCNP meshtal file header.
    """
    lines = text.split("\n", maxsplit=3)
    line_1 = lines[0]
    match = line_1_pattern.match(line_1)
    if not match:
        msg = f"Unexpected meshtal header: {line_1}"
        raise ValueError(msg)
    code = match["code"]
    version = match["version"]
    build = match["build"]
    date = match["probid"]
    title = lines[1].strip()
    nps_str = lines[2].split("=")[1].strip().removesuffix(".00")
    nps = int(nps_str)
    return ParseResult(
        code=code, version=version, build=build, date=date, title=title, histories=nps
    )


def _block_text(block: Token | str) -> str:
    value = block.value if isinstance(block, Token) else block
    if isinstance(value, TextSlice):
        return value.text[value.start : value.end]
    return str(value)


def _floats_from_block(block: Token | str) -> FloatArray:
    """Convert a whitespace separated numeric block into a 2D numpy array.

    The grammar captures complete matrices as a single token.  All numbers in
    the block are converted at once by numpy, which is much faster than
    creating a Lark token (and a Python ``float``) per value.
    For columnar data representation we parse only the last two columns.

    Note
    ----
    This is not suitable for mesh format with volumes and volumes*result columns.
    But we rarely use this format, let's handle this when we need it.
    """
    text = _block_text(block)
    lines = text.splitlines()
    nrows = len(lines)
    if nrows <= 1:
        msg = "Empty matrix is found"
        raise ValueError(msg)
    width = 2
    count = nrows * width
    values = np.fromiter(
        chain.from_iterable(line.rsplit(None, 2)[-2:] for line in lines),
        dtype=np.float64,
        count=count,
    )
    return values.reshape(nrows, width)


def _spatial_bin_floats_from_block(block: Token | str) -> FloatArray:
    """Convert a spatial-bin numeric block into a 2D numpy array.

    The block has an extra header row (column captions) and each data row has
    an extra leading column (row caption). Drop them.
    """
    text = _block_text(block)
    # splitlines avoids extra allocations; we drop first line
    lines = text.splitlines()
    if len(lines) <= 1:
        msg = "Empty matrix is found"
        raise ValueError(msg)
    data_lines = lines[1:]
    nrows = len(data_lines)
    width = len(data_lines[-1].split()) - 1
    count = nrows * width
    values = np.fromiter(
        chain.from_iterable(line.split()[1:] for line in data_lines),
        dtype=np.float64,
        count=count,
    )
    return values.reshape(nrows, width)


# noinspection method-may-be-static
@v_args(inline=True)
class TallyTransformer(Transformer):
    int = int
    float = float

    def tally(self, tally_header, boundaries, data) -> TallyParseResult:
        name, comment, particle = tally_header
        if "ORIGIN" in boundaries:
            geom = "CYL"
            origin = boundaries.pop("ORIGIN")
            assert "AXIS" in boundaries
            axis = boundaries.pop("AXIS")
            vec = boundaries.pop("VEC", None)
            od = BIN_CYL_ORDER
        else:
            geom = "XYZ"
            origin = None
            axis = None
            vec = None
            od = BIN_REC_ORDER
        bins = dict(boundaries.items())
        if "result" in data:
            # block data presentation (with spatial bins)
            src_perm = [od[let] for let in data["order"]]
            result = np.moveaxis(np.array(data["result"], dtype=np.float64), (0, 1, 2, 3), src_perm)
            error = np.moveaxis(np.array(data["error"], dtype=np.float64), (0, 1, 2, 3), src_perm)
        else:
            # columnar data presentation
            data = np.asarray(data["data"], dtype=np.float64)
            shape = [0, 0, 0, 0]
            for k in boundaries:
                v = od[k]
                shape[v] = boundaries[k].size
                if k != "TIME":
                    shape[v] -= 1
            result = data[:, -2].reshape(shape)
            error = data[:, -1].reshape(shape)
        return TallyParseResult(
            name=name,
            comment=comment,
            particle=particle,
            geom=geom,
            axis=axis,
            origin=origin,
            vec=vec,
            result=result,
            error=error,
            bins=bins,
        )

    def tally_header(
        self, name: int, comment: str | None, particle: str
    ) -> tuple[int, str | None, str]:
        return name, comment, particle

    def title(self, _title: Token) -> str:
        return _title.value.strip()

    def particle(self, kind: Token) -> str:
        return kind.value.upper()

    def boundaries(self, cylinder, bins):
        boundaries = bins
        if cylinder is not None:
            origin, axis, vec = cylinder
            boundaries["ORIGIN"] = origin
            boundaries["AXIS"] = axis
            if vec is not None:
                boundaries["VEC"] = vec
        for k, v in boundaries.items():
            boundaries[k] = np.array(v)
        return boundaries

    def cylinder(
        self,
        origin: FloatArray,
        axis: FloatArray,
        vec: FloatArray | None,
    ) -> tuple[FloatArray, FloatArray, FloatArray | None]:
        return origin, axis, vec

    def vector(self, *floats: float) -> FloatArray:
        return np.array(floats, dtype=np.float64)

    def bins(
        self,
        ibins: tuple[str, FloatArray],
        jbins: tuple[str, FloatArray],
        kbins: tuple[str, FloatArray],
        ebins: tuple[str, FloatArray],
    ) -> dict[str, FloatArray]:
        return dict((ibins, jbins, kbins, ebins))

    def direction_theta(self, vector):
        return "THETA", vector

    def xyzr(self, dir_spec: Token) -> str:
        return dir_spec.value

    def direction_xyzr(self, xyzr: str, vector: FloatArray) -> tuple[str, FloatArray]:
        return xyzr, vector

    def dir_spec(self, spec: Token) -> str:
        if spec.startswith("Th"):
            return "THETA"
        return spec.value

    def energies_e(self, vector):
        return "ENERGY", vector

    def energies_t(self, vector):
        return "TIME", vector

    def data(self, d):
        return d

    def matrix_data(self, energy_bins: EnergyBins, _total_energy_bin: EnergyBins | None):
        order, result, error = energy_bins
        return {"result": result, "error": error, "order": order}

    def energy_bins(self, *energy_bin: EnergyBin) -> EnergyBins:
        result = []
        error = []
        order = energy_bin[0][0]
        for o, r, e in energy_bin:
            assert o == order
            result.append(r)
            error.append(e)
        return order, result, error

    def time(self, _time_spec: Token) -> str:
        return "TIME"

    def energy_bin_e(self, _from: float, _to: float, spatial_bins: SpatialBins) -> EnergyBin:
        i, j, k = spatial_bins[0]
        order = ("ENERGY", i, j, k)
        return order, spatial_bins[1], spatial_bins[2]

    def energy_bin_t(self, _time: float, spatial_bins: SpatialBins) -> EnergyBin:
        i, j, k = spatial_bins[0]
        order = ("TIME", i, j, k)
        return order, spatial_bins[1], spatial_bins[2]

    def spatial_bins(self, *spatial_bin: SpatialBin) -> SpatialBins:
        result = []
        error = []
        order = spatial_bin[0][0]
        for o, r, e in spatial_bin:
            assert o == order
            result.append(r)
            error.append(e)
        return order, result, error

    def spatial_bin(
        self,
        dir_spec1: str,
        _from: float,
        _to: float,
        dir_spec2: str,
        dir_spec3: str,
        values: FloatArray,
        relerrs: FloatArray,
    ) -> SpatialBin:
        order = (dir_spec1, dir_spec3, dir_spec2)  # order 1, 3, 2 is intended
        return order, values, relerrs

    def total_energy_bin(self, spatial_bins: SpatialBins) -> EnergyBin:
        i, j, k = spatial_bins[0]
        order = ("TOTAL", i, j, k)
        return order, spatial_bins[1], spatial_bins[2]

    def matrix(self, block: Token) -> FloatArray:
        return _floats_from_block(block)

    def spatial_bin_matrix(self, block: Token) -> FloatArray:
        return _spatial_bin_floats_from_block(block)

    def total_matrix(self, block: Token) -> FloatArray:
        text = _block_text(block).replace("Total", "")
        block = text
        return _floats_from_block(block)

    def column_data(self, column_header, matrix, total_matrix):
        """column_data : column_header matrix total_matrix
        | column_header matrix
        """
        res = column_header
        res["data"] = matrix
        if total_matrix is not None:
            res["total"] = total_matrix
        return res

    def column_header(self, has_energy, ispec, jspec, kspec):
        """column_header : ENERGY dir_spec dir_spec dir_spec RESULT ERROR newline
        | dir_spec dir_spec dir_spec RESULT ERROR newline
        """
        if has_energy:
            return {"header": ["ENERGY", ispec, jspec, kspec, "RESULT", "ERROR"]}
        return {"header": [ispec, jspec, kspec, "RESULT", "ERROR"]}


BIN_REC_ORDER = {"ENERGY": 0, "X": 1, "Y": 2, "Z": 3, "TIME": 0}
BIN_CYL_ORDER = {"ENERGY": 0, "R": 1, "Z": 2, "THETA": 3, "TIME": 0}

meshtal_tally_parser = Lark.open_from_package(
    "mckit.parser",
    "meshtal-tally.lark",
    parser="lalr",
    search_paths=("grammars",),
    # regex=True,
    transformer=TallyTransformer(),
    # for performance
    propagate_positions=False,
    keep_all_tokens=False,
)


def parse_tally(text: TextSlice) -> TallyParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
    ... of a tally from an MCNP meshtal file.
    """
    return cast(TallyParseResult, cast(object, meshtal_tally_parser.parse(text)))


_BIN_NAMES = {
    "ENERGY": "ebins",
    "X": "xbins",
    "Y": "ybins",
    "Z": "zbins",
    "R": "rbins",
    "THETA": "tbins",
    "TIME": "dtbins",
}


def read_meshtal(
    filename: str | Path, tally: int | set[int] | list[int] | tuple[int, ...] | None = None
) -> dict[int, FMesh]:
    """Reads MCNP meshtal file.

    Parameters
    ----------
    filename
        Meshtal file name.
    tally
        Predicate to select mesh tallies by number. If ``None``, all tallies
        are loaded. If an integer or a collection of integers is passed, only
        tallies with numbers matching the selection are loaded.

    Returns
    -------
    dict
        tallies Index of mesh tallies contained in the file.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    with filename.open() as f:
        text = f.read()

    if tally is None:
        selected = None
        filtering = False
    elif isinstance(tally, int):
        selected = {tally}
        filtering = True
    else:
        selected = set(tally)
        filtering = True

    if filtering and selected is not None and len(selected) == 0:
        return {}

    start = 0
    end = text.find(" Mesh Tally Number", start)
    parse_result = parse_header(text[:end])
    histories = parse_result.histories
    tallies: dict[int, FMesh] = {}
    while end != -1:
        start = end
        end = text.find(" Mesh Tally Number", start + _MTL_OFFSET)
        segment = TextSlice(text, start, None if end == -1 else end)
        if filtering and selected is not None:
            # Extract tally number - it's the last number/token on the first line of segment
            first_nl = segment.text.find("\n", segment.start)
            if first_nl == -1 or first_nl > segment.end:
                first_nl = segment.end
            first_line = segment.text[segment.start : first_nl]
            tally_num = int(first_line.rsplit(None, 1)[-1])
            if tally_num not in selected:
                continue
        t = parse_tally(segment)
        data = t.result
        error = t.error
        kwdata = {}
        for k, v in t.bins.items():
            kwdata[_BIN_NAMES[k]] = v
        tallies[t.name] = FMesh(
            t.name,
            t.particle,
            data,
            error,
            histories=histories,
            transform=None,
            modifier=None,
            comment=t.comment,
            origin=t.origin,
            axis=t.axis,
            vec=t.vec,
            **kwdata,
        )
    return tallies
