"""Compute UP08 ISS/Portcell model intersection with envelopes for  UP08 ex-vessel components.
===================================================================================================

We don't use bounding boxes here, because the number of cells in the model is much more (about 1000 times)
than number of GA envelopes. The complexity is not reduced significantly using bounding box.
"""

import typing as tp

from functools import reduce
from glob import glob
from pathlib import Path

from tqdm import tqdm

import mckit as mk

working_dir = Path.cwd()
print("Working dir: ", working_dir)


def load_model(model):
    return mk.parser.from_file(model).universe


up08 = load_model("u200.i")
print("Model length: ", len(up08))


def intersect(model, envelop_file_name):
    envelop_path = Path(envelop_file_name)
    intersection_path = working_dir / "intersections" / envelop_path.name
    if intersection_path.exists():
        print(f"File {intersection_path} already exists. Skipping...")
        return
    envelop = load_model(envelop_path)
    print(f"Envelop {envelop_path}, length: {len(envelop)}")
    envelop_union = reduce(mk.Body.union, envelop[:3]).simplify(min_volume=0.1)

    envelopes_cells: tp.List[mk.Body] = []

    for c8 in tqdm(up08, desc=envelop_path.name):
        new_cell = c8.intersection(envelop_union).simplify(min_volume=0.1)
        if not new_cell.shape.is_empty():
            envelopes_cells.append(new_cell)

    # len(envelopes_cells), len(upp08)
    new_universe = mk.Universe(envelopes_cells, name_rule="clash")

    # envelopes_cells_names: tp.List[int] = list(map(mk.Body.name, envelopes_cells))
    #
    # print(envelopes_cells_names)

    Path.mkdir(intersection_path.parent, parents=True, exist_ok=True)
    new_universe.save(intersection_path)


# component_to_cell_map: tp.Dict[str, Set[int]] = dict()
# names_of_cells_with_materials: tp.Set[int] = {c.name() for c in envelopes_cells if c.material()}


# @click.command()
# @click.option(
#     "--output", "-o", default=None, help="Output directory, default: <source>.universes"
# )
# @click.argument(
#     "source", metavar="<source>", type=click.Path(exists=True), nargs=-1, required=True
# )
def cli():
    files = glob("mcnp-rotated/*.i")
    for f in files:
        intersect(up08, f)


if __name__ == "__main__":
    cli()
