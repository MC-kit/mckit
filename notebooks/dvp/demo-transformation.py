# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
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

# %% [markdown]
# # Rotation matrix demo
#
# Rotation matrix is defined by coordinates of new axes orts $[e_{x}', e_y', e_z']$, which present coordinates of the new orts in the original one: $[e_x, e_y, e_z]$.
# Rotation of a given vector $v=[v_x,v_y, v_z]$ in original coordinates, means linear combination of $v_x \cdot e_x' + v_y \cdot e_y' + v_z \cdot e_z' $.
#
# The new orts form columns of the rotation matix in C-format for usuage in numpy-like code.
#
# MCNP uses Fortran presentation in the transformation specs. 
#
# So, for the MCNP specification the transformation matrix should be saved as transposed, and transposed back on reading.
#

# %%
import sys

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
r4 @ [-1, -1, 0]

# %%
tr = Transformation(rotation=r4)

# %%
tr.apply2point([1, 0, 0])


# %%
def print_transformation(tr: Transformation, out = sys.stdout) -> None:
    t = np.array(tr.get_words()).reshape((4,6))
    for r in t:
        print("   ", *(x.rjust(6) for x in r if x != " "), file=out)
        


# %%
print_transformation(tr)

# %% [raw]
# ## Some adhoc computations
#
# rotate by 11.25 degree counter clockwise

# %%
print_transformation(Transformation(rotation=calc_z_rotation(11.25*np.pi/180.0)))


# %%
def print_xy_basis(angle):
    t = calc_z_rotation(angle*np.pi/180)
    print(*("{:.7g}".format(t) for t in t.ravel()[:-3]))


# %%
print_xy_basis(22.5 + 11.25)

# %%

# %%
