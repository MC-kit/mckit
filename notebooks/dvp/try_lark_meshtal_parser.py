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
    
    meshtal : header nl title nl "Number of histories used for normalizing tallies =" float tallies

    header : "mcnp" "version" stamp "mpi"? "ld=" stamp "probid =" stamp stamp

    stamp: STAMP

    title: /.+/

    float: SIGNED_FLOAT | INT   

    tallies: (separator tally)+

    ?separator: nl

    ?nl: NEWLINE

    tally : tally_header separator boundaries separator data

    tally_header : "Mesh Tally Number" integer nl tally_header_more

    integer: INT

    tally_header_more: particle  nl -> tally_header_more_wo_comment
        | title nl particle nl -> tally_header_more_with_comment

    particle: "This is a" KIND "tally."

    boundaries: "Tally bin boundaries:" nl [cylinder] bins

    cylinder: "Cylinder origin at"  vector ", axis in"  vector "direction" nl

    vector: float+

    bins : direction nl direction nl direction nl energies nl

    direction : dir_spec "direction:" vector

    dir_spec : "X" | "Y"  | "Z" | "R" | "THETA"

    energies: "Energy bin boundaries:" vector -> energies_e
            | "Time:" vector -> energies_t

    data: matrix_data
         | column_data nl?

    matrix_data: energy_bins [total_energy_bin]

    energy_bins: energy_bins energy_bin separator -> energy_bins_continued
               | energy_bin separator -> energy_bins_first

    energy_bin: "Energy Bin:" float "-" float nl separator spatial_bins -> energy_bin_e
              | "Time:" float nl separator spatial_bins -> energy_bin_t

    spatial_bins: spatial_bins spatial_bin separator -> spatial_bins_continued
                | spatial_bin separator -> spatial_bins_first

    spatial_bin : dir_spec ":" float "-" float nl separator /Tally Results:  .*/ nl matrix separator "Relative Errors" nl matrix separator

    total_energy_bin : "Total Energy Bin" nl separator spatial_bins separator


    column_data : column_header matrix [total_matrix]



    matrix : (vector nl)+
    total_matrix : ("Total" vector nl)+

    column_header : has_energy? dir_spec dir_spec dir_spec "Result" "Rel Error" nl

    ?has_energy: "Energy"

    KIND: "neutron"|"photon"|"electron"

    // MCNP version idenficiation entry on title line
    STAMP: /[0-9\/:]+/

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

    return (grammar,)


@app.cell
def _(grammar):
    parser = Lark(grammar, debug=True)
    return (parser,)


@app.cell
def _(mesh_text, parser):
    tree = parser.parse(mesh_text)
    rich.print(tree)
    return (tree,)


@app.cell
def _(tree):
    tree
    return


@app.cell
def _(tree):
    @v_args(inline=True)
    class TestTransformer(Transformer):
        float = float
    
        @staticmethod
        def vector(*v):
            return np.array(v)
        
    test_transformer = TestTransformer()
    test_result = test_transformer.transform(tree)
    rich.print("result:", test_result)  
    return


@app.cell
def _():
    BIN_REC_ORDER = {"ENERGY": 0, "X": 1, "Y": 2, "Z": 3, "TIME": 0}
    BIN_CYL_ORDER = {"ENERGY": 0, "R": 1, "Z": 2, "THETA": 3, "TIME": 0}
    return


@app.cell
def _():
    return


app._unparsable_cell(
    """
    @v_args(inline=True)
    class MeshtalTransformer(Transformer):
        int = int
        float = float

        def meshtal(self, header, title, histories, tallies):
            return {
                \"date\": header[\"PROBID\"],
                \"title\": title,
                \"histories\": histories,
                \"tallies\": tallies,
            }

        def header(self, version, date, time):
            return {\"PROBID\": date + time, \"VERSION\": version}

        def title(self, _title: str):
            return _title.strip()
    
        def tallies(self, p):
            return p

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

        def tallY_header(self, name: int, from_other_lines):
            from_other_lines[\"name\"] = name
            return from_other_lines

        def tally_header_more_wo_comment(self, particle):
            return {\"particle\": particle}

        def tally_header_more_with_comment(self, comment, particle):
            return {\"comment\": comment, \"particle\": particle}

        def boundaries(self, cyliner, bins):
            boundaries = bins
            if cylinder is not None:
                origin, axis = cylinder
                boundaries[\"ORIGIN\"] = origin
                boundaries[\"AXIS\"] = axis
            for k, v in boundaries.items():
                boundaries[k] = np.array(v)
            return boundaries

        def cylinder(self, origin, axis):
            return origin, axis
        
        def vector(self, *floats: float):
            return np.array(floats)

        def bins(self, ibins, jbins, kbins, ebins):
            return {name: data for name, data in (ibins, jbins, kbins, ebins)}

        def direction(self, dir_spec: str, vector):
            return dir_spec.upper(), vector

        def energies_e(vector):
            return \"ENERGY\": vector

        def energies_t(vector):
            return \"TIME\", vector
        def matrix_data(energy_bins, total_energy_bin):
            order, result, error = energy_bins
            p[0] = {\"result\": result, \"error\": error, \"order\": order}

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
            \"\"\"spatial_bins : spatial_bins spatial_bin separator
            | spatial_bin separator
            \"\"\"
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
            \"\"\"spatial_bin : dir_spec ':' float '-' float newline separator TALLY RESULT ':' dir_spec dir_spec newline matrix separator ERROR newline matrix separator\"\"\"
            order = (dir_spec1, dir_spec3, dir_spec2)   # order 1, 3, 2 is intended
            results = [line[1:] for line in values[1:]]
            errors = [line[1:] for line in relerrs[1:]]
            return order, results, errors


        def total_energy_bin(spatial_bins):
            \"\"\"total_energy_bin : TOTAL ENERGY newline separator spatial_bins separator\"\"\"
            order = (\"TOTAL\",  *spatial_bins[0])
            p[0] = order, spatial_bins[1], spatial_bins[2]
    
        def matrix(self, *vectors):
            return list(vectors)

        def total_matrix(self, *vectors):
            return list[vectors]

        def column_data(self, column_header, matrix, total_matrix):
            \"\"\"column_data : column_header matrix total_matrix
            | column_header matrix
            \"\"\"
            res = column_header
            res[\"data\"] = matrix
            if total_matrix:
                res[\"total\"] = total_matrix
            return res

        def column_header(self, has_energy, ispec, jspec, kspec):
            \"\"\"column_header : ENERGY dir_spec dir_spec dir_spec RESULT ERROR newline
            | dir_spec dir_spec dir_spec RESULT ERROR newline
            \"\"\"
            res = {\"header\": [ispec], jspec, jspec]}
            if has_energy:
                res[\"has_energy\"] = True
            return res


    """,
    name="_"
)


@app.cell
def _():
    # transformer = MeshtalTransformer()
    # result = transformer.transform(tree)
    # rich.print(result)
    return


@app.cell
def _():
    return


@app.cell
def _(result):
    result
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
