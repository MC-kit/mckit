from __future__ import annotations

from pathlib import Path

from mckit.parser import from_file

HERE = Path(__file__).parent

WRK_DIR = HERE / "../wrk"
assert WRK_DIR.is_dir()

path = WRK_DIR / "UPP08_#3h.i"
assert path.exists()


model = from_file(path).universe
model.simplify(min_volume=1e-3)
model.save(WRK_DIR / "up08-simplified.i")
