from __future__ import annotations

from mckit.material import Material

# for testing _get_material function purposes
materials = [
    Material(atomic=[(1000, 2), (8000, 1)], density=0.9982),
    Material(atomic=[(1000, 2), (8000, 1)], density=0.1),
]

densities = [
    (-0.9982, materials[0]),
    (-0.1, materials[1]),
    (-2.0, None),
    (-0.9984, None),
    (-0.9980, None),
    (1.0010337342849073e23, materials[0]),
    (1.0028388442044753e22, materials[1]),
    (1.0012337342849073e23, None),
    (1.0098337342849073e23, None),
    (-0.99825, materials[0]),
    (-0.99815, materials[0]),
]

compositions = {
    1: {"atomic": [(1000, 2), (8000, 1)]},
    2: {"atomic": [("Si", 1), ("O", 2)]},
    3: {"wgt": [("N", 75.5), ("O", 23.15), ("Ar", 1.292)]},
}

cells = {
    1: {},
    2: {"MAT": 2, "RHO": -2.6500},
    3: {"MAT": 1, "RHO": -0.9982},
    4: {},
    5: {"MAT": 3, "RHO": -1.247e-3},
    6: {"MAT": 2, "RHO": -2.6500},
    7: {"MAT": 2, "RHO": -2.6501},
    8: {"MAT": 1, "RHO": -0.9982},
    9: {"MAT": 2, "RHO": -1.3500},
    10: {"MAT": 2, "RHO": -1.3500},
    11: {"MAT": 1, "RHO": -0.9982},
    12: {"MAT": 3, "RHO": -1.247e-4},
}

mat_cell_ans = {0: [1, 4], 1: [[3, 8, 11]], 2: [[2, 6, 7], [9, 10]], 3: [[5], [12]]}
