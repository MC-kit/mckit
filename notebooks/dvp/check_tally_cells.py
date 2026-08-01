import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sys

    from pathlib import Path

    import duckdb as db
    import numpy as np
    import polars as pl

    import mckit as mc
    import mckit.utils as mut
    import mckit.workflow as mcw

    HOST = os.uname().nodename


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Проверка выборя ячеек для тэлли модели ТРТ 5.4.3
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
    sql_path = mut.check_file(MODEL_DIR / "trt-5.4.3.sqlite")
    return (sql_path,)


@app.cell
def _():
    # conn = db.connect(f"{sql_path.with_suffix(".db")}")
    conn = db.connect()
    return (conn,)


@app.cell
def _(conn, sql_path):
    conn.execute(f"attach '{sql_path}' as sq (type sqlite)")
    return


@app.cell
def _():
    path="%нейтронная защита_2%"
    # path="%(МР)Панель вертикальная%"
    return (path,)


@app.cell(hide_code=True)
def _(conn, mo, path):
    _df = mo.sql(
        f"""
        SELECT 
            cell, path
        FROM
        sq.cells 
        where path  like '{path}'
        """,
        engine=conn
    )
    return


@app.cell(hide_code=True)
def _(conn, mo, path):
    _df = mo.sql(
        f"""
        SELECT 
            min(cell), max(cell), count(cell), max(cell) - min(cell)
        FROM
        sq.cells 
        where path  like '{path}'
        """,
        engine=conn
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
