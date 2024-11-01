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

# %% [markdown]
# # Compute composition of boron and polyethilen
#
# dvp 2024.10.31
#
#
# Create mix of wgt5% boron and polyethilen (remaining).
#
#

# %% [markdown]
# ## Setup

# %%
import sys

from pathlib import Path

from mckit import Composition, Element, Material

# %%
print(sys.version)
print(sys.prefix)

# %%
# %config Completer.use_jedi = False

# %%
HERE = Path.cwd()
ROOT = HERE.parent.parent
dst =  ROOT / "wrk/bpe5.txt"

# %%
dst.parent.mkdir(exist_ok = True)

# %%
boron_fraction = 0.05
polyethylene_fraction = 1.0 - boron_fraction
mix_number = 170023 # free slot in up-mi-24-08-27.xlsx material index for mapstp


# %%
def mk_element(name: str):
    return Element(name, lib="31c")


# %% [markdown]
# ## Computation

# %%
boron = Composition(atomic=[(mk_element("B"), 1.0)]).expand()

# %%
boron.mcnp_repr()

# %%
polyethylene = Composition(atomic = [(mk_element("C"), 1.0), (mk_element("H"), 2.0)]).expand()

# %%
polyethylene.mcnp_repr()

# %%
bpe5 = Composition.mixture(
    (boron, boron_fraction / boron.molar_mass),
    (polyethylene, polyethylene_fraction / polyethilen.molar_mass),
).rename(mix_number)

# %%
bpe5.mcnp_repr()

# %%
dst.write_text(bpe5.mcnp_repr().replace("170023", "17023\n       "))

# %%
