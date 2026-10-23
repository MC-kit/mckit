# ruff: noqa: F401
from __future__ import annotations

import cProfile as prof  # noqa: N813

from pathlib import Path

from time import time
from mckit.parser.meshtal_lark_parser import read_meshtal as read_lark_mehstal
from mckit.parser.meshtal_parser import read_meshtal

HERE = Path(__file__).parent


# @lenovo
# mesh_path = HERE / "data/heat-1.1e10.m"
# start = time()
# read_meshtal(mesh_path)
# end =time()
# elapsed = end - start
# print("Old meshtal:", elapsed) # 373 s
# start = time()
# read_lark_mehstal(mesh_path)
# end = time()
# elapsed = end - start
# print("New meshtal:", elapsed) # 929 s - 2.5 times longer


# @WS-TNT
mesh_path = HERE / "data/400k.m"
start = time()
read_meshtal(mesh_path)
end =time()
elapsed = end - start
print("Old meshtal:", elapsed) # 373 s
start = time()
read_lark_mehstal(mesh_path)
end = time()
elapsed = end - start
print("New meshtal:", elapsed) # 929 s - 2.5 times longer

prof.run("read_meshtal(mesh_path)", "results/read_mesthal.prof")
prof.run("read_lark_mehstal(mesh_path)", "results/lark_mehstal.prof")

# View results (in results dir) with snakeviz:
# uvx snakeviz lark_mehstal.prof