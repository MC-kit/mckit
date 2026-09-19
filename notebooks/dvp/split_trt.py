import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sys

    from pathlib import Path

    import numpy as np

    import mckit as mc
    import mckit.utils as mut
    import mckit.workflow as mcw

    HOST = os.uname().nodename


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Разбивка интегральной модели ТРТ 5.4.3 на текстовые сегменты

    Для сборки вариантов модели нужно разбить ее на сегменты.
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(f"""
        - Python: {sys.version}, at {sys.prefix}
        - host: {HOST}
        - cwd: {Path.cwd()}
        - mckit: {mc.__version__}
    """).callout()
    return


@app.cell
def _():
    VERSION = "0.1.0"
    return


@app.cell
def _():
    MODEL_DIR = mut.check_dir(Path("~/dev/mcnp/trt/wrk/models/2025/5.4.3").expanduser())
    return (MODEL_DIR,)


@app.cell
def _(MODEL_DIR):
    MODEL_DIR
    return


@app.cell
def _(MODEL_DIR):
    model_path = mut.check_file(MODEL_DIR / "trt-5.4.3.i")
    return (model_path,)


@app.cell
def _():
    from mckit.cli.commands import do_split

    return (do_split,)


@app.cell
def _(MODEL_DIR, do_split, model_path):
    def _():
        split_dir = MODEL_DIR / "hall+trt-5.4.3.split"
        split_dir.mkdir(parents=True, exist_ok=True)
        do_split(split_dir, model_path, override=True, separators=True)

    _()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
