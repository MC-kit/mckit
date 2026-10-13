from __future__ import annotations

from typing import Final

import logging

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import numpy as np
import numpy.typing as npt

from lark import Lark, Token, Transformer, UnexpectedInput, UnexpectedToken, v_args, TextSlice

from mckit import FMesh


# @v_args(inline=True)
# class MeshtalTransformer(Transformer):
#     int = int
#     float = float
#
#     def meshtal(self, header, title, histories, tallies):
#         return {
#             "date": header["PROBID"],
#             "title": title,
#             "histories": histories,
#             "tallies": tallies,
#         }
#
#     def header(self, version, build_date, date, time):
#         return {
#             "PROBID": date.value + time.value,
#             "VERSION": version,
#             "BUILD_DATE": build_date
#         }
#
#     def title(self, _title: str):
#         return _title.strip()
#
#     def nps(self, _float):
#         return _float
#
#     def tallies(self, p):
#         return p
#
#     def tally(self, tally_header, boundaries, data):
#         rich.print(tally_header)
#         tally = tally_header
#         if "ORIGIN" in boundaries:
#             tally["origin"] = boundaries.pop("ORIGIN")
#             tally["geom"] = "CYL"
#             assert "AXIS" in boundaries
#             tally["axis"] = boundaries.pop("AXIS")
#         else:
#             tally["geom"] = "XYZ"
#         tally["bins"] = {k: np.array(v) for k, v in boundaries.items()}
#         od = BIN_CYL_ORDER if "origin" in tally else BIN_REC_ORDER
#         if "result" in data:
#             src_perm = [od[let] for let in data["order"]]
#             tally["result"] = np.moveaxis(np.array(data["result"]), (0, 1, 2, 3), src_perm)
#             tally["error"] = np.moveaxis(np.array(data["error"]), (0, 1, 2, 3), src_perm)
#         else:
#             header = data["header"]
#             data = np.array(data["data"])
#             shape = [0, 0, 0, 0]
#             for k in tally["bins"]:
#                 v = od[k]
#                 shape[v] = boundaries[k].size
#                 if k != "TIME":
#                     shape[v] -= 1
#             if "ENERGY" in boundaries:
#                 boundaries["ENERGY"] = 0.5 * (boundaries["ENERGY"][1:] + boundaries["ENERGY"][:-1])
#             result = np.empty(shape)
#             error = np.empty(shape)
#             indices = np.empty((data.shape[0], 4), dtype=int)
#             for k in boundaries:
#                 if k in header:
#                     indices[:, od[k]] = np.searchsorted(boundaries[k], data[:, header.index(k)]) - 1
#                 else:
#                     indices[:, od[k]] = np.zeros(data.shape[0])
#             res_ind = header.index("RESULT")
#             err_ind = header.index("ERROR")
#             for i in range(indices.shape[0]):
#                 result[tuple(indices[i, :])] = data[i, res_ind]
#                 error[tuple(indices[i, :])] = data[i, err_ind]
#             tally["result"] = result
#             tally["error"] = error
#         return tally
#
#     def tally_header(self, name: int, from_other_lines: dict[str, Any]) -> dict[str, str|int]:
#         rich.print("tall_header:", name, from_other_lines)
#         from_other_lines["name"] = name
#         return from_other_lines
#
#     def tally_header_more_wo_comment(self, particle: str) -> dict[str, str]:
#         return {"particle": particle}
#
#     def particle(self, kind):
#         return kind.value.upper()  # to reproduce old PLY parser
#
#     def tally_header_more_with_comment(self, comment, particle):
#         return {"comment": comment, "particle": particle}
#
#     def boundaries(self, cylinder, bins):
#         boundaries = bins
#         if cylinder is not None:
#             origin, axis = cylinder
#             boundaries["ORIGIN"] = origin
#             boundaries["AXIS"] = axis
#         for k, v in boundaries.items():
#             boundaries[k] = np.array(v)
#         return boundaries
#
#     def cylinder(self, origin, axis):
#         return origin, axis
#
#     def vector(self, *floats: float):
#         return np.array(floats)
#
#     def bins(self, ibins, jbins, kbins, ebins):
#         return {name: data for name, data in (ibins, jbins, kbins, ebins)}
#
#     def direction_theta(self, vector):
#         return "THETA", vector
#
#     def direction_xyzr(self, dir_spec: str, vector):
#         return dir_spec, vector
#
#     def dir_spec(self, spec: Token) -> str:
#         if spec.startswith("Th"):
#             return "THETA"
#         return spec.value
#
#     def energies_e(self, vector):
#         return "ENERGY", vector
#
#     def energies_t(self, vector):
#         return "TIME", vector
#
#     def data(self, d):
#         return d
#
#     def matrix_data(energy_bins, total_energy_bin):
#         order, result, error = energy_bins
#         return {"result": result, "error": error, "order": order}
#
#     def energy_bins_first(self, energy_bin):
#         order, result, error = energy_bin
#         return order, [result], [error]
#
#     def energy_bins_continued(self, energy_bins, energy_bin):
#         order, result, error = energy_bin
#         assert order == energy_bins[0]
#         result_list = energy_bins[1]
#         error_list = energy_bins[2]
#         result_list.append(result)
#         error_list.append(error)
#         return order, result_list, error_list
#
#     def spatial_bins_first(self, spatial_bin):
#         """spatial_bins : spatial_bins spatial_bin separator
#         | spatial_bin separator
#         """
#         order, result, error = spatial_bin
#         return order, [result], [error]
#
#     def spatial_bins_continued(self, spatial_bins, spatial_bin):
#         order, result, error = spatial_bin
#         result_list = spatial_bins[1]
#         error_list = spatial_bins[2]
#         result_list.append(result)
#         error_list.append(error)
#         return order, result_list, error_list
#
#     def spatial_bin(self, dir_spec1, _from, _to, dir_spec2, dir_spec3, values, relerrs):
#         """spatial_bin : dir_spec ':' float '-' float newline separator TALLY RESULT ':' dir_spec dir_spec newline matrix separator ERROR newline matrix separator"""
#         order = (dir_spec1, dir_spec3, dir_spec2)   # order 1, 3, 2 is intended
#         results = [line[1:] for line in values[1:]]
#         errors = [line[1:] for line in relerrs[1:]]
#         return order, results, errors
#
#
#     def total_energy_bin(spatial_bins):
#         """total_energy_bin : TOTAL ENERGY newline separator spatial_bins separator"""
#         order = ("TOTAL",  *spatial_bins[0])
#         p[0] = order, spatial_bins[1], spatial_bins[2]
#
#     def matrix(self, *vectors):
#         return list(vectors)
#
#     def total_matrix(self, *vectors):
#         return list[vectors]
#
#     def column_data(self, column_header, matrix, total_matrix):
#         """column_data : column_header matrix total_matrix
#         | column_header matrix
#         """
#         res = column_header
#         res["data"] = matrix
#         if total_matrix:
#             res["total"] = total_matrix
#         return res
#
#     def column_header(self, has_energy, ispec, jspec, kspec):
#         """column_header : ENERGY dir_spec dir_spec dir_spec RESULT ERROR newline
#         | dir_spec dir_spec dir_spec RESULT ERROR newline
#         """
#         if has_energy:
#             return {"header": ["ENERGY", ispec, jspec, kspec,  "RESULT", "ERROR"]}
#         return {"header": [ispec, jspec, kspec,  "RESULT", "ERROR"]}
#
# BIN_REC_ORDER = {"ENERGY": 0, "X": 1, "Y": 2, "Z": 3, "TIME": 0}
# BIN_CYL_ORDER = {"ENERGY": 0, "R": 1, "Z": 2, "THETA": 3, "TIME": 0}


@dataclass
class TallyParseResult:
    name: int
    comment: str
    result: npt.NDArray[np.float64]
    error: npt.NDArray[np.float64]
    bins: dict[str, npt.NDArray[np.float64]]
    geom: str | None = None
    axis: npt.NDArray[np.float64] | None = None
    origin: npt.NDArray[np.float64] | None = None

@dataclass
class ParseResult:
    code: str
    build: str
    date: str
    title: str
    histories: int
    tallies: list[TallyParseResult]


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
    while  end != -1:
        start = end + len(" Mesh Tally Number")
        end = text.find(" Mesh Tally Number", start);
        parse_result.tallies.append(parse_tally(TextSlice(text, start, end)))  #TODO @dvp: use multithreading

def parse_header(text: TextSlice | str) -> ParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
    ... of MCNP meshtal file header.
    """
    return ParseResult()

def parse_tally(text: TextSlice) -> TallyParseResult:
    """Parses MCNP meshtal file.

    Parameters
    ----------
    text
    ... of a tally from an MCNP meshtal file.
    """
    return TallyParseResult()


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
            #TODO @dvp: vec is not provided by MCNP5 (check for MCNP6 difference)
        for k, v in t.bins.items():
            kwdata[_BIN_NAMES[k]] = v
        tallies[name] = FMesh(name, particle, data, error, histories=histories, **kwdata)
    return tallies
