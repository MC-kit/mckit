from __future__ import annotations

import re

from pathlib import Path

import numpy as np

from ply import lex, yacc

from mckit.fmesh import FMesh

literals = ["+", "-", ":", "/"]

KEYWORDS = [
    "MCNP",
    "VERSION",
    "LD",
    "PROBID",
    "NEUTRON",
    "PHOTON",
    "ELECTRON",
    "RESULT",
    "RESULTS",
    "ERROR",
    "ERRORS",
    "CYLINDER",
    "ORIGIN",
    "AXIS",
    "TALLY",
    "MPI",
    "X",
    "Y",
    "Z",
    "R",
    "THETA",
    "ENERGY",
    "TIME",
    "TH",
    "TOTAL",
]

BIN_REC_ORDER = {"ENERGY": 0, "X": 1, "Y": 2, "Z": 3, "TIME": 0}
BIN_CYL_ORDER = {"ENERGY": 0, "R": 1, "Z": 2, "THETA": 3, "TIME": 0}

# List of token names
tokens = [
    "separator",
    "newline",
    "int_number",
    "flt_number",
    "minus",
    "title",
    "stamp",
    "MCNP",
    "VERSION",
    "LD",
    "PROBID",
    "NEUTRON",
    "PHOTON",
    "ELECTRON",
    "RESULT",
    "ERROR",
    "CYLINDER",
    "ORIGIN",
    "AXIS",
    "TALLY",
    "MPI",
    "X",
    "Y",
    "Z",
    "R",
    "THETA",
    "ENERGY",
    "TIME",
    "TOTAL",
]

# precedence = (
#    ('left', 'newline'),
# )

states = (("title", "exclusive"), ("norm", "exclusive"), ("tally", "exclusive"))

BLANK_LINE = r"^\n"
STAMP = r"[\d/:]+"
NEWLINE = r"\n"
FRACTION = r"\."
EXPONENT = r"(E[-+]?\d+)"
INT_NUMBER = r"(\d+)"
MINUS = r"-(?=\d)"
FLT_NUMBER = (
    r"("
    + INT_NUMBER
    + r"?"
    + FRACTION
    + INT_NUMBER
    + EXPONENT
    + r"?|"
    + INT_NUMBER
    + FRACTION
    + r"?"
    + EXPONENT
    + r"|"
    + INT_NUMBER
    + FRACTION
    + r")(?=[ \n-+])"
)
KEYWORD = r"[A-Z]+(/[A-Z]+)?"

SKIP = r"[=,.() ]"

t_ANY_ignore = SKIP


def t_title_title(t):
    r""".+"""
    return t


@lex.TOKEN(MINUS)
def t_norm_tally_minus(t):
    return t


# noinspection PyPep8Naming
@lex.TOKEN(BLANK_LINE)
def t_ANY_separator(t):
    t.lexer.lineno += 1
    t.lexer.last_pos = t.lexer.lexpos
    return t


@lex.TOKEN(NEWLINE)
def t_newline(t):
    t.lexer.lineno += 1
    t.lexer.last_pos = t.lexer.lexpos
    t.lexer.begin("title")
    return t


@lex.TOKEN(NEWLINE)
def t_title_newline(t):
    t.lexer.lineno += 1
    t.lexer.last_pos = t.lexer.lexpos
    t.lexer.begin("norm")
    return t


@lex.TOKEN(NEWLINE)
def t_norm_newline(t):
    t.lexer.lineno += 1
    t.lexer.last_pos = t.lexer.lexpos
    t.lexer.begin("tally")
    return t


@lex.TOKEN(NEWLINE)
def t_tally_newline(t):
    t.lexer.lineno += 1
    t.lexer.last_pos = t.lexer.lexpos
    return t


@lex.TOKEN(STAMP)
def t_stamp(t):
    return t


@lex.TOKEN(KEYWORD)
def t_keyword(t):
    value = t.value.upper()
    if value == "MCNP":
        t.lexer.section_index = 0
        meshtal_lexer.lineno = 1
        t.lineno = 1
        t.lexer.last_pos = 1
    if value in KEYWORDS:
        t.type = value
        t.value = value
        return t
    return None


@lex.TOKEN(KEYWORD)
def t_norm_tally_keyword(t):
    value = t.value.upper()
    if value == "TIMES":
        value = "TIME"
    if value in KEYWORDS:
        if value == "RESULTS":
            value = "RESULT"
        elif value == "ERRORS":
            value = "ERROR"
        elif value == "TH":
            value = "THETA"
        t.type = value
        t.value = value
        return t
    return None


# noinspection PyPep8Naming
def t_ANY_error(t):
    column = t.lexer.lexpos - t.lexer.last_pos + 1
    msg = f"Illegal character {t.value[0]!r} at line {t.lexer.lineno} column {column}"
    raise ValueError(msg, t.value[0], t.lexer.lineno, column)


@lex.TOKEN(FLT_NUMBER)
def t_norm_tally_flt_number(t):
    t.value = float(t.value)
    return t


@lex.TOKEN(INT_NUMBER)
def t_norm_tally_int_number(t):
    t.value = int(t.value)
    return t


meshtal_lexer = lex.lex(reflags=re.MULTILINE + re.IGNORECASE + re.VERBOSE)


def p_meshtal(p):
    """meshtal : header newline title newline float newline separator tallies"""
    p[0] = {
        "date": p[1]["PROBID"],
        "title": p[3].lstrip().rstrip(),
        "histories": p[5],
        "tallies": p[8],
    }


def p_header(p):
    """header : MCNP VERSION stamp LD stamp PROBID stamp stamp
    | MCNP VERSION stamp MPI LD stamp PROBID stamp stamp
    """
    t = len(p)
    p[0] = {"PROBID": p[t - 2] + p[t - 1], "VERSION": p[3]}


# noinspection GrazieInspection
def p_tallies(p):
    """tallies : tallies tally
    | tallies tally separator
    | tally separator
    | tally
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        if isinstance(p[1], list):
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = [p[1]]


def p_tally(p):
    """tally : tally_header separator boundaries separator data"""
    tally = p[1]
    boundaries = p[3]
    tally["geom"] = "XYZ"
    if "ORIGIN" in boundaries.keys():
        tally["origin"] = boundaries.pop("ORIGIN")
        tally["geom"] = "CYL"
    if "AXIS" in boundaries.keys():
        tally["axis"] = boundaries.pop("AXIS")
    tally["bins"] = {k: np.array(v) for k, v in boundaries.items()}
    data = p[5]
    od = BIN_CYL_ORDER if "origin" in tally.keys() else BIN_REC_ORDER
    if "result" in data.keys():
        src_perm = [od[let] for let in data["order"]]
        tally["result"] = np.moveaxis(np.array(data["result"]), (0, 1, 2, 3), src_perm)
        tally["error"] = np.moveaxis(np.array(data["error"]), (0, 1, 2, 3), src_perm)
    else:
        header = data["header"]
        data = np.array(data["data"])
        shape = [0, 0, 0, 0]
        for k in tally["bins"].keys():
            v = od[k]
            shape[v] = boundaries[k].size
            if k != "TIME":
                shape[v] -= 1
        if "ENERGY" in boundaries.keys():
            boundaries["ENERGY"] = 0.5 * (boundaries["ENERGY"][1:] + boundaries["ENERGY"][:-1])
        result = np.empty(shape)
        error = np.empty(shape)
        indices = np.empty((data.shape[0], 4), dtype=int)
        for k in boundaries.keys():
            if k in header:
                indices[:, od[k]] = np.searchsorted(boundaries[k], data[:, header.index(k)]) - 1
            else:
                indices[:, od[k]] = np.zeros(data.shape[0])
        res_ind = header.index("RESULT")
        err_ind = header.index("ERROR")
        for i in range(indices.shape[0]):
            result[tuple(indices[i, :])] = data[i, res_ind]
            error[tuple(indices[i, :])] = data[i, err_ind]
        tally["result"] = result
        tally["error"] = error
    p[0] = tally


# noinspection PyPep8Naming,GrazieInspection
def p_tallY_header(p):
    """tally_header : TALLY integer newline particle TALLY newline
    | TALLY integer newline particle TALLY newline ENERGY newline
    | TALLY integer newline particle TALLY newline TALLY newline
    | TALLY integer newline particle TALLY newline TALLY newline ENERGY newline
    """
    p[0] = {"name": p[2], "particle": p[4]}


def p_particle(p):
    """particle : NEUTRON
    | PHOTON
    | ELECTRON
    """
    p[0] = p[1]


def p_boundaries(p):
    """boundaries : TALLY ':' newline CYLINDER ORIGIN vector AXIS vector newline bins
    | TALLY ':' newline bins
    """
    boundaries = p[len(p) - 1]
    if len(p) == 11:
        boundaries["ORIGIN"] = p[6]
        boundaries["AXIS"] = p[8]
    for k, v in boundaries.items():
        boundaries[k] = np.array(v)
    p[0] = boundaries


def p_bins(p):
    """bins : direction newline direction newline direction newline energies newline"""
    bins = {name: data for name, data in (p[1], p[3], p[5], p[7])}  # noqa: C416
    p[0] = bins


def p_dir_spec(p):
    """dir_spec : X
    | Y
    | Z
    | R
    | THETA
    """
    p[0] = p[1]


def p_direction(p):
    """direction : dir_spec ':' vector"""
    p[0] = p[1], p[3]


def p_energies(p):
    """energies : ENERGY ':' vector
    | TIME ':' vector
    """
    p[0] = p[1], p[3]


def p_float(p):
    """float : '+' flt_number
    | minus flt_number
    | flt_number
    | integer
    """
    if p[1] == "-":
        p[0] = -p[2]
    elif p[1] == "+":
        p[0] = p[2]
    else:
        p[0] = p[1]


def p_integer(p):
    """integer : '+' int_number
    | minus int_number
    | int_number
    """
    if p[1] == "-":
        p[0] = -p[2]
    elif p[1] == "+":
        p[0] = p[2]
    else:
        p[0] = p[1]


def p_vector(p):
    """vector : vector float
    | float
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_matrix(p):
    """matrix : matrix vector newline
    | vector newline
    """
    if len(p) == 3:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_total_matrix(p):
    """total_matrix : total_matrix TOTAL vector newline
    | TOTAL vector newline"""
    if len(p) == 4:
        p[0] = [p[2]]
    else:
        p[1].append(p[4])
        p[0] = p[1]


def p_data(p):
    """data : matrix_data
    | column_data separator
    | column_data
    """
    p[0] = p[1]


def p_column_data(p):
    """column_data : column_header matrix total_matrix
    | column_header matrix
    """
    p[0] = {"header": p[1], "data": p[2]}
    if len(p) == 4:
        p[0]["total"] = p[3]


def p_column_header(p):
    """column_header : ENERGY dir_spec dir_spec dir_spec RESULT ERROR newline
    | dir_spec dir_spec dir_spec RESULT ERROR newline
    """
    n = len(p)
    p[0] = p[1 : n - 1]


def p_matrix_data(p):
    """matrix_data : energy_bins total_energy_bin
    | energy_bins
    """
    order, result, error = p[1]
    p[0] = {"result": result, "error": error, "order": order}


def p_energy_bins(p):
    """energy_bins : energy_bins energy_bin separator
    | energy_bin separator
    """
    if len(p) == 3:
        order, result, error = p[1]
        p[0] = order, [result], [error]
    else:
        order, result, error = p[2]
        p[1][1].append(result)
        p[1][2].append(error)
        p[0] = order, p[1][1], p[1][2]


def p_energy_bin(p):
    """energy_bin : ENERGY ':' float '-' float newline separator spatial_bins
    | TIME ':' float newline separator spatial_bins
    """
    t = len(p) - 1
    order = [p[1]] + p[t][0]
    p[0] = order, p[t][1], p[t][2]


def p_total_energy_bin(p):
    """total_energy_bin : TOTAL ENERGY newline separator spatial_bins separator"""
    order = [p[1]] + p[5][0]
    p[0] = order, p[5][1], p[5][2]


def p_spatial_bins(p):
    """spatial_bins : spatial_bins spatial_bin separator
    | spatial_bin separator
    """
    if len(p) == 3:
        order, result, error = p[1]
        p[0] = order, [result], [error]
    else:
        order, result, error = p[2]
        p[1][1].append(result)
        p[1][2].append(error)
        p[0] = order, p[1][1], p[1][2]


def p_spatial_bin(p):
    """spatial_bin : dir_spec ':' float '-' float newline separator TALLY RESULT ':' dir_spec dir_spec newline matrix separator ERROR newline matrix separator"""
    order = [p[1], p[12], p[11]]
    results = [line[1:] for line in p[14][1:]]
    errors = [line[1:] for line in p[18][1:]]
    p[0] = order, results, errors


def p_error(p):
    if p:
        column = p.lexer.lexpos - p.lexer.last_pos + 1
        print(f"Syntax error at token {p.type} {p.value}, line {p.lexer.lineno}, column {column}")
    else:
        print("Syntax error at EOF")


meshtal_parser = yacc.yacc(tabmodule="meshtal_tab", debug=True)


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

    Args:
        filename: File that contains MCNP meshtally data.

    Returns:
        tallies Index of mesh tallies contained in the file.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    with filename.open() as f:
        text = f.read() + "\n"
    meshtal_lexer.begin("INITIAL")
    meshtal_data = meshtal_parser.parse(text, lexer=meshtal_lexer)
    histories = meshtal_data["histories"]
    tallies = {}
    for t in meshtal_data["tallies"]:
        name = t["name"]
        particle = t["particle"]
        data = t["result"]
        error = t["error"]
        kwdata = {}
        for k, v in t["bins"].items():
            kwdata[_BIN_NAMES[k]] = v
        tallies[name] = FMesh(name, particle, data, error, histories=histories, **kwdata)
    return tallies
