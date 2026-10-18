from __future__ import annotations

from typing import cast

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import numpy.typing as npt


# noinspection package-requirements
from lark import Lark, TextSlice, Token, Transformer, v_args

from mckit import FMesh

FloatArray = npt.NDArray[np.float64]
Matrix = list[FloatArray]
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


def parse(text: str) -> ParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
        ... of MCNP meshtal file.
    """
    start = 0
    end = text.find(" Mesh Tally Number", start)
    parse_result = parse_header(TextSlice(text, start, end))
    offset = len(" Mesh Tally Number")
    while end != -1:
        start = end
        end = text.find(" Mesh Tally Number", start + offset)
        parse_result.tallies.append(parse_tally(TextSlice(text, start, end)))
        # TODO @dvp: use multithreading
        # TODO @dvp: check if TextSlice works without copying of large amount of texts on multithreading
    return parse_result


# noinspection method-may-be-static
@v_args(inline=True)
class MeshtalHeaderTransformer(Transformer):
    int = int

    def start(self, header: tuple[str, str, str, str], title: str, nps: int) -> ParseResult:
        return ParseResult(*header, title=title, histories=nps)

    def header(
        self, code: Token, version: Token, build_date: Token, date: Token, time: Token
    ) -> tuple[str, str, str, str]:
        return code.value, version.value, build_date.value, date.value + " " + time.value

    def title(self, _title: Token):
        return _title.value.strip()

    # def nps(self, _int):
    #     return _int


meshtal_header_parser = Lark.open_from_package(
    "mckit.parser",
    "meshtal-header.lark",
    parser="lalr",
    search_paths=("grammars",),
    regex=True,
    transformer=MeshtalHeaderTransformer(),
)


def parse_header(text: TextSlice | str) -> ParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
    ... of MCNP meshtal file header.
    """
    return cast(ParseResult, cast(object, meshtal_header_parser.parse(TextSlice.cast_from(text))))


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
            src_perm = [od[let] for let in data["order"]]
            result = np.moveaxis(np.array(data["result"], dtype=np.float64), (0, 1, 2, 3), src_perm)
            error = np.moveaxis(np.array(data["error"], dtype=np.float64), (0, 1, 2, 3), src_perm)
        else:
            header = data["header"]
            data = np.array(data["data"], dtype=np.float64)
            shape = [0, 0, 0, 0]
            for k in boundaries:
                v = od[k]
                shape[v] = boundaries[k].size
                if k != "TIME":
                    shape[v] -= 1
            if "ENERGY" in boundaries:
                boundaries["ENERGY"] = 0.5 * (boundaries["ENERGY"][1:] + boundaries["ENERGY"][:-1])
            result = np.empty(shape, dtype=np.float64)
            error = np.empty(shape, dtype=np.float64)
            indices = np.empty((data.shape[0], 4), dtype=int)
            for k in boundaries:
                if k in header:
                    indices[:, od[k]] = np.searchsorted(boundaries[k], data[:, header.index(k)]) - 1
                else:
                    indices[:, od[k]] = np.zeros(data.shape[0])
            res_ind = header.index("RESULT")
            err_ind = header.index("ERROR")
            for i in range(indices.shape[0]):
                result[tuple(indices[i, :])] = data[i, res_ind]
                error[tuple(indices[i, :])] = data[i, err_ind]
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
        values: Matrix,
        relerrs: Matrix,
    ) -> SpatialBin:
        order = (dir_spec1, dir_spec3, dir_spec2)  # order 1, 3, 2 is intended
        results = [line[1:] for line in values[1:]]
        errors = [line[1:] for line in relerrs[1:]]
        return order, results, errors

    def total_energy_bin(self, spatial_bins: SpatialBins) -> EnergyBin:
        i, j, k = spatial_bins[0]
        order = ("TOTAL", i, j, k)
        return order, spatial_bins[1], spatial_bins[2]

    def matrix(self, *vectors: FloatArray) -> Matrix:
        return [*vectors]

    def total_matrix(self, *vectors: FloatArray) -> Matrix:
        return [*vectors]

    def column_data(self, column_header, matrix, total_matrix):
        """column_data : column_header matrix total_matrix
        | column_header matrix
        """
        res = column_header
        res["data"] = matrix
        if total_matrix:
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


def read_meshtal(filename: str | Path) -> dict[int, FMesh]:
    """Reads MCNP meshtal file.

    Parameters
    ----------
    filename
        Meshtal file name.

    Returns
    -------
    dict
        tallies Index of mesh tallies contained in the file.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    with filename.open() as f:
        text = f.read()
    meshtal_data = parse(text)
    histories = meshtal_data.histories
    tallies = {}
    for t in meshtal_data.tallies:
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
