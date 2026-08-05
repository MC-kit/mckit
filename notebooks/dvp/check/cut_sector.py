import marimo

__generated_with = "0.23.9"
app = marimo.App()

with app.setup:
    # Initialization code that runs before all other cells
    from typing import TYPE_CHECKING, Sequence

    import sys
    from pathlib import Path

    import mckit as mc


    from mckit import Universe
    from mckit.cli import init_logger, logger
    from mckit.workflow import filter_by_cell_number, extract_cells, make_universe

    if TYPE_CHECKING:
        from mckit import Body

    __version__ = "0.1.1"
    OUTPUT_PREFIX = Path(f"50-assets/20-output/{__version__}")
    OUTPUT_PREFIX.mkdir(parents=True, exist_ok=True)

    def out_name(fname: str) -> Path:
        return OUTPUT_PREFIX / fname

    def extract_suspicious_universe(tokamak_complex, suspicious_cell: int) -> Universe:
        cells = extract_cells(tokamak_complex, filter_by_cell_number(suspicious_cell))
        return make_universe(cells)

    def save_suspicious_universe(universe: Universe, suspicious_cell: int) -> None:
        suspicious_universe_path = out_name(f"suspicios-{suspicious_cell}.mcnp")
        universe.save(suspicious_universe_path)
        logger.info(
            "Saved universe for suspicious cell {} in ",
            suspicious_cell,
            suspicious_universe_path.absolute(),
        )

    init_logger(out_name("mckit.log"), quiet=False, verbose=False)
    logger.info("Script cut_sector.py, version {}", __version__)
    logger.info("Extracting sector")
    logger.info("Using mckit {}", mc.__version__)
    logger.info("Working dir: {}", Path.cwd())
    logger.info("Python {}, at {}", sys.version, sys.prefix)
    logger.info("Output files will be saved in {}", OUTPUT_PREFIX)



@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Extract sector from tokamak building model
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    tokamak_complex_path = "20251013101844_input.i"
    _path = Path(tokamak_complex_path)
    logger.info("Tokamak complex model file: {}", _path.absolute())
    logger.info("            ... model size: {}", _path.stat().st_size)
    return (tokamak_complex_path,)


@app.cell
def _(tokamak_complex_path):

    tokamak_complex_info = mc.from_file(tokamak_complex_path, encoding="cp1251")
    return (tokamak_complex_info,)


@app.cell
def _(tokamak_complex_info):
    logger.info(
        "Cells to process from tokamak complex {}", len(tokamak_complex_info.cells)
    )
    return


@app.cell
def _(mo):
    mo.md(f"Reading rate: {239727 / (32):.0f} cell/min")
    return


@app.cell
def _(tokamak_complex_info):
    tokamak_complex = tokamak_complex_info.universe
    return (tokamak_complex,)


@app.cell
def _(tokamak_complex):
    logger.info("Top level cells: {}", len(tokamak_complex))
    return


@app.cell
def _():
    segment_path = "segment.i"
    logger.info("Segment model: {}", Path(segment_path).absolute())
    return (segment_path,)


@app.cell
def _(segment_path):

    port_box_info = mc.from_file(segment_path)
    return (port_box_info,)


@app.cell
def _(port_box_info):
    port_box_info.cells
    return


@app.cell
def _(port_box_info):
    port_cell = port_box_info.cells[0]
    return (port_cell,)


@app.cell
def _(mo, port_cell):
    def extract_intersecting_cells(cells: Sequence[Body]) -> list[Body]:
        _new_cells = []

        total_appended = 0
        total_skipped = 0
        with mo.status.progress_bar(
            total=len(cells), title="Intersecting cells"
        ) as bar:
            for bc in cells:
                c_int = bc.intersection(port_cell).simplify(min_volume=1e1)
                if c_int.shape.is_empty():
                    total_skipped += 1
                    subtitle = (
                        f"{c_int.name()} - skipped, {total_skipped=}, {total_appended=}"
                    )
                else:
                    _new_cells.append(c_int)
                    total_appended += 1
                    subtitle = f"{c_int.name()} - appended, {total_skipped=}, {total_appended=}"
                bar.update(subtitle=subtitle)
            bar.update(
                title="Intersection complete",
                subtitle=f"{total_skipped=}, {total_appended=}",
            )
        return _new_cells


    return (extract_intersecting_cells,)


@app.cell
def _(extract_intersecting_cells, tokamak_complex):

    new_cells = extract_intersecting_cells(tokamak_complex)  # ty:ignore[invalid-argument-type]
    return (new_cells,)


@app.cell
def _(new_cells):

    logger.info("Cells remaining after extraction {}", len(new_cells))
    return


@app.cell
def _(new_cells):

    new_u = make_universe(new_cells)  # , name_rule = "clash")

    # flat_model = new_u.apply_fill()
    # new_u.rename(start_cell=0, start_surf=0, start_mat=0, name=0)

    extracted_path = out_name("lp14-test.i")
    new_u.save(extracted_path)

    logger.success("Extracted model saved to {}", extracted_path.absolute())
    return


@app.cell
def _():
    suspicious_cell = 138850
    return (suspicious_cell,)


@app.cell
def _(suspicious_cell, tokamak_complex):
    suspicious_universe = extract_suspicious_universe(tokamak_complex, suspicious_cell)
    save_suspicious_universe(suspicious_universe, suspicious_cell)
    return


@app.cell
def _():
    from PIL import Image


    def convert_to_png(ps_file: Path) -> None:
        img = Image.open(ps_file, formats=["EPS"])
        dst_file = ps_file.with_suffix(".png")
        img.save(dst_file)


    # convert_to_png(Path("surfaces.ps"))
    return


@app.cell
def _():
    def _():
        import subprocess
        from PIL import Image

        input_ps = "surfaces.ps"
        output_png = "output.png"

        # Execute the exact Ghostscript command that works for you
        # -sDEVICE=pngalpha ensures transparency if needed, -r300 sets DPI
        cmd = [
            f"{sys.prefix}/bin/gs",  # Or full path like 'C:\\Program Files\\gs\\...\\gswin64c.exe'
            "-sDEVICE=pngalpha",
            "-r300",
            "-o",
            output_png,
            input_ps,
        ]

        try:
            # Run Ghostscript
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Now open the generated PNG with Pillow for further manipulation if needed
            img = Image.open(output_png)
            rotated_img = img.rotate(270, expand=True)
            rotated_img.save(output_png)
            print(f"Successfully converted {input_ps} to {output_png}")
            return output_png

        except subprocess.CalledProcessError as e:
            print(f"Ghostscript failed: {e.stderr.decode()}")
        except FileNotFoundError:
            print("Ghostscript not found. Ensure 'gs' is in your system PATH.")

    # mo.image(_(), width=1500)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
