from __future__ import annotations

from typing import Final

import logging

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import numpy as np

from lark import Lark, Token, Transformer, UnexpectedInput, UnexpectedToken, v_args

DEBUG_PARSER: Final[bool] = True

if DEBUG_PARSER:
    logger = logging.getLogger("lark")
    for _hdlr in logger.handlers:
        logger.removeHandler(_hdlr)
    logger.disabled = False
    logger.setLevel(logging.DEBUG)

    logging.getLogger("parso").setLevel(logging.INFO)

    logger = logging.getLogger("mckit.parser.meshtal_lark_parser")
    logger.disabled = False
    logger.setLevel(logging.DEBUG)

    logger.info("Started meshtal lark parser" + "-"*40 )

def token2string(token: Token | None) -> str:
    if token is None:
        return "None"
    return f"[{token.type}] '{token.value}'"


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
