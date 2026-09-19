# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Вставить модель НГ-24М в C-model
#
# ## Change log
#
# ### v0.0.2 dvp - check materials list change
#
# Some material are not found in the integrated model (m303 for instance)…
# In the original model ( initial/C-model-dnfm-geom.i) the m303 is in the component
# of `BM01_C03`, cells 127000..127009 and some others.
#

# %%
from pathlib import Path

import mckit as mc

# %%
print(mc.__version__)

# %% [markdown]
# ## Load initial models

# %%
folder = Path('initial')
assert folder.is_dir()

# %%
cmodel_path = folder / 'C-model-dnfm-geom.i'
ng_path = folder / 'ng-24m-v5-geom-trans.i'       ## without outer-cell

# %%
cmodel_info = mc.from_file(cmodel_path)
cmodel = cmodel_info.universe


# %%
print("Number of envelop cells in C-model:", len(cmodel))

# %%
ng_info = mc.from_file(ng_path)
ng = ng_info.universe

common_materials = set(cmodel_info.compositions_index.values()) | set(ng_info.compositions_index.values())


# %%
cell_127000: mc.Body = cmodel_info.cells_index[127000]

# %%
print(cell_127000.material().composition.name())

# %% [markdown]
# ## Integration

# %%
new_cells = []

for bc in cmodel:
    bc_id = bc.name()
    print("Working on", bc_id)
    bc_new = bc
    if bc_id == 1: # the plasma cell is the only one affected with NG insertion
        for c in ng:
            c_int = bc_new.intersection(c).simplify(min_volume = 1e-3)
            if not c_int.shape.is_empty():
                print("    Intersection with cell", c.name())
                bc_new = bc_new.intersection(c.shape.complement())
        if bc_new is not bc:  # changed with intersection
            bc_new = bc_new.simplify(min_volume = 1e-3)
            assert not bc_new.shape.is_empty()
    new_cells.append(bc_new)

new_cells.extend(ng._cells)
# new_u = mc.Universe(new_cells, name_rule = "clash")
new_u = mc.Universe(new_cells, name_rule = "keep", common_materials=common_materials)

# %% [markdown]
# ## Check results

# %%

# %% [markdown]
# ## Save integrate models

# %%
new_u.save('integration-result-v5.i')  # for mckit-0.8.4

# %%
print(new_u.name_clashes())

# %% [markdown]
#
