from __future__ import annotations

import cProfile as prof  # noqa: N813
import platform

from pathlib import Path
from time import time

from mckit import __version__
from mckit.parser import read_meshtal
from mckit.utils import get_last_line

HERE = Path(__file__).parent


node = platform.node()
mesh_path = HERE / "data/64M.m"
mesh_size = mesh_path.stat().st_size
start = time()
read_meshtal(mesh_path)
end = time()
elapsed = end - start
results_csv = HERE / "results/mestal_parsing.csv"
elapsed_old = None
if results_csv.exists():
    last_line = get_last_line(results_csv, chunk_size=256)
    assert len(last_line) < 256
    if last_line:
        elapsed_old = float(last_line.rsplit(",", maxsplit=2)[-2])

with results_csv.open(mode="a", encoding="utf8") as fid:
    print(
        __version__,
        node,
        mesh_path.relative_to(HERE),
        mesh_size,
        elapsed,
        elapsed / elapsed_old if elapsed_old else 1.0,
        file=fid,
        sep=",",
    )

prof.run("read_meshtal(mesh_path)", "results/lark_meshtal.prof")

# View results (in results dir) with snakeviz:
# uvx snakeviz lark_meshtal.prof
