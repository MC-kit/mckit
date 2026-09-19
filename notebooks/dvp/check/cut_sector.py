import marimo

__generated_with = "0.23.16"
app = marimo.App()

with app.setup:
    # Initialization code that runs before all other cells
    from typing import Sequence

    import sys
    from pathlib import Path

    import mckit as mc
    import mckit.workflow as mwf
    import mckit.utils as mut

    from mckit import Universe, Box, Body, Shape
    from mckit.cli import init_logger, logger

    __version__ = "0.2.0"
    MODEL_DIR = mut.check_dir(mut.mkpath("~/dev/dsf/lp14/").expanduser())
    OUTPUT_PREFIX = mut.mkdir(MODEL_DIR / f"50-assets/20-output/{__version__}")
    OUTPUT_PREFIX.mkdir(parents=True, exist_ok=True)

    def out_name(fname: str) -> Path:
        return OUTPUT_PREFIX / fname

    def extract_suspicious_universe(tokamak_complex, suspicious_cell: int) -> Universe:
        cells = mwf.extract_cells(tokamak_complex, mwf.filter_by_cell_number(suspicious_cell))
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
    tokamak_complex_path = mut.check_file(MODEL_DIR / "20251013101844_input.i")
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
    mo.md(f"""
    Reading rate: {239727 / (36):.0f} cell/min
    """)
    return


@app.cell
def _():
    global_box = Box.from_bounds(850, 3000, 210, 2330,-1010, 10)
    return (global_box,)


@app.cell
def _(global_box):
    global_box.bounds
    return


@app.cell
def _(global_box, mo):
    global_box_volume = global_box.volume
    mo.md(f"{global_box_volume:.2g}")
    return (global_box_volume,)


@app.cell
def _():
    min_volume_ratio = 1e-9
    return (min_volume_ratio,)


@app.cell
def _(global_box_volume, min_volume_ratio):
    min_volume = global_box_volume * min_volume_ratio
    return (min_volume,)


@app.cell
def _(min_volume):
    min_volume
    return


@app.cell
def _(global_box, min_volume):
    def simplify(cell: Body) -> Body:
        return cell.simplify(box = global_box, min_volume=min_volume)

    return (simplify,)


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
    segment_path = mut.check_file(MODEL_DIR / "segment.i")
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
def _():
    import time

    return (time,)


@app.cell
def _(mo, port_cell, simplify, time):
    def extract_intersecting_cells(cells: Sequence[Body]) -> list[Body]:
        _new_cells = []

        appended = []
        skipped = []
        with mo.status.progress_bar(
            total=len(cells), title="Intersecting cells"
        ) as bar:
            start_time = time.time()
            for bc in cells:
                c_int = simplify(bc.intersection(port_cell))
                if c_int.shape.is_empty():
                    skipped.append(bc.name())
                    subtitle = (
                        f"{c_int.name()} - skipped, total skipped: {len(skipped)}, total_appended: {len(appended)}"
                    )
                else:
                    _new_cells.append(c_int)
                    appended.append(c_int.name())
                    subtitle = (
                        f"{c_int.name()} - appended, total skipped: {len(skipped)}, total appended: {len(appended)}"
                    )
                bar.update(subtitle=subtitle)
            bar.update(
                title="Intersection complete",
                subtitle=f"skipped: {len(skipped)},, appended: {len(appended)}",
            )
            elapsed_time = time.time() - start_time
        return _new_cells, appended, skipped, elapsed_time


    return (extract_intersecting_cells,)


@app.cell
def _(extract_intersecting_cells, tokamak_complex):

    new_cells, appended, skipped, elapsed_time = extract_intersecting_cells(tokamak_complex)  # ty:ignore[invalid-argument-type]
    return appended, elapsed_time, new_cells, skipped


@app.cell
def _(appended, elapsed_time, new_cells, skipped):
    logger.info("Elapsed {}", elapsed_time)
    logger.info("skipped: {}, appended: {}", len(skipped), len(appended))
    logger.info("Cells remaining after extraction {}", len(new_cells))

    return


@app.cell
def _():
    name_for_graveyard =1_000_000
    name_for_graveyard
    return (name_for_graveyard,)


@app.cell
def _(name_for_graveyard, port_cell):
    graveyard = Body(
        port_cell.shape.complement(),
        name = name_for_graveyard,
        VOL=1.0,
        IMPN=0.0,
        IMPP=0.0,
        comment = ["Graveyard"]
    )
    return (graveyard,)


@app.cell
def _(graveyard, new_cells):
    new_u = Universe(new_cells + [graveyard])

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
    import marimo as mo

    return (mo,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
