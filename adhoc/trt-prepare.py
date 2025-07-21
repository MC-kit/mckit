from pathlib import Path

import mckit as mc

WRK_DIR = Path("~/dev/mcnp/trt").expanduser()
assert WRK_DIR.exists()
print("Working directory: ", WRK_DIR)


def load_model(model_file):
    return mc.parser.from_file(model_file)


if __name__ == "__main__":
    model = load_model(WRK_DIR / "mcnp/trt-2.3.i")
