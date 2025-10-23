# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import numpy as np

# %%
from mckit import Transformation


# %%
def calc_z_rotation(theta: float):
    return np.array(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0,             0,             1],
        ],
        dtype=np.float64
    )


# %%
r4 = calc_z_rotation(np.pi/4)
r4

# %%
r4 @ [1, 0, 0]

# %%
tr = Transformation(rotation=r4)

# %%
tr.apply2point([1, 0, 0])

# %%
np.array(tr.get_words()).reshape((4,6))

# %%
180*(9/8)

# %%
r15 = calc_z_rotation((17/16)*np.pi)
r15

# %%
r15 @ [1, 0, 0]

# %%
tr15 = Transformation(rotation=r15)

# %%
tr15.apply2point([1,0,0])

# %%
np.array(tr15.get_words()).reshape((4,6))

# %%
