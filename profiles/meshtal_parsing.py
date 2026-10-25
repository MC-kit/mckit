from __future__ import annotations

import cProfile as prof  # noqa: N813
import platform

from pathlib import Path
from time import time

from loguru import logger

from mckit.parser.meshtal_lark_parser import read_meshtal as read_lark_meshtal
from mckit.parser.meshtal_parser import read_meshtal

HERE = Path(__file__).parent

logger.add(HERE / "result/meshtal_parsing.log")

logger.info("Platform {}", platform.node())
# @lenovo
# mesh_path = HERE / "data/1534M.m"
mesh_path = HERE / "data/62M.m"
# @WS-TNT
# mesh_path = HERE / "data/400k.m"
logger.info("Mesh: {}", mesh_path)
logger.info("Mesh size: {}", mesh_path.stat().st_size)
start = time()
read_meshtal(mesh_path)
end =time()
elapsed_old = end - start
logger.info("Old meshtal ET: {:.3g}", elapsed_old)
# lenovo: 373 s
start = time()
read_lark_meshtal(mesh_path)
end = time()
elapsed_new = end - start
logger.info("New meshtal ET: {:.3g}", elapsed_new)
logger.info("Ratio: {:.2g}", elapsed_new/elapsed_old)

# prof.run("read_meshtal(mesh_path)", "results/read_meshtal.prof")
prof.run("read_lark_meshtal(mesh_path)", "results/lark_meshtal.prof")

# View results (in results dir) with snakeviz:
# uvx snakeviz lark_meshtal.prof

