import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", auto_download=["html"])

with app.setup:
    import logging
    import sys

    from pathlib import Path
    from textwrap import dedent

    import lark_cython
    import numpy as np
    import rich

    from rich.console import Console
    from rich.logging import RichHandler
    from rich.traceback import install



    from lark import Lark, Transformer, Token, v_args

    MY_NAME = "try-lark-parser"

    # Use Rich as the default traceback handler for all uncaught exceptions
    install(show_locals=True)

    def get_logger(suffix: str | None = None) -> logging.Logger:
        """Get the package specific logger.

        Parameters
        ----------
            suffix
                The requested logger name, optional

        Returns
        -------
            The logger for name prepended with the package name, if provided,
            otherwise the root MY_NAME logger
        """
        return logging.getLogger(MY_NAME if suffix is None else MY_NAME + "." + suffix)

    # File handler
    file_handler = logging.FileHandler("try-lark-parser-debug.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=Console(), rich_tracebacks=True),
            file_handler,
        ],
    )

    logger = logging.getLogger("lark")
    logger.disabled = False
    logger.setLevel(logging.DEBUG)

    logger = get_logger()
    logger.disabled = False
    logger.setLevel(logging.DEBUG)



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

    from config_utils import HOST, check_file, find_git_root
    HOST
    return (find_git_root,)


@app.cell
def _(find_git_root):
    ROOT = find_git_root()
    ROOT
    return


@app.cell
def _():
    text="""
       1 2
       3 4"""
    return (text,)


@app.cell
def _():
    grammar=r"""
    start: _N* matrix _N*

    _N: /\r?\n/

    matrix: (vector _N)+

    # This works but the tree is too complicated with long left branch
    # matrix: [matrix _N] vector

    vector: float+

    ?float: SIGNED_NUMBER

    // Numbers
    %import common.SIGNED_NUMBER
    // Separators / whitespace (ignored)
    %import common.WS_INLINE
    %ignore WS_INLINE
    """
    return (grammar,)


@app.cell
def _(grammar):
    parser = Lark(grammar, parser="lalr", cache=False, debug=True)
    return (parser,)


@app.cell
def _(parser, text):
    list(map(lambda t: f"{t.type}: {t.value}", parser.lex(text)))
    return


@app.cell
def _(parser, text):
    def _():
        tree = parser.parse(text)
        return tree
    rich.print(_())
    return


@app.cell
def _():
    return


@app.cell
def _(parser, text):
    parsed_tokens = []
    try:
        tree = parse_with_progress(parser, text, parsed_tokens=parsed_tokens)
        with Path("try-lark-parser-tree.txt").open("w") as _f:
            rich.print(tree, file=_f)
    finally:
        with Path("try-lark-parser-tokens.txt").open("w") as _f:
            for t in parsed_tokens:
                rich.print(t, file=_f)
    return parsed_tokens, tree


@app.cell
def _(parsed_tokens):
    rich.print(parsed_tokens)
    return


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


@app.function
def parse_with_progress(parser: Lark, text: str, start=None, parsed_tokens: list[str] | None = None):
    if parsed_tokens is not None:
        del parsed_tokens[:]
    pi = parser.parse_interactive(text, start=start)
    for i, token in enumerate(pi.iter_parse()):
        if parsed_tokens is not None:
            parsed_tokens.append(dedent(
                f"""\
                {i}:
                    tp: {token.type}
                    vl: {token.value if token.type not in ("_NL", "_SP") else "..."} 
                    ln: {token.line}
                    ps: {token.start_pos}
                    {pi.pretty().replace("Parser choices", "ch")}
                """))
    return pi.resume_parse()


if __name__ == "__main__":
    app.run()
