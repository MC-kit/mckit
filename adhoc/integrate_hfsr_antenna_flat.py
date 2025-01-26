""""""

# import matplotlib.pyplot as plt
# import seaborn as sb
# import pandas as pd
# import numpy as np
# import scipy as sp
# import scipy.constants as sc
import typing as tp

from typing import NoReturn

import os
import sys

# from multiprocessing.pool import ThreadPool
# from multiprocessing.dummy import Pool as ThreadPool
from functools import reduce
from multiprocessing import Pool

import dotenv
import numpy as np

from mckit.utils import check_if_all_paths_exist, get_root_dir

# from joblib import (
#     Memory,
#     # Parallel, delayed, wrap_non_picklable_objects, effective_n_jobs
# )


sys.path.append("..")

import mckit as mk

from mckit.box import Box
from mckit.cli._logging import logger as LOG


def select_from(cell: mk.Body, to_select: np.ndarray) -> bool:
    name: int = cell.name()
    index: int = to_select.searchsorted(name)
    return index < to_select.size and to_select[index] == name


dotenv.load_dotenv(dotenv_path=".env", verbose=True)
HFSR_ROOT = get_root_dir("HFSR_ROOT", "~/dev/mcnp/hfsr")
CMODEL_ROOT = get_root_dir("CMODEL_ROOT", "~/dev/mcnp/c-model")
LOG.info("HFSR_ROOT=%s", HFSR_ROOT)
LOG.info("CMODEL_ROOT=%s", CMODEL_ROOT)
check_if_all_paths_exist(HFSR_ROOT, CMODEL_ROOT)
universes_dir = CMODEL_ROOT / "simple_cubes.universes"
# assert universes_dir.is_dir()
NJOBS = os.cpu_count()
# print(f"NJOBS: {NJOBS}")
# set_loky_pickler()


class BoundingBoxAdder:
    def __init__(self, tolerance: float):
        self.tolerance = tolerance

    def __call__(self, cell: mk.Body):
        box = cell.shape.bounding_box(tol=self.tolerance)
        if not isinstance(box, Box):
            box = Box.from_geometry_box(box)
        return box

    def __getstate__(self):
        return self.tolerance

    def __setstate__(self, state):
        self.__init__(state)


def attach_bounding_boxes(
    cells: tp.List[mk.Body], tolerance: float = 10.0, chunksize=1
) -> NoReturn:
    assert 0 < len(cells), "Needs explicit list of cells to run iteration over it twice"
    cpu_count = os.cpu_count()
    with Pool(cpu_count) as pool:
        boxes = pool.map(BoundingBoxAdder(tolerance), cells, chunksize)
    for _i, cell in enumerate(cells):
        cell.bounding_box = boxes[_i]


# def attach_bounding_boxes(model: mk.Universe, tolerance: float = 1.0) -> tp.NoReturn:
#     boxes = Parallel(n_jobs=NJOBS, backend='multiprocessing')(
#         delayed(compute_bounding_box)(c.shape, tolerance) for c in model
#     )
#     for _i, cell in enumerate(model):
#         cell.bounding_box = boxes[_i]


# mem = Memory(location=".cache", verbose=2)


# @mem.cache
def load_model(path: str) -> mk.Universe:
    # The cp1251-encoding reads C-model with various kryakozyabrs
    model: mk.Universe = mk.read_mcnp(path, encoding="Cp1251")
    return model


def load_filler(universe_name):
    universe_path = universes_dir / f"u{universe_name}.i"
    LOG.info(f"Loading filler {universe_name}")
    universe = load_model(universe_path)
    universe.rename(name=universe_name)
    return universe


def subtract_model_from_model(
    minuend: mk.Universe,
    subtrahend: mk.Universe,
    cells_filter: tp.Callable[[mk.Body], bool] = None,
) -> mk.Universe:
    def mapper(a_cell):
        if cells_filter is None or cells_filter(a_cell.name()):
            return subtract_model_from_cell(a_cell, subtrahend, simplify=True)
        else:
            return a_cell

    new_cells = list(map(mapper, minuend))
    new_universe = mk.Universe(new_cells, name=minuend.name(), name_rule="keep")
    return new_universe


def subtract_model_from_cell(cell: mk.Body, model: mk.Universe, simplify: bool = True) -> mk.Body:
    new_cell = cell
    cbb = cell.bounding_box
    for b_cell in model:
        if cbb.check_intersection(b_cell.bounding_box):
            comp = b_cell.shape.complement()
            new_cell = new_cell.intersection(comp)
    if new_cell is not cell:
        if simplify:
            new_cell = new_cell.simplify(box=cbb, min_volume=0.1)
    return new_cell


def set_common_materials(*universes) -> None:
    universes_collection = reduce(set.union, map(mk.Universe.get_universes, universes))
    common_materials = reduce(set.union, map(mk.Universe.get_compositions, universes_collection))
    for u in universes_collection:
        u.set_common_materials(common_materials)


def main():
    # new_cells.extend(b_model)
    LOG.info("Loading antenna envelop")
    antenna_envelop = load_model(str(HFSR_ROOT / "models/antenna/box.i"))
    LOG.info("Attaching bounding boxes to antenna envelop")
    attach_bounding_boxes(
        antenna_envelop,
        tolerance=5.0,
        chunksize=max(len(antenna_envelop) // os.cpu_count(), 1),
    )
    LOG.info("Loading c-model envelopes")
    envelopes = load_model(str(CMODEL_ROOT / "simple_cubes.universes/envelopes.i"))

    cells_to_fill = [11, 14, 75]
    cells_to_fill_indexes = [c - 1 for c in cells_to_fill]

    LOG.info("Attaching bounding boxes to c-model envelopes %s", cells_to_fill)
    attach_bounding_boxes([envelopes[i] for i in cells_to_fill_indexes], tolerance=5.0, chunksize=1)
    # attach_bounding_boxes((envelopes), tolerance=10.0, chunksize=5)
    LOG.info("Backing up original envelopes")
    envelopes_original = envelopes.copy()

    antenna_envelop.rename(start_cell=200000, start_surf=200000)

    LOG.info("Subtracting antenna envelop from c-model envelopes %s", cells_to_fill)
    envelopes = subtract_model_from_model(
        envelopes, antenna_envelop, cells_filter=lambda c: c in cells_to_fill
    )
    LOG.info("Adding antenna envelop to c-model envelopes")
    envelopes.add_cells(antenna_envelop, name_rule="clash")
    envelopes_path = "envelopes+antenna-envelop.i"
    envelopes.save(envelopes_path)
    LOG.info("The envelopes are saved to %s", envelopes_path)

    # def load_subtracted_universe(universe_name):
    #     new_universe_path = Path(f"u{universe_name}-ae.i")
    #     if new_universe_path.exists():
    #         LOG.info(f"Loading filler {universe_name}")
    #         universe = load_model(new_universe_path)
    #     else:
    #         st = time.time()
    #         universe_path = universes_dir / f"u{universe_name}.i"
    #         LOG.info("Subtracting antenna envelope from the original filler %s", universe_name)
    #         universe: mk.Universe = mk.read_mcnp(universe_path, encoding="cp1251")
    #         LOG.info("Size %d", len(universe))
    #         attach_bounding_boxes(
    #             universe,
    #             tolerance=100.0,
    #             chunksize=max(len(universe) // os.cpu_count(), 1),
    #         )
    #         et = time.time()
    #         LOG.info(f"Elapsed time on attaching bounding boxes: %.2f min", (et - st)/60)
    #         st = time.time()
    #         universe = subtract_model_from_model(universe, antenna_envelop)
    #         et = time.time()
    #         LOG.info(f"Elapsed time on subtracting filler %d, : %.2f min", universe_name, (et - st)/60)
    #         for c in universe._cells:
    #             del c.options['comment']
    #         universe.rename(name=universe_name)
    #         universe.save(str(new_universe_path))
    #         LOG.info("Universe %d is saved to %s", universe_name, new_universe_path)
    #     return universe
    #
    #
    # universes = list(map(load_subtracted_universe, cells_to_fill))

    universes = list(map(load_filler, cells_to_fill))
    antenna = load_model(HFSR_ROOT / "models/antenna/antenna.i")
    antenna.rename(210000, 210000, 210000, 210000, name=210)

    for i, filler in zip(cells_to_fill_indexes, universes):
        envelopes[i].options["FILL"] = {"universe": filler}

    added_cells = len(antenna_envelop)
    for c in envelopes[-added_cells:]:
        c.options["FILL"] = {"universe": antenna}

    set_common_materials(envelopes)

    # def delete_subtracted_universe(universe_name):
    #     new_universe_path = Path(f"u{universe_name}-ae.i")
    #     new_universe_path.unlink()
    # foreach(delete_subtracted_universe, cells_to_fill)

    envelopes_surrounding_and_antenna_file = "ewfa_3.i"
    envelopes.save(envelopes_surrounding_and_antenna_file)
    LOG.info(
        'c-model envelopes integrated with universes and antenna is saved to "%s"',
        envelopes_surrounding_and_antenna_file,
    )


if __name__ == "__main__":
    main()
