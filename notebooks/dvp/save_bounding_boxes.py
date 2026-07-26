import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sqlite3 as sq
    import sys

    from pathlib import Path

    import duckdb as db
    import numpy as np
    import polars as pl

    import mckit as mc
    import mckit.utils as mut
    import mckit.workflow as mcw

    HOST = os.uname().nodename
    VERSION = "0.2.0"
    MODEL_DIR = mut.check_dir(mut.mkpath("~/dev/mcnp/trt/wrk/models/2025/5.4.1").expanduser())


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Перенос данных по bounding box csv->slite

    Есть файл trt-5.4-component-volumes.csv содержащий данные по ячейкам, включая объем, границы bounding box, путь в STP файле.
    Есть база данных trt-5.4.sqlite, в которой есть таблица 'cells' с аналогичными полями. В CSV путь получен из STP c помощью скрипта extract-info прогоном в SpaceClaim. Файл sqlite создан mapstp командой summary2sqlite. Эта команда переносит информацию из summary файла, созданного geouned при генерации модели. Путь в summary отличается от пути найденного extract_info: в конце вместо имени тела, geouned вставляет номер. Видимо, это связано с возможной декомпозицией тела в момент генерации модели.

    Нужно проверить, есть ли однозначное соответствие между путями в summary и extract_info csv. Если можно такое соответствие установить, то:
    1) перенести информацию о bounding box
    2) проверить соответствие объемов, измеренных extract_info (в SpaceClaim) и geouned (FreeCad).
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
    sql_path = mut.check_file(MODEL_DIR / "trt-5.4.sqlite")
    return (sql_path,)


@app.cell
def _():
    csv_path = mut.check_file(MODEL_DIR / "trt-5.4-component-volumes.csv")
    return (csv_path,)


@app.cell
def _(csv_path):
    csv = pl.read_csv(csv_path)
    return (csv,)


@app.cell
def _(csv):
    csv
    return


@app.cell
def _(sql_path):
    conn = db.connect(f"{sql_path.with_suffix(".db")}")
    return (conn,)


@app.cell
def _(conn, sql_path):
    conn.execute(f"attach '{sql_path}' as sq (type sqlite)")
    return


@app.cell
def _(conn):
    sum = conn.table("sq.cells").pl()
    return (sum,)


@app.cell
def _(csv, sum):
    len(csv) == len(sum)
    return


@app.cell
def _(conn):
    conn.execute(
        """
        select ok, count(*) as cnt from (
            select
                starts_with(
                    cells.path, 
                    REGEXP_REPLACE(csv.path, '/.*$', '')
                ) as ok
            from sq.cells, csv
            where sq.cells.cell = csv.offset
        )
        group by ok
        """
    ).pl()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Начала путей совпадают для каждой ячейки.

    Проверим совпадение объемов.
    """)
    return


@app.cell
def _(conn):
    conn.execute(
        """
        with r as ( 
            select
            abs(sq.cells.volume - csv.volume)/(sq.cells.volume + csv.volume) as ratio
            from sq.cells, csv
            where sq.cells.cell = csv.offset
        )
        select
            min(ratio), 
            avg(ratio),
            max(ratio)
        from r
        """
    ).pl()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Относительное совпадение объемов очень хорошее.

    Перенесем инфорамцию о bounding box.
    """)
    return


@app.cell
def _(conn):
    conn.execute(
        """
        create or replace table cells as
        select
            c.cell,
            c.volume,
            csv.xmin,
            csv.ymin,
            csv.zmin,
            csv.xmax,
            csv.ymax,
            csv.zmax,
            c.path,
            c.material,
            c.density,
            c.correction,
            c.rwcl,
            csv.path as csv_path,
            csv.volume as csv_volume        
        from 
            sq.cells as c
            inner join csv on c.cell = csv.offset
        """
    )
    return


@app.cell
def _(conn):
    conn.table("cells").pl()
    return


@app.cell
def _(conn):
    conn.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Utils
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
