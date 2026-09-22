import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", auto_download=["html"])

with app.setup:

    from pathlib import Path

    import lark_cython
    import numpy as np
    import rich

    from lark import Lark, Transformer, Token, v_args

    # from mckit.fmesh import FMesh

    from config_utils import check_file, find_git_root


@app.cell
def _():
    import marimo as mo

    return


@app.cell
def _():
    ROOT = find_git_root()
    ROOT
    return (ROOT,)


@app.cell
def _(ROOT):
    mesh_path = check_file(ROOT / "tests/data/parser/fmesh2.m")
    return (mesh_path,)


@app.cell
def _(mesh_path):
    mesh_text = mesh_path.read_text(encoding="utf8")
    return (mesh_text,)


@app.cell
def _(mesh_text):
    print(mesh_text[:1000])
    return


@app.cell
def _():
    grammar = r"""
    ?start: meshtal
    
    meshtal : header nl title nl "Number of histories used for normalizing tallies =" float nl nl tallies

    header : "mcnp" "version" stamp "mpi"? "ld=" stamp "probid" stamp stamp

    stamp: STAMP

    title: /.+/

    float: SIGNED_FLOAT   
    int: INT

    tallies: tally (nl tally)*

    tally : tally_header nl boundaries nl data

    tally_header : "Mesh Tally Number" integer nl tally_header_more

    tally_header_more: particle  nl -> tally_header_more_wo_comment
        | mesh_comment nl particle nl -> tally_header_more_with_comment

    mesh_comment: title

    ?nl: NEWLINE

    ?particle: "This is a" KIND "tally."

    ?boundaries : "Tally bin boundaries:" nl boundaries_more:

    boundaries_more: "Cylinder origin at"  vector ", axis in"  vector "direction" nl bins -> boundaries_cyl
        | bins -> boundaries_rect


    vector: float+

    bins : direction nl direction nl direction nl energies nl

    direction : dir_spec "direction:" vector

    ?dir_spec : "X" | "Y"  | "Z" | "R" | "THETA"

    energies : "Energy bin boundaries:" vector -> energies_e
        | "Time:" vector -> energies_t

    ?data : matrix_data
       | column_data nl?

    matrix_data : energy_bins total_energy_bin?

    column_data : column_header matrix total_matrix?

    energy_bins : (energy_bin nl)+

    energy_bin : "Energy Bin:" float "-" float nl separator spatial_bins
         | "Time:" float nl separator spatial_bins

    spatial_bins : spatial_bin+ separator

    spatial_bin : dir_spec ':' float '-' float nl separator /Tally Results:  .*/ nl matrix separator "Relative Errors" nl matrix separator

    matrix : (vector nl)+
    total_matrix : ("Total" vector nl)+

    total_energy_bin : "Total Energy Bin" nl separator spatial_bins separator

    column_header : has_energy? dir_spec dir_spec dir_spec "Result" "Rel Error" nl

    ?has_energy: "Energy"

    ?separator: nl

    KIND: "neutron"|"photon"|"electron"
    MESH_TALLY_NUMBER : 
    NPS_LINE_START: 

    // MCNP version idenficiation entry on title line
    STAMP : r"[\d/:]+"

    // A generic identifier for any non-keyword word
    WORD: /[A-Za-z_][A-Za-z0-9_]*/

    // Keywords (must come with higher priority so they win over WORD)
    KEYWORD.10: "MCNP" | "VERSION" | "LD" | "PROBID" | "NEUTRON"
              | "PHOTON" | "ELECTRON" | "RESULT" | "RESULTS"
              | "ERROR" | "ERRORS" | "CYLINDER" | "ORIGIN" | "AXIS"
              | "TALLY" | "MPI" | "X" | "Y" | "Z" | "R"
              | "THETA" | "ENERGY" | "TIME" | "TH" | "TOTAL"

    // Numbers
    %import common.SIGNED_FLOAT
    %import common.INT
    // Separators / whitespace (ignored)
    %import common.WS_INLINE
    %import common.NEWLINE
    %ignore WS_INLINE
    """

    return


@app.cell
def _():
    gr1="""
    ?start: particle
    particle: "This is a" KIND "mesh tally."
    KIND: "neutron"|"photon"
    %import common.NEWLINE
    %import common.WS_INLINE
    %ignore WS_INLINE
    """
    return (gr1,)


@app.cell
def _(gr1):
    parser = Lark(gr1)
    return (parser,)


@app.cell
def _():
    txt1="""\
    This is a photon mesh tally."""
    return (txt1,)


@app.cell
def _(parser, txt1):
    tree = parser.parse(txt1)
    rich.print(tree)
    return (tree,)


@app.cell
def _(tree):
    tree
    return


@app.cell
def _():
    BIN_REC_ORDER = {"ENERGY": 0, "X": 1, "Y": 2, "Z": 3, "TIME": 0}
    BIN_CYL_ORDER = {"ENERGY": 0, "R": 1, "Z": 2, "THETA": 3, "TIME": 0}
    return


app._unparsable_cell(
    """
    class MeshtalTransformer(Transformer):
        int = int
        float = float

        @v_args(inline=True)
        def meshtal(self, header, title, histories, tallies):
            return {
                \"date\": header[\"PROBID\"],
                \"title\": title,
                \"histories\": histories,
                \"tallies\": tallies,
            }

        @v_args(inline=True)
        def header(self, version, date, time):
            return {\"PROBID\": date + time, \"VERSION\": version}

        @v_args(inline=True)
        def title(self, _title: str)
    
        def tallies(self, p):
            return p

        @v_args(inline=True)
        def tally(self, tally_header, boundaries, data):
            \"\"\"tally : tally_header separator boundaries separator data\"\"\"
            tally = tally_header
            tally[\"geom\"] = \"XYZ\"
            if \"ORIGIN\" in boundaries:
                tally[\"origin\"] = boundaries.pop(\"ORIGIN\")
                tally[\"geom\"] = \"CYL\"
            if \"AXIS\" in boundaries:
                tally[\"axis\"] = boundaries.pop(\"AXIS\")
            tally[\"bins\"] = {k: np.array(v) for k, v in boundaries.items()}
            od = BIN_CYL_ORDER if \"origin\" in tally else BIN_REC_ORDER
            if \"result\" in data:
                src_perm = [od[let] for let in data[\"order\"]]
                tally[\"result\"] = np.moveaxis(np.array(data[\"result\"]), (0, 1, 2, 3), src_perm)
                tally[\"error\"] = np.moveaxis(np.array(data[\"error\"]), (0, 1, 2, 3), src_perm)
            else:
                header = data[\"header\"]
                data = np.array(data[\"data\"])
                shape = [0, 0, 0, 0]
                for k in tally[\"bins\"]:
                    v = od[k]
                    shape[v] = boundaries[k].size
                    if k != \"TIME\":
                        shape[v] -= 1
                if \"ENERGY\" in boundaries:
                    boundaries[\"ENERGY\"] = 0.5 * (boundaries[\"ENERGY\"][1:] + boundaries[\"ENERGY\"][:-1])
                result = np.empty(shape)
                error = np.empty(shape)
                indices = np.empty((data.shape[0], 4), dtype=int)
                for k in boundaries:
                    if k in header:
                        indices[:, od[k]] = np.searchsorted(boundaries[k], data[:, header.index(k)]) - 1
                    else:
                        indices[:, od[k]] = np.zeros(data.shape[0])
                res_ind = header.index(\"RESULT\")
                err_ind = header.index(\"ERROR\")
                for i in range(indices.shape[0]):
                    result[tuple(indices[i, :])] = data[i, res_ind]
                    error[tuple(indices[i, :])] = data[i, err_ind]
                tally[\"result\"] = result
                tally[\"error\"] = error
            return tally

        @v_args(inline=True)
        def tallY_header(self, name: int, from_other_lines):
            from_other_lines[\"name\"] = name
            return from_other_lines

        def tally_header_more_wo_comment(self, particle):
            return {\"particle\": particle}

        def tally_header_more_with_comment(self, comment, particle):
            return {\"comment\": comment, \"particle\": particle}

        @v_args(inline=True)
        def particle(self, kind: str):
            return kind

        @v_args(inline=True)
        def boundaries_cyl(self, origin, axis, bins):
            boundaries = bins
            boundaries[\"ORIGIN\"] = origin
            boundaries[\"AXIS\"] = axis
            for k, v in boundaries.items():
                boundaries[k] = np.array(v)
            return boundaries

        @v_args(inline=True)
        def boundaries_rect(self, boundaries):
            for k, v in boundaries.items():
                boundaries[k] = np.array(v)
            p[0] = boundaries

        @v_args(inline=True)
        def bins(self, ibins, jbins, kbins, ebins):
            \"\"\"bins : direction newline direction newline direction newline energies newline\"\"\"
            return {name: data for name, data in (ibins, jbins, kbins, ebins)}

        @v_args(inline=True)
        def direction(self, dir_spec: str, vector):
            return dir_spec.upper(), vector

        @v_args(inline=True)
        def energies_e(vector):
            return \"ENERGY\": vector

        @v_args(inline=True)
        def energies_t(vector):
            return \"TIME\", vector

        def vector(self, p):  # TODO check in debugger
            return np.array(p)

        def matrix(self, p):
            return p

        def total_matrix(self, p):
            return p

        @v_args(inline=True)
        def column_data(self, column_header, matrix, total_matrix):
            \"\"\"column_data : column_header matrix total_matrix
            | column_header matrix
            \"\"\"
            res = column_header
            res[\"data\"] = matrix
            if total_matrix:
                res[\"total\"] = total_matrix
            return res

        @v_args(inline=True)
        def column_header(self, has_energy, ispec, jspec, kspec):
            \"\"\"column_header : ENERGY dir_spec dir_spec dir_spec RESULT ERROR newline
            | dir_spec dir_spec dir_spec RESULT ERROR newline
            \"\"\"
            res = {\"header\": [ispec], jspec, jspec]}
            if has_energy:
                res[\"has_energy\"] = True
            return res

        @v_args(inline=True)
        def matrix_data(energy_bins, total_energy_bin):
            order, result, error = energy_bins
            p[0] = {\"result\": result, \"error\": error, \"order\": order}

        @v_args(inline=True)
        def energy_bins(self, energy_bins):
            if len(p) == 3:
                order, result, error = p[1]
                p[0] = order, [result], [error]
            else:
                order, result, error = p[2]
                p[1][1].append(result)
                p[1][2].append(error)
                p[0] = order, p[1][1], p[1][2]
    
    """,
    name="_"
)


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
    return


if __name__ == "__main__":
    app.run()
