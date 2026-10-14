from __future__ import annotations

from typing import cast

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import numpy.typing as npt

from lark import Lark, TextSlice, Token, Transformer, v_args

from mckit import FMesh


@dataclass
class TallyParseResult:
    name: int
    comment: str
    particle: str
    result: npt.NDArray[np.float64]
    error: npt.NDArray[np.float64]
    bins: dict[str, npt.NDArray[np.float64]]
    geom: str | None = None
    axis: npt.NDArray[np.float64] | None = None
    origin: npt.NDArray[np.float64] | None = None
    vec: npt.NDArray[np.float64] | None = None


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
    while end != -1:
        start = end + len(" Mesh Tally Number")
        end = text.find(" Mesh Tally Number", start)
        parse_result.tallies.append(
            parse_tally(TextSlice(text, start, end))
        )  # TODO @dvp: use multithreading
    return parse_result


@v_args(inline=True)
class MeshtalHeaderTransformer(Transformer):
    int = int

    def start(self, header: tuple[str, str, str, str], title: str, nps: int) -> ParseResult:
        return ParseResult(*header, title=title, histories=nps)

    def header(
        self, code: str, version: str, build_date: str, date: str, time: str
    ) -> tuple[str, str, str, str]:
        return code, version, build_date, date + " " + time

    def title(self, _title: str):
        return _title.strip()

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
        else:
            geom = "XYZ"
            origin = None
            axis = None
            vec = None
        bins = {k: np.array(v) for k, v in boundaries.items()}
        od = BIN_CYL_ORDER if origin else BIN_REC_ORDER
        if "result" in data:
            src_perm = [od[let] for let in data["order"]]
            result = np.moveaxis(np.array(data["result"]), (0, 1, 2, 3), src_perm)
            error = np.moveaxis(np.array(data["error"]), (0, 1, 2, 3), src_perm)
        else:
            header = data["header"]
            data = np.array(data["data"])
            shape = [0, 0, 0, 0]
            for k in bins:
                v = od[k]
                shape[v] = boundaries[k].size
                if k != "TIME":
                    shape[v] -= 1
            if "ENERGY" in boundaries:
                boundaries["ENERGY"] = 0.5 * (boundaries["ENERGY"][1:] + boundaries["ENERGY"][:-1])
            result = np.empty(shape)
            error = np.empty(shape)
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
            # tally["result"] = result
            # tally["error"] = error
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

    def particle(self, kind: str) -> str:
        return kind.upper()  # to reproduce old PLY parser

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
        origin: npt.NDArray[np.float64],
        axis: npt.NDArray[np.float64],
        vec: npt.NDArray[np.float64] | None,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64] | None]:
        return origin, axis, vec

    def vector(self, *floats: float) -> npt.NDArray[np.float64]:
        return np.array(floats, dtype=np.float64)

    def bins(
        self,
        ibins: tuple[str, npt.NDArray[np.float64]],
        jbins: tuple[str, npt.NDArray[np.float64]],
        kbins: tuple[str, npt.NDArray[np.float64]],
        ebins: tuple[str, npt.NDArray[np.float64]],
    ) -> dict[str, npt.NDArray[np.float64]]:
        return dict((ibins, jbins, kbins, ebins))

    def direction_theta(self, vector):
        return "THETA", vector

    def xyzr(self, dir_spec: Token) -> str:
        return dir_spec.value

    def direction_xyzr(
        self, xyzr: str, vector: npt.NDArray[np.float64]
    ) -> tuple[str, npt.NDArray[np.float64]]:
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

    def matrix_data(energy_bins, total_energy_bin):
        order, result, error = energy_bins
        return {"result": result, "error": error, "order": order}

    def energy_bins_first(self, energy_bin):
        order, result, error = energy_bin
        return order, [result], [error]

    def energy_bins_continued(self, energy_bins, energy_bin):
        order, result, error = energy_bin
        assert order == energy_bins[0]
        result_list = energy_bins[1]
        error_list = energy_bins[2]
        result_list.append(result)
        error_list.append(error)
        return order, result_list, error_list

    def spatial_bins_first(self, spatial_bin):
        """spatial_bins : spatial_bins spatial_bin separator
        | spatial_bin separator
        """
        order, result, error = spatial_bin
        return order, [result], [error]

    def spatial_bins_continued(self, spatial_bins, spatial_bin):
        order, result, error = spatial_bin
        result_list = spatial_bins[1]
        error_list = spatial_bins[2]
        result_list.append(result)
        error_list.append(error)
        return order, result_list, error_list

    def spatial_bin(self, dir_spec1, _from, _to, dir_spec2, dir_spec3, values, relerrs):
        """spatial_bin : dir_spec ':' float '-' float newline separator TALLY RESULT ':' dir_spec dir_spec newline matrix separator ERROR newline matrix separator"""
        order = (dir_spec1, dir_spec3, dir_spec2)  # order 1, 3, 2 is intended
        results = [line[1:] for line in values[1:]]
        errors = [line[1:] for line in relerrs[1:]]
        return order, results, errors

    def total_energy_bin(self, spatial_bins):
        """total_energy_bin : TOTAL ENERGY newline separator spatial_bins separator"""
        order = ("TOTAL", *spatial_bins[0])
        return order, spatial_bins[1], spatial_bins[2]

    def matrix(self, *vectors: npt.NDArray[np.float64]) -> list[npt.NDArray[np.float64]]:
        return list(vectors)

    def total_matrix(self, *vectors: npt.NDArray[np.float64]) -> list[npt.NDArray[np.float64]]:
        return list(vectors)

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
    # parser="earley",
    search_paths=("grammars",),
    regex=True,
)


def parse_tally(text: TextSlice) -> TallyParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
    ... of a tally from an MCNP meshtal file.
    """
    # tokens = [(t.type, t.value) for t in meshtal_tally_parser.lex(text)]
    tree = meshtal_tally_parser.parse(text)
    return TallyTransformer().transform(tree)


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
        name = t.name
        particle = t.particle
        data = t.result
        error = t.error
        kwdata = {}
        if t.geom == "CYL":
            kwdata["origin"] = t.origin
            kwdata["axis"] = t.axis
            # TODO @dvp: vec is not provided by MCNP5 (check for MCNP6 difference)
        for k, v in t.bins.items():
            kwdata[_BIN_NAMES[k]] = v
        tallies[name] = FMesh(name, particle, data, error, histories=histories, **kwdata)
    return tallies
