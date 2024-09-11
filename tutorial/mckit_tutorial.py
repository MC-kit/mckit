# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from __future__ import annotations

from mckit import Body, Composition, Material, Shape, Universe, create_surface, from_file

# %% [markdown]
# ### Read MCNP input file
#
# read_mcnp function reads MCNP input file and returns Universe instance. Universe instance contains _cell variable, list of cells.

# %%
model1 = from_file("test1.i").universe
type(model1)

# %%
model1.name()

# %% [markdown]
# It is possible to iterate over universe entities. Entities of inner universes are not included.

# %%
for cell in model1:
    print(cell.mcnp_repr())

# %% [markdown]
# #### Get all universes

# %%
universes = model1.get_universes()
udict = {}
for u in universes:
    udict[u.name()] = u
    print("name: ", u.name(), "The number of cells: ", len(u))

# %%
cell_1 = udict[0]._cells[0]
print(cell_1.mcnp_repr())

# %%
surfaces = cell_1.shape.get_surfaces()
for s in surfaces:
    print(s.mcnp_repr())

# %% [markdown]
# Surfaces 4, 5 and 6 are redundant. To simplify cell description *simplify* method can be used.

# %%
print(cell_1.simplify.__doc__)

# %%
cell_1s = cell_1.simplify(min_volume=1.0e-3)
print(cell_1s.mcnp_repr())

# %% [markdown]
# To flatten mcnp model *apply_fill* method of Universe can be used. It modifies current universe: inserts all cells of inner universes. But *simplify* method must be called separately.

# %%
for c in model1:
    print(c.mcnp_repr())

# %%
model1.apply_fill()
for c in model1:
    print(c.mcnp_repr())

# %%
model1.simplify(min_volume=1.0e-3)

# %%
for c in model1:
    print(c.mcnp_repr())

# %%
model1.save("test_flattened.i")

# %%
surfaces = model1.get_surfaces()
for s in surfaces:
    print(s.mcnp_repr())

# %% [markdown]
# Now cut a sphere of radius 4 cm from the model1.

# %%
sphere = create_surface("SO", 4, name=20)

# %%
new_cells = []  # new cells
mask_shape = Shape("S", sphere)  # mask shape: only intersections with mask shape will
# be presented in new model
for c in model1:
    nc = c.intersection(mask_shape)  # get intersection cell
    nc = nc.simplify(min_volume=0.1)  # simplify intersection cell.
    new_cells.append(nc)  # append truncated cell to cell list.
new_cells.append(Body(Shape("C", sphere), name=20))  # finally append new body, which is
# the sphere.
new_u = Universe(new_cells)  # And create new universe.

# %%
new_u.simplify(min_volume=0.1)

# %%
new_u.save("test_cut.i")

# %%
cell_1.material()

# %% [markdown]
# ## Insert cells with material

# %%
to_insert = from_file("to_insert.i").universe

# %%
new_cells = list(iter(model1))
ext_cells = []
for add_c in to_insert:
    if add_c.material():
        comp = add_c.shape.complement()
        for i, c in enumerate(new_cells):
            new_cells[i] = c.intersection(comp)
        ext_cells.append(add_c)
new_cells.extend(ext_cells)
comb_u = Universe(new_cells, name_rule="clash")

# %%
comb_u.simplify(min_volume=0.01)

# %%
comb_u.save("combine.i")

# %% [markdown]
# # Material manipulation

# %%
comp = Composition(atomic=[("H", 2), ("O", 1)], name=1, comment="Material 1")
print(comp.mcnp_repr())

# %%
comp_e = comp.expand()  # Get isotope composition
print(comp_e.mcnp_repr())

# %%
water = Material(comp, density=1.0)

# %%
oil = Material(atomic=[("C", 1), ("H", 2)], density=0.8)

# %%
mix = Material.mixture((water, 0.4), (oil, 0.6), fraction_type="weight")

# %%
print(mix.density)
mix.composition.options["name"] = 3
print(mix.composition.mcnp_repr())
