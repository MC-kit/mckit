import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", auto_download=["html"])

with app.setup:
    import sys

    from pathlib import Path
    from textwrap import dedent

    import lark_cython
    import numpy as np
    import rich

    from lark import Lark, Transformer, Token, v_args

    # from mckit.fmesh import FMesh


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.notebook_dir()
    return


@app.cell
def _(mo):
    if not mo.running_in_notebook():
        nb_common_path = Path(mo.notebook_dir().parent, "nb_common").absolute()
        assert nb_common_path.is_dir(), nb_common_path
        nb_common_name = str(nb_common_path)
        if not nb_common_name in sys.path:
            sys.path.append(str(nb_common_path))

    from config_utils import check_file, find_git_root

    return check_file, find_git_root


@app.cell
def _(find_git_root):
    ROOT = find_git_root()
    ROOT
    return (ROOT,)


@app.cell
def _(ROOT, check_file):
    mesh_path = check_file(ROOT / "tests/data/parser/fmesh2.m")
    return (mesh_path,)


@app.cell
def _(mesh_path):
    mesh_text = mesh_path.read_text(encoding="utf8")
    return (mesh_text,)


@app.cell
def _(grammar):
    parser = Lark(grammar, start="meshtal", parser="lalr", debug=True)
    return (parser,)


@app.cell
def _(mesh_text, parser):
    parsed_tokens = []
    try:
        tree = parse_with_progress(parser, mesh_text, start="meshtal", parsed_tokens=parsed_tokens)
    finally:
        with Path("try_lark_tokens.txt").open("w") as _f:
            for t in parsed_tokens:
                rich.print(t, file=_f)
    return (tree,)


@app.cell
def _(tree):
    with Path("try_lark.txt").open("w") as _f:
        rich.print(tree, file=_f)
    return


@app.cell
def _():
    BIN_REC_ORDER = {"ENERGY": 0, "X": 1, "Y": 2, "Z": 3, "TIME": 0}
    BIN_CYL_ORDER = {"ENERGY": 0, "R": 1, "Z": 2, "THETA": 3, "TIME": 0}
    return BIN_CYL_ORDER, BIN_REC_ORDER


@app.cell
def _():
    grammar = (Path(__file__).parent / "meshtal.lark").read_text()
    return (grammar,)


@app.cell
def _(Any, BIN_CYL_ORDER, BIN_REC_ORDER, p):
    @v_args(inline=True)
    class MeshtalTransformer(Transformer):
        int = int
        float = float

        def meshtal(self, header, title, histories, tallies):
            return {
                "date": header["PROBID"],
                "title": title,
                "histories": histories,
                "tallies": tallies,
            }

        def header(self, version, build_date, date, time):
            return {
                "PROBID": date.value + time.value, 
                "VERSION": version, 
                "BUILD_DATE": build_date
            }

        def title(self, _title: str):
            return _title.strip() 

        def nps(self, _float):
            return _float       

        def tallies(self, p):
            return p

        def tally(self, tally_header, boundaries, data):
            rich.print(tally_header)
            tally = tally_header
            if "ORIGIN" in boundaries:
                tally["origin"] = boundaries.pop("ORIGIN")
                tally["geom"] = "CYL"
                assert "AXIS" in boundaries
                tally["axis"] = boundaries.pop("AXIS")
            else:
                tally["geom"] = "XYZ"
            tally["bins"] = {k: np.array(v) for k, v in boundaries.items()}
            od = BIN_CYL_ORDER if "origin" in tally else BIN_REC_ORDER
            if "result" in data:
                src_perm = [od[let] for let in data["order"]]
                tally["result"] = np.moveaxis(np.array(data["result"]), (0, 1, 2, 3), src_perm)
                tally["error"] = np.moveaxis(np.array(data["error"]), (0, 1, 2, 3), src_perm)
            else:
                header = data["header"]
                data = np.array(data["data"])
                shape = [0, 0, 0, 0]
                for k in tally["bins"]:
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
                tally["result"] = result
                tally["error"] = error
            return tally

        def tally_header(self, name: int, from_other_lines: dict[str, Any]) -> dict[str, str|int]:
            rich.print("tall_header:", name, from_other_lines)
            from_other_lines["name"] = name
            return from_other_lines

        def tally_header_more_wo_comment(self, particle: str) -> dict[str, str]:
            return {"particle": particle}

        def particle(self, kind):
            return kind.value.upper()  # to reproduce old PLY parser

        def tally_header_more_with_comment(self, comment, particle):
            return {"comment": comment, "particle": particle}

        def boundaries(self, cylinder, bins):
            boundaries = bins
            if cylinder is not None:
                origin, axis = cylinder
                boundaries["ORIGIN"] = origin
                boundaries["AXIS"] = axis
            for k, v in boundaries.items():
                boundaries[k] = np.array(v)
            return boundaries

        def cylinder(self, origin, axis):
            return origin, axis

        def vector(self, *floats: float):
            return np.array(floats)

        def bins(self, ibins, jbins, kbins, ebins):
            return {name: data for name, data in (ibins, jbins, kbins, ebins)}

        def direction_theta(self, vector):
            return "THETA", vector

        def direction_xyzr(self, dir_spec: str, vector):
            return dir_spec, vector

        def dir_spec(self, spec: str) -> str:
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
            order = (dir_spec1, dir_spec3, dir_spec2)   # order 1, 3, 2 is intended
            results = [line[1:] for line in values[1:]]
            errors = [line[1:] for line in relerrs[1:]]
            return order, results, errors


        def total_energy_bin(spatial_bins):
            """total_energy_bin : TOTAL ENERGY newline separator spatial_bins separator"""
            order = ("TOTAL",  *spatial_bins[0])
            p[0] = order, spatial_bins[1], spatial_bins[2]

        def matrix(self, *vectors):
            return list(vectors)

        def total_matrix(self, *vectors):
            return list[vectors]

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
                return {"header": ["ENERGY", ispec, jspec, kspec,  "RESULT", "ERROR"]}
            return {"header": [ispec, jspec, kspec,  "RESULT", "ERROR"]}
                



    return (MeshtalTransformer,)


@app.cell
def _(MeshtalTransformer, tree):
    transformer = MeshtalTransformer()
    result = transformer.transform(tree)
    rich.print(result)
    return (result,)


@app.cell
def _(result):
    result
    return


@app.cell
def _():
    # portion="""\
    #   mcnp   version 5     ld=09292010  probid =  05/24/18 12:21:45
    #  fmesh test
    #  Number of histories used for normalizing tallies =      10000000.00"""
    return


@app.cell
def _():
    # parse_with_progress(parser, portion, start="meshtal")
    return


@app.function
def parse_with_progress(parser: Lark, text: str, start=None, parsed_tokens: list[str] | None = None):
    last = 0
    if parsed_tokens is not None:
        del parsed_tokens[:]
    pi = parser.parse_interactive(text, start=start)
    for i, token in enumerate(pi.iter_parse()):
        if parsed_tokens is not None:
            parsed_tokens.append(dedent(
                f"""\
                {i}:
                    tp: {token.type}
                    vl: {token.value if token.value != "\n" else "\\n"} 
                    ln: {token.line}
                    ps: {token.start_pos}
                """))
        if token.end_pos is not None:
            last = token.end_pos
    return pi.resume_parse()


if __name__ == "__main__":
    app.run()
