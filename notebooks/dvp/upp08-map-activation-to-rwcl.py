# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: mckit
#     language: python
#     name: mckit
# ---

# %% [markdown]
# # Extract results of activation computations for UPP08 to RWCL
#
# Dmitry Portnov, Sep 2021
#
# ## Goals and input data
#
# Extract data from "component_to_cell.json" and form a table of values corresponding to RWCL "Radwaste_Checklist_UPP08.xlsx" and "Radwaste_Checklist_UP08_ISS_PCSS.xlsx"
# The component to cell mapping "component-to-cell-4.json" is used.
#
# Al the files are in the same folder on 10.106.203.11: "d:\dvp\dev\mcnp\upp\wrk\up08".
#
#
# ## Scenario
#
# - Load data from json as map RWCL item -> list of cells in the MCNP model
# - Load activation data as map cell -> activation values for 12 day of cooliing
#
#

# %%
# %config Completer.use_jedi = False

# %%
import typing as tp
from typing import Dict

# %%
import os, sys

# %%
try:
    import matplotlib as mpl
except ImportError:
    # !pip install matplotlib
    import matplotlib as mpl

import matplotlib.pyplot as plt
# %matplotlib inline

# %%
import json
import pathlib

from collections import defaultdict
from pathlib import Path
from pprint import pprint, pformat


# %%
import numpy as np
import dotenv
from tqdm import tqdm

# %%
try:
    import pandas as pd
except ImportError:
    # !pip install pandas
    import pandas as pd

# %%
try:
    import openpyxl
except ImportError:
    # !pip install openpyxl
    import openpyxl

# %%
import mckit as mc
import r2s_rfda as r2s
import r2s_rfda.fetch as r2sft
import r2s_rfda.utils as r2sut
import r2s_rfda.launcher as r2sln

# from r2s_rfda.fetch import load_result_config, load_data, load_result_config
# from r2s_rfda import utils
# from r2s_rfda.launcher import load_config


# %%
# If exists local ".env" file, then load it to environment.
dotenv.load_dotenv();


# %%
def all_exist(*paths: Path) -> bool:
    for p in paths: # type: Path
        if not p.exists():
            raise FileNotFoundError(p)
def all_are_files(*paths: Path) -> bool:
    return all(map(Path.is_file, paths))
def all_are_dirs(*paths: Path) -> bool:
    return all(map(Path.is_dir, paths))



# %%
ROOT: Path = Path(os.getenv("UP08_ACT_ROOT", r'd:\dvp\dev\mcnp\upp\wrk\up08'))
r2swrk: Path = ROOT / "r2s"
component_to_cell_json: Path = ROOT / "component-to-cell-4.json"
rwclinput: Path = ROOT / "Radwaste_Checklist_UPP08.xlsx"
rwclinput_iss: Path = ROOT / "Radwaste_Checklist_UP08_ISS_PCSS.xlsx"
inp_keys_json = ROOT / "inp-keys.json"
all_exist(ROOT, r2swrk, component_to_cell_json, rwclinput, rwclinput_iss, inp_keys_json)
assert all_are_dirs(ROOT, r2swrk)
assert all_are_files(component_to_cell_json, rwclinput, rwclinput_iss, inp_keys_json)


# %% [markdown]
# ## Load RWCL->cells mapping from JSON

# %%
with component_to_cell_json.open() as fid:
    component_to_cell = json.load(fid)
pprint(sorted(component_to_cell.keys()))

# %%
with inp_keys_json.open(encoding="utf8") as fid:
    inp_keys = json.load(fid)
# pprint(sorted(inp_keys.keys()))
pprint(inp_keys)

# %% [markdown]
# ## Load Cell->activation data mapping from R2S working folder

# %%
r2s_launch_conf = r2sln.load_config(r2swrk)
r2s_result_conf = r2sft.load_result_config(r2swrk)

# %%
time = r2sut.convert_time_literal('12d')
time_labels = list(sorted(r2s_result_conf['gamma'].keys()))
time += time_labels[r2s_launch_conf['zero']]
closest_lab = r2sut.find_closest(time, time_labels)
# closest_lab

# %%
r2s_result_conf.keys()

# %%
activation_paths = r2s_result_conf["activity"]
activation_paths
act_data = r2sft.load_data(r2swrk / activation_paths[closest_lab])

# %%
# Estimate correction factor for tqdm progressbar total value.
its=80625951000
its/act_data._data.nnz

# %%
tqdm_correction = 6400


# %%
def load_cell_activity(cell_excel_path: Path):
    if cell_excel_path.exists():
        cell_activity_df = pd.read_excel(cell_excel_path, sheet_name="activity", index_col=0)
    else:
        cell_activity = defaultdict(float)
        with tqdm(total=act_data._data.nnz * tqdm_correction) as pbar:
            for cnt, ((g, c, i, j, k), act) in enumerate(act_data.iter_nonzero()):
                cell_activity[c] += act
                #print(act_data.gbins[g], c, i, j, k, act)
                #i += 1
                #if i == 1000:
                #    break
                if cnt % 1000 == 0:
                    pbar.update(cnt)
        cell_excel_path.parent.mkdir(parents=True, exist_ok=True)
        index = np.array(sorted(cell_activity.keys()), dtype=np.int32)
        data  = np.fromiter((cell_activity[k] for k in index), dtype=float)
        cell_activity_df = pd.DataFrame(data, columns=["activity"], index=index)
        with pd.ExcelWriter(cell_excel_path, engine="openpyxl") as excel:
            cell_activity_df.to_excel(excel, sheet_name="activity")
    return cell_activity_df



# %%
def load_cell_nuclide_activity(cell_excel_path: Path, act_data, nuclide: str):
    label = nuclide + " activity"
    loaded_from_cache = False
    if cell_excel_path.exists():
        try:
            cell_activity_df = pd.read_excel(cell_excel_path, sheet_name=label, index_col=0)
            loaded_from_cache = True
        except ValueError:
            loaded_from_cache = False

    if not loaded_from_cache:
        nuclide_idx = np.searchsorted(act_data.gbins, nuclide)
        assert act_data.gbins[nuclide_idx] == nuclide
        cell_activity = defaultdict(float)
        with tqdm(total=act_data._data.nnz * tqdm_correction) as pbar:
            for cnt, ((g, c, i, j, k), act) in enumerate(act_data.iter_nonzero()):
                if nuclide_idx == g:
                    cell_activity[c] += act
                if cnt % 1000 == 0:
                    pbar.update(cnt)
        cell_excel_path.parent.mkdir(parents=True, exist_ok=True)
        index = np.array(sorted(cell_activity.keys()), dtype=np.int32)
        data  = np.fromiter((cell_activity[k] for k in index), dtype=float)
        cell_activity_df = pd.DataFrame(data, columns=["activity"], index=index)
        with pd.ExcelWriter(cell_excel_path, engine="openpyxl", mode="w") as excel:
            cell_activity_df.to_excel(excel, sheet_name=label)
    return cell_activity_df



# %%
cell_activity_df = load_cell_activity(Path.cwd().parent.parent / "wrk/up08/cell_data.xlsx")
cell_activity_df

# %%
cell_h3_activity_df = load_cell_nuclide_activity(Path.cwd().parent.parent / "wrk/up08/cell_h3_activity.xlsx", act_data, "H3")
cell_h3_activity_df

# %% [markdown]
# ## In-vessel components

# %%
rwclinput

# %%
rwclinput_df = pd.read_excel(rwclinput, sheet_name="UPP02", header=0, usecols=[2,3], index_col=0).iloc[3:]  # Yes, UPP02 for UPP08
rwclinput_df

# %%
mass_column = rwclinput_df.columns[0]


# %%
def fix_mass_values(row):
    mass_text = row[mass_column]
    mass = float(mass_text.split()[0])
    row[mass_column] = mass


# %%
in_vessel_components = rwclinput_df.copy()
in_vessel_components.apply(fix_mass_values, axis=1)
in_vessel_components.rename(columns={mass_column: "Mass, kg"}, inplace=True)
in_vessel_components

# %%
in_vessel_components["Activity, Bq"] = np.zeros(len(in_vessel_components.index), dtype=float)
in_vessel_components["H3 Activity, Bq"] = np.zeros(len(in_vessel_components.index), dtype=float)


# %%
def collect_cells_map(rwcl_key, inp_key_map, component_to_cell_map) -> tp.Optional[Dict[int, float]]:
    keys_in_cell_map = inp_key_map[rwcl_key]
    if keys_in_cell_map:
        cell_fraction_map = defaultdict(float)
        for k in keys_in_cell_map:
            if "Взять" in k:
                print(f"Warning: use data for UP02 for RWCL id \"{rwcl_key}\"")
            else:
                cells_fraction_map_for_key = component_to_cell_map[k]
                if cells_fraction_map_for_key:
                    for k, v in cells_fraction_map_for_key.items():
                        cell_fraction_map[int(k)] += v
        for k, v in cell_fraction_map.items():
            if 1.0 < v:
                print(f"Warning: ramp down fraction owverflow in cell {k}: {v:.3g}")
                cell_fraction_map[k] = 1.0
        return cell_fraction_map
    else:
        print(f"Warning: cannot find mapping for RWCL id \"{rwcl_key}\"")
        return None


# %%
def compute_activity(cell_fraction_map: Dict[int, float], cell_activity: pd.DataFrame) -> float:

    def mapper(pair: tp.Tuple[int, float]) -> float:
        cell, fraction = pair
        assert isinstance(cell, int), f"Integer cell number is expected, {cell} is found"
        try:
            result = cell_activity.loc[cell].activity * fraction
        except KeyError:
            print(f"Warning: cannot find cell {cell} in cell activity data")
            result = 0.0
        return result

    return sum(map(mapper, cell_fraction_map.items()))


# %%
for rwclid in in_vessel_components.index:
    cell_fraction_map = collect_cells_map(rwclid, inp_keys, component_to_cell)
    if cell_fraction_map is not None:
        activity = compute_activity(cell_fraction_map, cell_activity_df)
        in_vessel_components.loc[rwclid, ["Activity, Bq"]] = activity
    else:
        print(f"Warning: cannot find activity for RWCL component \"{rwclid}\"")

# %%
in_vessel_components

# %%
cell_h3_activity_df.rename(columns={"H3 activity":"activity"}, inplace=True)

# %%
for rwclid in in_vessel_components.index:
    cell_fraction_map = collect_cells_map(rwclid, inp_keys, component_to_cell)
    if cell_fraction_map is not None:
        activity = compute_activity(cell_fraction_map, cell_h3_activity_df)
        in_vessel_components.loc[rwclid, ["H3 Activity, Bq"]] = activity
    else:
        print(f"Warning: cannot find activity for RWCL component \"{rwclid}\"")

# %%
in_vessel_components["Unit Activity, Bq/kg"] = in_vessel_components["Activity, Bq"] / in_vessel_components["Mass, kg"]
in_vessel_components["Unit H3 Activity, Bq/kg"] = in_vessel_components["H3 Activity, Bq"] / in_vessel_components["Mass, kg"]
in_vessel_components


# %%
def create_msg(row):
#     print("Row:", row)
    activity = row["Activity, Bq"]
    unit_activity = row["Unit Activity, Bq/kg"]
    h3_activity = row["H3 Activity, Bq"]
    unit_h3_activity = row["Unit H3 Activity, Bq/kg"]
    if activity > 0.0:
        return f"Activity {activity:.2g} Bq\n({unit_activity:.2g}, Bq/kg),\nH3 Activity {h3_activity:.2g} Bq\n({unit_h3_activity:.2g}, Bq/kg)"
    else:
        return ""


# %% [markdown]
# ## Interpolate missed values in in-vessel components.
#
# "Generic Screws (50 pieces)", "PP Generics (pads, skids, gripping - 8 pieces)","PP Tubes"  - unit values as for "PP Structure", totals proportional to masses
#

# %%
def update_missed_components(df, refkey, missed_keys):
    unit_activity = df.loc[refkey, ["Unit Activity, Bq/kg"]].values[0]
    unit_h3_activity = df.loc[refkey, ["Unit H3 Activity, Bq/kg"]].values[0]
    df.loc[missed_keys, ["Unit Activity, Bq/kg"]] =  unit_activity
    df.loc[missed_keys, ["Unit H3 Activity, Bq/kg"]] = unit_h3_activity
    masses = df.loc[missed_keys, ["Mass, kg"]].values
    df.loc[missed_keys, ["Activity, Bq"]] = unit_activity * masses
    df.loc[missed_keys, ["H3 Activity, Bq"]] = unit_h3_activity * masses
    return df.loc[missed_keys]


# %%
def update_missed_pp_components():
    missed_keys = ["Generic Screws (50 pieces)", "PP Generics (pads, skids, gripping - 8 pieces)","PP Tubes"]
    refkey = "PP structure"
    return update_missed_components(in_vessel_components, refkey, missed_keys)

update_missed_pp_components()

# %%
in_vessel_components

# %%
in_vessel_components["Radiological data"] = in_vessel_components.apply(create_msg, axis=1)

# %%
with pd.ExcelWriter(ROOT / "in-vessel.xlsx", engine="openpyxl", mode="w") as excel:
    in_vessel_components.to_excel(excel, sheet_name="result")

# %% [markdown]
# ## Inter space components

# %%
rwclinput_iss_df = pd.read_excel(rwclinput_iss, sheet_name="UPP02", header=0, usecols=[2,3], index_col=0).iloc[3:]  # Yes, UPP02 for UPP08
rwclinput_iss_df

# %%
iss_components = rwclinput_iss_df.copy()
iss_components.rename(columns={mass_column: "Mass, kg"}, inplace=True)
iss_components

# %%
with (ROOT / "component_to_cell_keys.txt").open("w") as stream:
    for key in sorted(component_to_cell.keys()):
        print(key, file=stream)

# %%
with (ROOT / "iss_rwcl_keys.txt").open("w") as stream:
    for i in iss_components.index:
        print(i, file=stream)

# %% [markdown]
# Ждем mapping от Ромы, продолжить отсюда...

# %%
inp1 = set(rwclinput_df.index.values)
inp2 = set(rwclinput_iss_df.index.values)
available = set(djson.keys())

# %%
sorted(inp1), sorted(inp2), sorted(available)

# %%
inp1.intersection(available)

# %%
inp2.intersection(available)


# %%
def calc_rwcl_item_activity(cell_activity_df: pd.DataFrame, djson: Dict[str, int]) -> tp.Tuple[Dict[str, float], Dict[str, tp.List[int]]]:
    missed_items_cells = defaultdict(list)
    rwcl_item_activity = defaultdict(float)
    for i, (k, v) in enumerate(djson.items()):
        for c in v:
            if c in cell_activity_df:
                rwcl_item_activity[k] += cell_activity_df.loc[c]
            else:
                missed_items_cells[k].append(c)
    return rwcl_item_activity, missed_items_cells


# %%
rwcl_item_activity, missed_items_cells = calc_rwcl_item_activity(cell_activity_df, djson)

# %%
rwcl_item_activity

# %%

# %% [markdown]
# ## Map RWCL items to activity value

# %%
# missed_items_cells

# %%
# sorted(rwcl_item_activity.keys())

# %%
# 6                       Side plate #1-18 (18 pieces)
# 17                                    Frame Blade #9
# 18                              DSM Rails (2 pieces)
# 19                                          PP Tubes
# 20    PP Generics (pads, skids, gripping - 8 pieces)
# 22                        Generic Screws (50 pieces)
# 34              Rear box shielding plates (8 pieces)
# 35                                          Manifold
# Name: Equipment part (see 4.1), dtype: object

rwcl2json = {
 "Frame Blade #1": 'Frame1',
 "Frame Blade #2": 'Blade2',
 "Frame Blade #3": 'Blade3',
 "Frame Blade #4": 'Blade4',
 "Frame Blade #5": 'Blade5',
 "Frame Blade #6": 'Blade6',
 "Frame Blade #7": 'Blade7',
 "Frame Blade #8": 'Blade8',
 "DFW Left": 'DFW_left',
 "DFW Right": 'DFW_right',
#  'DMS_front',
#  'DMS_rear',
 "DSM": ['DSM','DSM_down', 'DSM_up'],

 "PP structure": [
     'Flange',
     'Flange_ext',
     'Trapezoid',
     'Rear_box',
 ]

 "Frame Bottom": 'Frame_bottom',
 "Frame Top": 'Frame_top',
# 'GDC',
 'Interspace_left_block',
 'Interspace_left_frame',
 'Interspace_lower_shielding',
 'Interspace_right_block',
 'Interspace_right_frame',
 'Interspace_top_frame',
 'Mount_bottom',
 'Mount_left',
 'Mount_right',
 'Mount_up',
#  'Reflectometer_left',
#  'Reflectometer_rear',
#  'Reflectometer_right',
 "Rear frame shielding1": 'Shielding1',
#  "Rear frame shielding10": ,
 "Rear frame shielding2": 'Shielding2',
 "Rear frame shielding3": 'Shielding3',
 "Rear frame shielding4": 'Shielding4',
 "Rear frame shielding5": 'Shielding5',
 "Rear frame shielding6": 'Shielding6',
 "Rear frame shielding7": 'Shielding7',
 "Rear frame shielding8": 'Shielding8',
 "Rear frame shielding8": 'Shielding_segment_9',
 "Rear box shielding (left)": 'Shielding_rear_left',
 "Rear box shielding (rightt)": 'Shielding_rear_right',
#  'Vis_exvessel',
#  'Visir_flange',
#  'Visir_invessel',
]

# %%
activation_column = np.zeros(len(rwclout_keys), dtype=float)

for i, key in enumerate(rwclout_keys):
    if key is np.NaN:
        activation_column[i] = np.NaN
    else:
        activity = rwcl_item_activity.get(key, None)
        if activity is None:
            print(f"No data for component {i} {key}")
            activation_column[i] = np.NaN
        else:
            activation_column[i] = activity

activation_column

# %%
rwclinput_df = pd.read_excel(rwclinput, sheet_name="UPP02", engine="openpyxl")   # Yes, sheet name is "UPP02" in file for UP08 RWCL

# %%
rwclout_keys = rwclinput_df[rwclinput_df.columns[2]]

# %%
rwclout_keys
