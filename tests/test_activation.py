import pytest
from pathlib import Path
import os
import shutil
import numpy as np
from itertools import accumulate
import pickle

from mckit.activation import FispactError, fispact_fatal, fispact_files, \
                             fispact_convert, fispact_collapse, \
                             IrradiationProfile, activation, \
                             mesh_activation, LIBS, DATA_PATH
from mckit.material import Material
from mckit import read_meshtal, read_mcnp
from mckit.fmesh import SparseData


@pytest.mark.parametrize('text, fatal', [
    ("Arbitrary text", False),
    (" collapse:--------- FATAL ERROR ---------- run terminated, for details see runlog file, collapse.log", True),
    (" convert: --------- FATAL ERROR ---------- run terminated, for details see runlog file, convert.log", True),
    (" condense:--------- FATAL ERROR ---------- run terminated, for details see runlog file, condense.log ", True),
    (" inventory--------- FATAL ERROR ---------- run terminated, for details see runlog file, inventory.log", True),
    (" collapse: cpu time =  27.3     secs.    2 errors/warnings, for details see runlog file, collapse.log", False)
])
def test_fispact_fatal(text, fatal):
    if fatal:
        with pytest.raises(FispactError):
            fispact_fatal(text)


@pytest.mark.parametrize('input, expected_file, expected_names', [
    ({}, 'files', {'collapxi': 'COLLAPX', 'collapxo': 'COLLAPX', 'fluxes': 'fluxes', 'arrayx': 'ARRAYX'}),
    ({'files': 'files1'}, 'files1', {'collapxi': 'COLLAPX', 'collapxo': 'COLLAPX', 'fluxes': 'fluxes', 'arrayx': 'ARRAYX'}),
    ({'files': 'files2', 'fluxes': 'fluxes2', 'collapx': 'collapx2'}, 'files2', {'collapxi': 'collapx2', 'collapxo': 'collapx2', 'fluxes': 'fluxes2', 'arrayx': 'ARRAYX'}),
])
def test_files(input, expected_file, expected_names):
    expected_data = {k: DATA_PATH + v for k, v in LIBS.items()}
    expected_data.update(expected_names)
    fispact_files(**input)
    assert Path(expected_file).exists()
    with open(expected_file) as f:
        content = {}
        for line in f:
            name, value = line.split()
            content[name] = value
        assert content == expected_data
    os.remove(expected_file)


@pytest.fixture
def new_ebins():
    return [
        1.0000E+9, 9.6000E+8, 9.2000E+8, 8.8000E+8, 8.4000E+8, 8.0000E+8,
        7.6000E+8, 7.2000E+8, 6.8000E+8, 6.4000E+8, 6.0000E+8, 5.6000E+8,
        5.2000E+8, 4.8000E+8, 4.4000E+8, 4.0000E+8, 3.6000E+8, 3.2000E+8,
        2.8000E+8, 2.4000E+8, 2.0000E+8, 1.8000E+8, 1.6000E+8, 1.5000E+8,
        1.4000E+8, 1.3000E+8, 1.2000E+8, 1.1000E+8, 1.0000E+8, 9.0000E+7,
        8.0000E+7, 7.5000E+7, 7.0000E+7, 6.5000E+7, 6.0000E+7, 5.8000E+7,
        5.6000E+7, 5.4000E+7, 5.2000E+7, 5.0000E+7, 4.8000E+7, 4.6000E+7,
        4.4000E+7, 4.2000E+7, 4.0000E+7, 3.8000E+7, 3.6000E+7, 3.4000E+7,
        3.2000E+7, 3.0000E+7, 2.9000E+7, 2.8000E+7, 2.7000E+7, 2.6000E+7,
        2.5000E+7, 2.4000E+7, 2.3000E+7, 2.2000E+7, 2.1000E+7, 2.0000E+7,
        1.9800E+7, 1.9600E+7, 1.9400E+7, 1.9200E+7, 1.9000E+7, 1.8800E+7,
        1.8600E+7, 1.8400E+7, 1.8200E+7, 1.8000E+7, 1.7800E+7, 1.7600E+7,
        1.7400E+7, 1.7200E+7, 1.7000E+7, 1.6800E+7, 1.6600E+7, 1.6400E+7,
        1.6200E+7, 1.6000E+7, 1.5800E+7, 1.5600E+7, 1.5400E+7, 1.5200E+7,
        1.5000E+7, 1.4800E+7, 1.4600E+7, 1.4400E+7, 1.4200E+7, 1.4000E+7,
        1.3800E+7, 1.3600E+7, 1.3400E+7, 1.3200E+7, 1.3000E+7, 1.2800E+7,
        1.2600E+7, 1.2400E+7, 1.2200E+7, 1.2000E+7, 1.1800E+7, 1.1600E+7,
        1.1400E+7, 1.1200E+7, 1.1000E+7, 1.0800E+7, 1.0600E+7, 1.0400E+7,
        1.0200E+7, 1.0000E+7, 9.5499E+6, 9.1201E+6, 8.7096E+6, 8.3176E+6,
        7.9433E+6, 7.5858E+6, 7.2444E+6, 6.9183E+6, 6.6069E+6, 6.3096E+6,
        6.0256E+6, 5.7544E+6, 5.4954E+6, 5.2481E+6, 5.0119E+6, 4.7863E+6,
        4.5709E+6, 4.3652E+6, 4.1687E+6, 3.9811E+6, 3.8019E+6, 3.6308E+6,
        3.4674E+6, 3.3113E+6, 3.1623E+6, 3.0200E+6, 2.8840E+6, 2.7542E+6,
        2.6303E+6, 2.5119E+6, 2.3988E+6, 2.2909E+6, 2.1878E+6, 2.0893E+6,
        1.9953E+6, 1.9055E+6, 1.8197E+6, 1.7378E+6, 1.6596E+6, 1.5849E+6,
        1.5136E+6, 1.4454E+6, 1.3804E+6, 1.3183E+6, 1.2589E+6, 1.2023E+6,
        1.1482E+6, 1.0965E+6, 1.0471E+6, 1.0000E+6, 9.5499E+5, 9.1201E+5,
        8.7096E+5, 8.3176E+5, 7.9433E+5, 7.5858E+5, 7.2444E+5, 6.9183E+5,
        6.6069E+5, 6.3096E+5, 6.0256E+5, 5.7544E+5, 5.4954E+5, 5.2481E+5,
        5.0119E+5, 4.7863E+5, 4.5709E+5, 4.3652E+5, 4.1687E+5, 3.9811E+5,
        3.8019E+5, 3.6308E+5, 3.4674E+5, 3.3113E+5, 3.1623E+5, 3.0200E+5,
        2.8840E+5, 2.7542E+5, 2.6303E+5, 2.5119E+5, 2.3988E+5, 2.2909E+5,
        2.1878E+5, 2.0893E+5, 1.9953E+5, 1.9055E+5, 1.8197E+5, 1.7378E+5,
        1.6596E+5, 1.5849E+5, 1.5136E+5, 1.4454E+5, 1.3804E+5, 1.3183E+5,
        1.2589E+5, 1.2023E+5, 1.1482E+5, 1.0965E+5, 1.0471E+5, 1.0000E+5,
        9.5499E+4, 9.1201E+4, 8.7096E+4, 8.3176E+4, 7.9433E+4, 7.5858E+4,
        7.2444E+4, 6.9183E+4, 6.6069E+4, 6.3096E+4, 6.0256E+4, 5.7544E+4,
        5.4954E+4, 5.2481E+4, 5.0119E+4, 4.7863E+4, 4.5709E+4, 4.3652E+4,
        4.1687E+4, 3.9811E+4, 3.8019E+4, 3.6308E+4, 3.4674E+4, 3.3113E+4,
        3.1623E+4, 3.0200E+4, 2.8840E+4, 2.7542E+4, 2.6303E+4, 2.5119E+4,
        2.3988E+4, 2.2909E+4, 2.1878E+4, 2.0893E+4, 1.9953E+4, 1.9055E+4,
        1.8197E+4, 1.7378E+4, 1.6596E+4, 1.5849E+4, 1.5136E+4, 1.4454E+4,
        1.3804E+4, 1.3183E+4, 1.2589E+4, 1.2023E+4, 1.1482E+4, 1.0965E+4,
        1.0471E+4, 1.0000E+4, 9.5499E+3, 9.1201E+3, 8.7096E+3, 8.3176E+3,
        7.9433E+3, 7.5858E+3, 7.2444E+3, 6.9183E+3, 6.6069E+3, 6.3096E+3,
        6.0256E+3, 5.7544E+3, 5.4954E+3, 5.2481E+3, 5.0119E+3, 4.7863E+3,
        4.5709E+3, 4.3652E+3, 4.1687E+3, 3.9811E+3, 3.8019E+3, 3.6308E+3,
        3.4674E+3, 3.3113E+3, 3.1623E+3, 3.0200E+3, 2.8840E+3, 2.7542E+3,
        2.6303E+3, 2.5119E+3, 2.3988E+3, 2.2909E+3, 2.1878E+3, 2.0893E+3,
        1.9953E+3, 1.9055E+3, 1.8197E+3, 1.7378E+3, 1.6596E+3, 1.5849E+3,
        1.5136E+3, 1.4454E+3, 1.3804E+3, 1.3183E+3, 1.2589E+3, 1.2023E+3,
        1.1482E+3, 1.0965E+3, 1.0471E+3, 1.0000E+3, 9.5499E+2, 9.1201E+2,
        8.7096E+2, 8.3176E+2, 7.9433E+2, 7.5858E+2, 7.2444E+2, 6.9183E+2,
        6.6069E+2, 6.3096E+2, 6.0256E+2, 5.7544E+2, 5.4954E+2, 5.2481E+2,
        5.0119E+2, 4.7863E+2, 4.5709E+2, 4.3652E+2, 4.1687E+2, 3.9811E+2,
        3.8019E+2, 3.6308E+2, 3.4674E+2, 3.3113E+2, 3.1623E+2, 3.0200E+2,
        2.8840E+2, 2.7542E+2, 2.6303E+2, 2.5119E+2, 2.3988E+2, 2.2909E+2,
        2.1878E+2, 2.0893E+2, 1.9953E+2, 1.9055E+2, 1.8197E+2, 1.7378E+2,
        1.6596E+2, 1.5849E+2, 1.5136E+2, 1.4454E+2, 1.3804E+2, 1.3183E+2,
        1.2589E+2, 1.2023E+2, 1.1482E+2, 1.0965E+2, 1.0471E+2, 1.0000E+2,
        9.5499E+1, 9.1201E+1, 8.7096E+1, 8.3176E+1, 7.9433E+1, 7.5858E+1,
        7.2444E+1, 6.9183E+1, 6.6069E+1, 6.3096E+1, 6.0256E+1, 5.7544E+1,
        5.4954E+1, 5.2481E+1, 5.0119E+1, 4.7863E+1, 4.5709E+1, 4.3652E+1,
        4.1687E+1, 3.9811E+1, 3.8019E+1, 3.6308E+1, 3.4674E+1, 3.3113E+1,
        3.1623E+1, 3.0200E+1, 2.8840E+1, 2.7542E+1, 2.6303E+1, 2.5119E+1,
        2.3988E+1, 2.2909E+1, 2.1878E+1, 2.0893E+1, 1.9953E+1, 1.9055E+1,
        1.8197E+1, 1.7378E+1, 1.6596E+1, 1.5849E+1, 1.5136E+1, 1.4454E+1,
        1.3804E+1, 1.3183E+1, 1.2589E+1, 1.2023E+1, 1.1482E+1, 1.0965E+1,
        1.0471E+1, 1.0000E+1, 9.5499E+0, 9.1201E+0, 8.7096E+0, 8.3176E+0,
        7.9433E+0, 7.5858E+0, 7.2444E+0, 6.9183E+0, 6.6069E+0, 6.3096E+0,
        6.0256E+0, 5.7544E+0, 5.4954E+0, 5.2481E+0, 5.0119E+0, 4.7863E+0,
        4.5709E+0, 4.3652E+0, 4.1687E+0, 3.9811E+0, 3.8019E+0, 3.6308E+0,
        3.4674E+0, 3.3113E+0, 3.1623E+0, 3.0200E+0, 2.8840E+0, 2.7542E+0,
        2.6303E+0, 2.5119E+0, 2.3988E+0, 2.2909E+0, 2.1878E+0, 2.0893E+0,
        1.9953E+0, 1.9055E+0, 1.8197E+0, 1.7378E+0, 1.6596E+0, 1.5849E+0,
        1.5136E+0, 1.4454E+0, 1.3804E+0, 1.3183E+0, 1.2589E+0, 1.2023E+0,
        1.1482E+0, 1.0965E+0, 1.0471E+0, 1.0000E+0, 9.5499E-1, 9.1201E-1,
        8.7096E-1, 8.3176E-1, 7.9433E-1, 7.5858E-1, 7.2444E-1, 6.9183E-1,
        6.6069E-1, 6.3096E-1, 6.0256E-1, 5.7544E-1, 5.4954E-1, 5.2481E-1,
        5.0119E-1, 4.7863E-1, 4.5709E-1, 4.3652E-1, 4.1687E-1, 3.9811E-1,
        3.8019E-1, 3.6308E-1, 3.4674E-1, 3.3113E-1, 3.1623E-1, 3.0200E-1,
        2.8840E-1, 2.7542E-1, 2.6303E-1, 2.5119E-1, 2.3988E-1, 2.2909E-1,
        2.1878E-1, 2.0893E-1, 1.9953E-1, 1.9055E-1, 1.8197E-1, 1.7378E-1,
        1.6596E-1, 1.5849E-1, 1.5136E-1, 1.4454E-1, 1.3804E-1, 1.3183E-1,
        1.2589E-1, 1.2023E-1, 1.1482E-1, 1.0965E-1, 1.0471E-1, 1.0000E-1,
        9.5499E-2, 9.1201E-2, 8.7096E-2, 8.3176E-2, 7.9433E-2, 7.5858E-2,
        7.2444E-2, 6.9183E-2, 6.6069E-2, 6.3096E-2, 6.0256E-2, 5.7544E-2,
        5.4954E-2, 5.2481E-2, 5.0119E-2, 4.7863E-2, 4.5709E-2, 4.3652E-2,
        4.1687E-2, 3.9811E-2, 3.8019E-2, 3.6308E-2, 3.4674E-2, 3.3113E-2,
        3.1623E-2, 3.0200E-2, 2.8840E-2, 2.7542E-2, 2.6303E-2, 2.5119E-2,
        2.3988E-2, 2.2909E-2, 2.1878E-2, 2.0893E-2, 1.9953E-2, 1.9055E-2,
        1.8197E-2, 1.7378E-2, 1.6596E-2, 1.5849E-2, 1.5136E-2, 1.4454E-2,
        1.3804E-2, 1.3183E-2, 1.2589E-2, 1.2023E-2, 1.1482E-2, 1.0965E-2,
        1.0471E-2, 1.0000E-2, 9.5499E-3, 9.1201E-3, 8.7096E-3, 8.3176E-3,
        7.9433E-3, 7.5858E-3, 7.2444E-3, 6.9183E-3, 6.6069E-3, 6.3096E-3,
        6.0256E-3, 5.7544E-3, 5.4954E-3, 5.2481E-3, 5.0119E-3, 4.7863E-3,
        4.5709E-3, 4.3652E-3, 4.1687E-3, 3.9811E-3, 3.8019E-3, 3.6308E-3,
        3.4674E-3, 3.3113E-3, 3.1623E-3, 3.0200E-3, 2.8840E-3, 2.7542E-3,
        2.6303E-3, 2.5119E-3, 2.3988E-3, 2.2909E-3, 2.1878E-3, 2.0893E-3,
        1.9953E-3, 1.9055E-3, 1.8197E-3, 1.7378E-3, 1.6596E-3, 1.5849E-3,
        1.5136E-3, 1.4454E-3, 1.3804E-3, 1.3183E-3, 1.2589E-3, 1.2023E-3,
        1.1482E-3, 1.0965E-3, 1.0471E-3, 1.0000E-3, 9.5499E-4, 9.1201E-4,
        8.7096E-4, 8.3176E-4, 7.9433E-4, 7.5858E-4, 7.2444E-4, 6.9183E-4,
        6.6069E-4, 6.3096E-4, 6.0256E-4, 5.7544E-4, 5.4954E-4, 5.2481E-4,
        5.0119E-4, 4.7863E-4, 4.5709E-4, 4.3652E-4, 4.1687E-4, 3.9811E-4,
        3.8019E-4, 3.6308E-4, 3.4674E-4, 3.3113E-4, 3.1623E-4, 3.0200E-4,
        2.8840E-4, 2.7542E-4, 2.6303E-4, 2.5119E-4, 2.3988E-4, 2.2909E-4,
        2.1878E-4, 2.0893E-4, 1.9953E-4, 1.9055E-4, 1.8197E-4, 1.7378E-4,
        1.6596E-4, 1.5849E-4, 1.5136E-4, 1.4454E-4, 1.3804E-4, 1.3183E-4,
        1.2589E-4, 1.2023E-4, 1.1482E-4, 1.0965E-4, 1.0471E-4, 1.0000E-4,
        9.5499E-5, 9.1201E-5, 8.7096E-5, 8.3176E-5, 7.9433E-5, 7.5858E-5,
        7.2444E-5, 6.9183E-5, 6.6069E-5, 6.3096E-5, 6.0256E-5, 5.7544E-5,
        5.4954E-5, 5.2481E-5, 5.0119E-5, 4.7863E-5, 4.5709E-5, 4.3652E-5,
        4.1687E-5, 3.9811E-5, 3.8019E-5, 3.6308E-5, 3.4674E-5, 3.3113E-5,
        3.1623E-5, 3.0200E-5, 2.8840E-5, 2.7542E-5, 2.6303E-5, 2.5119E-5,
        2.3988E-5, 2.2909E-5, 2.1878E-5, 2.0893E-5, 1.9953E-5, 1.9055E-5,
        1.8197E-5, 1.7378E-5, 1.6596E-5, 1.5849E-5, 1.5136E-5, 1.4454E-5,
        1.3804E-5, 1.3183E-5, 1.2589E-5, 1.2023E-5, 1.1482E-5, 1.0965E-5,
        1.0471E-5
    ]


@pytest.fixture
def ebins():
    return [
        1.00000000e-11,   1.00000000e-07,   4.14000000e-07,   5.32000000e-07,
        6.83000000e-07,   8.76000000e-07,   1.13000000e-06,   1.44000000e-06,
        1.86000000e-06,   2.38000000e-06,   3.06000000e-06,   3.93000000e-06,
        5.04000000e-06,   6.48000000e-06,   8.32000000e-06,   1.07000000e-05,
        1.37000000e-05,   1.76000000e-05,   2.26000000e-05,   2.90000000e-05,
        3.73000000e-05,   4.79000000e-05,   6.14000000e-05,   7.89000000e-05,
        1.01000000e-04,   1.30000000e-04,   1.67000000e-04,   2.14000000e-04,
        2.75000000e-04,   3.54000000e-04,   4.54000000e-04,   5.83000000e-04,
        7.49000000e-04,   9.61000000e-04,   1.23000000e-03,   1.58000000e-03,
        2.03000000e-03,   2.25000000e-03,   2.49000000e-03,   2.61000000e-03,
        2.75000000e-03,   3.04000000e-03,   3.35000000e-03,   3.71000000e-03,
        4.31000000e-03,   5.53000000e-03,   7.10000000e-03,   9.12000000e-03,
        1.06000000e-02,   1.17000000e-02,   1.50000000e-02,   1.93000000e-02,
        2.19000000e-02,   2.36000000e-02,   2.42000000e-02,   2.48000000e-02,
        2.61000000e-02,   2.70000000e-02,   2.85000000e-02,   3.18000000e-02,
        3.43000000e-02,   4.09000000e-02,   4.63000000e-02,   5.25000000e-02,
        5.66000000e-02,   6.74000000e-02,   7.20000000e-02,   7.95000000e-02,
        8.25000000e-02,   8.65000000e-02,   9.80000000e-02,   1.11000000e-01,
        1.17000000e-01,   1.23000000e-01,   1.29000000e-01,   1.36000000e-01,
        1.43000000e-01,   1.50000000e-01,   1.58000000e-01,   1.66000000e-01,
        1.74000000e-01,   1.83000000e-01,   1.93000000e-01,   2.02000000e-01,
        2.13000000e-01,   2.24000000e-01,   2.35000000e-01,   2.47000000e-01,
        2.73000000e-01,   2.87000000e-01,   2.95000000e-01,   2.97000000e-01,
        2.98000000e-01,   3.02000000e-01,   3.34000000e-01,   3.69000000e-01,
        3.88000000e-01,   4.08000000e-01,   4.50000000e-01,   4.98000000e-01,
        5.23000000e-01,   5.50000000e-01,   5.78000000e-01,   6.08000000e-01,
        6.39000000e-01,   6.72000000e-01,   7.07000000e-01,   7.43000000e-01,
        7.81000000e-01,   8.21000000e-01,   8.63000000e-01,   9.07000000e-01,
        9.62000000e-01,   1.00000000e+00,   1.11000000e+00,   1.16000000e+00,
        1.22000000e+00,   1.29000000e+00,   1.35000000e+00,   1.42000000e+00,
        1.50000000e+00,   1.57000000e+00,   1.65000000e+00,   1.74000000e+00,
        1.83000000e+00,   1.92000000e+00,   2.02000000e+00,   2.12000000e+00,
        2.23000000e+00,   2.31000000e+00,   2.35000000e+00,   2.37000000e+00,
        2.39000000e+00,   2.47000000e+00,   2.59000000e+00,   2.73000000e+00,
        2.87000000e+00,   3.01000000e+00,   3.17000000e+00,   3.33000000e+00,
        3.68000000e+00,   4.07000000e+00,   4.49000000e+00,   4.72000000e+00,
        4.97000000e+00,   5.22000000e+00,   5.49000000e+00,   5.77000000e+00,
        6.07000000e+00,   6.38000000e+00,   6.59000000e+00,   6.70000000e+00,
        7.05000000e+00,   7.41000000e+00,   7.79000000e+00,   8.19000000e+00,
        8.61000000e+00,   9.05000000e+00,   9.51000000e+00,   1.00000000e+01,
        1.05000000e+01,   1.11000000e+01,   1.16000000e+01,   1.22000000e+01,
        1.25000000e+01,   1.28000000e+01,   1.35000000e+01,   1.38000000e+01,
        1.42000000e+01,   1.45000000e+01,   1.49000000e+01,   1.57000000e+01,
        1.65000000e+01,   1.69000000e+01,   1.73000000e+01,   1.96400000e+01
    ]


@pytest.mark.parametrize('flux', [
    [
        3.22364000e+12,   3.49018000e+12,   6.68344000e+11,   6.96219000e+11,
        7.24916000e+11,   7.40953000e+11,   7.65277000e+11,   8.00225000e+11,
        8.11609000e+11,   8.30607000e+11,   8.56549000e+11,   8.76154000e+11,
        8.90778000e+11,   8.92658000e+11,   9.06612000e+11,   9.25102000e+11,
        9.46345000e+11,   9.50126000e+11,   9.69977000e+11,   9.72945000e+11,
        8.91562000e+11,   1.01666000e+12,   1.02179000e+12,   1.04209000e+12,
        1.05784000e+12,   1.01588000e+12,   1.09128000e+12,   1.21074000e+12,
        9.45772000e+11,   9.46879000e+11,   1.08542000e+12,   1.10852000e+12,
        1.15041000e+12,   1.06392000e+12,   1.19520000e+12,   1.32423000e+12,
        4.56794000e+11,   3.38685000e+11,   1.97494000e+11,   2.20893000e+11,
        4.79385000e+11,   5.07905000e+11,   5.14382000e+11,   6.99170000e+11,
        1.17667000e+12,   1.28101000e+12,   9.06538000e+11,   7.29466000e+11,
        5.72721000e+11,   1.34124000e+12,   1.06354000e+12,   6.53497000e+11,
        4.55974000e+11,   1.66350000e+11,   2.22590000e+11,   5.94821000e+11,
        3.04414000e+11,   1.12903000e+11,   3.81649000e+11,   3.88535000e+11,
        9.67020000e+11,   8.02009000e+11,   8.09689000e+11,   4.36557000e+11,
        1.22835000e+12,   5.31780000e+11,   6.71704000e+11,   4.39433000e+11,
        2.70295000e+11,   9.67125000e+11,   8.86275000e+11,   4.01154000e+11,
        4.53296000e+11,   5.12448000e+11,   5.65215000e+11,   5.29842000e+11,
        3.33609000e+11,   4.77049000e+11,   4.80220000e+11,   4.79371000e+11,
        6.45367000e+11,   4.94243000e+11,   4.54067000e+11,   5.11578000e+11,
        5.75962000e+11,   5.74561000e+11,   5.78411000e+11,   1.31497000e+12,
        5.48638000e+11,   3.05845000e+11,   1.31054000e+11,   6.61682000e+10,
        1.94880000e+11,   1.50178000e+12,   1.55801000e+12,   8.20771000e+11,
        6.54509000e+11,   1.20603000e+12,   1.47925000e+12,   7.95269000e+11,
        7.96674000e+11,   8.93619000e+11,   1.00667000e+12,   9.22262000e+11,
        1.08248000e+12,   1.03101000e+12,   1.16019000e+12,   9.44687000e+11,
        9.45891000e+11,   9.86574000e+11,   8.55742000e+11,   1.07061000e+12,
        6.04217000e+11,   1.60078000e+12,   8.84127000e+11,   9.67036000e+11,
        8.13577000e+11,   7.73406000e+11,   8.08930000e+11,   7.21397000e+11,
        6.87796000e+11,   6.94617000e+11,   7.04561000e+11,   6.74318000e+11,
        5.99602000e+11,   5.59727000e+11,   5.49765000e+11,   5.41305000e+11,
        3.69727000e+11,   1.80159000e+11,   9.53836000e+10,   9.74404000e+10,
        3.35538000e+11,   4.74346000e+11,   4.66625000e+11,   4.40457000e+11,
        4.22157000e+11,   3.93331000e+11,   3.69682000e+11,   6.88190000e+11,
        6.05989000e+11,   5.61747000e+11,   2.62660000e+11,   2.58770000e+11,
        2.36703000e+11,   2.35576000e+11,   2.18799000e+11,   2.07832000e+11,
        2.03860000e+11,   1.33971000e+11,   6.65969000e+10,   1.97603000e+11,
        1.88199000e+11,   1.86024000e+11,   1.82426000e+11,   1.81498000e+11,
        1.92282000e+11,   1.97989000e+11,   1.85735000e+11,   1.75964000e+11,
        1.76249000e+11,   1.67578000e+11,   2.25362000e+11,   1.71819000e+11,
        2.36343000e+11,   1.68090000e+12,   3.45776000e+12,   5.48335000e+12,
        4.09493000e+12,   1.34737000e+12,   1.90277000e+11,   1.92022000e+08,
        0.00000000e+00,   0.00000000e+00,   0.00000000e+00
    ]
])
def test_convert(new_ebins, ebins, flux):
    if not Path('fluxes_convert').exists():
        os.mkdir('fluxes_convert', mode=0o777)
    fispact_convert(ebins, flux, convert='fluxes_convert/convert',
                    fluxes='fluxes_convert/fluxes',
                    arb_flux='fluxes_convert/arb_flux',
                    files='fluxes_convert/files.convert')
    new_ebins = np.array(list(reversed(new_ebins))) * 1.e-6
    ebins = np.array(ebins)
    assert Path('fluxes_convert/fluxes').exists()
    with open('fluxes_convert/fluxes') as f:
        data = [float(x) for x in f.read().split()[:709]]
        new_flux = [x for x in reversed(data)]
    acc_flux = list(accumulate(flux))
    new_acc_flux = list(accumulate(new_flux))
    indices = np.searchsorted(new_ebins, ebins)
    # print(indices)
    for i, f in enumerate(acc_flux):
        if i >= 2:
            ind = indices[i]
            #       print(i, f, new_acc_flux[ind])
            assert f == pytest.approx(new_acc_flux[ind], rel=10.e-2)

    shutil.rmtree('fluxes_convert')


class TestIrradiationProfile:
    @pytest.fixture
    def irr_prof(self):
        irr = IrradiationProfile(norm_flux=2.0)
        irr.irradiate(5.0, 12, units='MINS')
        irr.relax(20, units='MINS', record='ATOMS')
        irr.irradiate(1.0, 2, units='HOURS', record='SPEC')
        irr.relax(1, units='HOURS', record='SPEC')
        irr.relax(2, units='MINS', record='ATOMS')
        return irr

    @pytest.mark.parametrize('flux, duration, units, record, exception', [
        (5.0, 10, 'HOURS', 'ABCD', ValueError),
        (5.0, 10, 'ABCD', None, KeyError),
        (-5.0, 10, 'MINS', None, ValueError),
        (5.0, -10, 'MINS', None, ValueError)
    ])
    def test_irradiate_failure(self, irr_prof, flux, duration, units, record, exception):
        with pytest.raises(exception):
            irr_prof.irradiate(flux, duration, units, record)

    @pytest.mark.parametrize('times', [
        list(accumulate([1920, 7200, 3600, 120]))
    ])
    def test_measure_times(self, irr_prof, times):
        measures = irr_prof.measure_times()
        assert measures == times

    @pytest.mark.parametrize('duration, units, record, exception', [
        (10, 'HOURS', 'ABCD', ValueError),
        (10, 'ABCD', None, KeyError),
        (-10, 'MINS', None, ValueError)
    ])
    def test_relax(self, irr_prof, duration, units, record, exception):
        with pytest.raises(exception):
            irr_prof.relax(duration, units, record)

    @pytest.mark.parametrize('time, value, unit', [
        (0.5, 0.5, 'SECS'),
        (12, 12, 'SECS'),
        (59, 59, 'SECS'),
        (75, 1.25, 'MINS'),
        (120, 2.0, 'MINS'),
        (3540, 59, 'MINS'),
        (3600, 1.0, 'HOURS'),
        (7200, 2.0, 'HOURS'),
        (23*3600, 23.0, 'HOURS'),
        (24*3600, 1.0, 'DAYS'),
        (36*3600, 1.5, 'DAYS'),
        (363*24*3600, 363.0, 'DAYS'),
        (365*24*3600, 1.0, 'YEARS'),
        (2*365*24*3600, 2.0, 'YEARS')
    ])
    def test_adjust_time(self, time, value, unit):
        adj_val, adj_unit = IrradiationProfile.adjust_time(time)
        assert adj_unit == unit
        assert adj_val == value

    @pytest.mark.parametrize('input, times, flux, record', [
        (['SPEC', 20, 'MINS'], [720, 480, 720, 7200, 3600, 120], [5.0, 0, 0, 1.0, 0, 0], ['', 'SPEC', 'ATOMS', 'SPEC', 'SPEC', 'ATOMS']),
        (['ATOMS', 3, 'HOURS'], [720, 1200, 7200, 1680, 1920, 120], [5.0, 0, 1.0, 0, 0, 0], ['', 'ATOMS', 'SPEC', 'ATOMS', 'SPEC', 'ATOMS']),
        (['SPEC', 12730, 'SECS'], [720, 1200, 7200, 3600, 10, 110], [5.0, 0, 1.0, 0, 0, 0], ['', 'ATOMS', 'SPEC', 'SPEC', 'SPEC', 'ATOMS']),
        (['SPEC', 7, 'MINS'], [420, 300, 1200, 7200, 3600, 120], [5.0, 5.0, 0, 1.0, 0, 0], ['SPEC', '', 'ATOMS', 'SPEC', 'SPEC', 'ATOMS']),
        (['ATOMS', 1, 'HOURS'], [720, 1200, 1680, 5520, 3600, 120], [5.0, 0, 1.0, 1.0, 0, 0], ['', 'ATOMS', 'ATOMS', 'SPEC', 'SPEC', 'ATOMS'])
    ])
    def test_insert_record(self, irr_prof, input, times, flux, record):
        irr_prof.insert_record(*input)
        assert irr_prof._duration == times
        assert irr_prof._flux == flux
        assert irr_prof._record == record

    @pytest.mark.parametrize('nominal, output', [
        (10, [
            'FLUX 25.0',
            'TIME 12.0 MINS ',
            'FLUX 0.0',
            'TIME 20.0 MINS ATOMS',
            'FLUX 5.0',
            'TIME 2.0 HOURS SPEC',
            'FLUX 0.0',
            'TIME 1.0 HOURS SPEC',
            'TIME 2.0 MINS ATOMS'
        ])
    ])
    def test_output(self, irr_prof, nominal, output):
        lines = irr_prof.output(nominal_flux=nominal)
        assert lines == output


@pytest.fixture
def irr_profile():
    irr = IrradiationProfile(norm_flux=1)
    irr.irradiate(0.05, 1, units='YEARS', record='ATOMS')
    irr.irradiate(1.0, 10, units='MINS', record='ATOMS')
    return irr


@pytest.fixture
def rel_profile():
    rel = IrradiationProfile()
    rel.relax(1, units='HOURS', record='ATOMS')
    rel.relax(23, units='HOURS', record='ATOMS')
    rel.relax(9, units='DAYS', record='ATOMS')
    rel.relax(355, units='DAYS', record='ATOMS')
    return rel


water = Material(atomic=[('H', 2), ('O', 1)], density=1.0)
steel = Material(weight=[('C', 0.8), ('Co', 0.1), ('Si', 1.0), ('Ni', 12.0),
                         ('Cr', 17.0), ('Cu', 0.2), ('Mn', 2.0), ('Mo', 2.5),
                         ('Fe', 64.4)], density=7.8)


fmesh = read_meshtal('tests/activ1.m')[94]
fluxes = fmesh._data[:, :, 0, 0]


@pytest.mark.skip
@pytest.mark.parametrize('flux, mat, gamma_yield', [
    (fluxes[:, 0],  steel, [4.9092e+09, 2.5711e+09, 2.2591e+09, 7.0520e+08]),
    (fluxes[:, 1],  steel, [2.7429e+09, 1.4365e+09, 1.2622e+09, 3.9401e+08]),
    (fluxes[:, 2],  steel, [1.8606e+09, 9.7446e+08, 9.1343e+08, 2.6728e+08]),
    (fluxes[:, 3],  steel, [1.4365e+09, 7.5232e+08, 6.6104e+08, 2.0635e+08]),
    pytest.param(fluxes[:, 4],  steel, [1.1831e+09, 5.4445e+08, 6.1963e+08, 1.4933e+08], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 5],  steel, [9.7446e+08, 4.7838e+08, 4.2033e+08, 1.2300e+08], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 6],  steel, [8.0259e+08, 3.9401e+08, 3.4620e+08, 9.4957e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 7],  steel, [8.0259e+08, 3.4620e+08, 3.0419e+08, 8.3435e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 8],  steel, [9.7446e+08, 3.0419e+08, 2.6728e+08, 7.3311e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 9],  steel, [1.3465e+09, 3.0419e+08, 2.6728e+08, 7.3311e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    (fluxes[:, 10], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 11], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 12], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 13], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 14], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 15], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 16], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 17], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 18], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 19], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    pytest.param(fluxes[:, 20], steel, [7.0520e+08, 1.2300e+08, 1.0807e+08, 2.7786e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 21], steel, [3.9401e+08, 8.9010e+07, 7.8209e+07, 2.0108e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 22], steel, [2.3485e+08, 6.4415e+07, 5.6599e+07, 1.3641e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 23], steel, [1.5931e+08, 4.9731e+07, 4.3697e+07, 1.1235e+07], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 24], steel, [1.1529e+08, 4.3697e+07, 3.5990e+07, 9.2532e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 25], steel, [8.9010e+07, 3.3736e+07, 2.9642e+07, 7.1439e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 26], steel, [7.8209e+07, 2.9642e+07, 2.6045e+07, 6.2770e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 27], steel, [7.8209e+07, 2.6045e+07, 2.2885e+07, 5.5153e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 28], steel, [9.4957e+07, 2.4414e+07, 2.1452e+07, 4.8461e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 29], steel, [1.3998e+08, 2.7786e+07, 2.2885e+07, 5.8839e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    (fluxes[:, 30], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 31], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 32], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 33], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 34], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 35], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 36], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 37], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 38], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 39], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    pytest.param(fluxes[:, 40], steel, [6.8719e+07, 1.1235e+07, 9.8715e+06, 2.3791e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 41], steel, [3.8395e+07, 7.6212e+06, 6.6964e+06, 1.5128e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 42], steel, [2.2885e+07, 5.5153e+06, 4.8461e+06, 1.1679e+06], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 43], steel, [1.4552e+07, 4.2581e+06, 3.7414e+06, 9.0169e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 44], steel, [1.0531e+07, 3.5071e+06, 2.8885e+06, 6.9614e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 45], steel, [8.1304e+06, 2.8885e+06, 2.5380e+06, 5.7336e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 46], steel, [7.1439e+06, 2.5380e+06, 2.2301e+06, 5.0379e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 47], steel, [6.6964e+06, 1.9595e+06, 1.7217e+06, 4.1493e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 48], steel, [8.1304e+06, 2.0904e+06, 1.7217e+06, 4.1493e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    pytest.param(fluxes[:, 49], steel, [1.1985e+07, 2.2301e+06, 1.9595e+06, 4.7223e+05], marks=pytest.mark.xfail(reason='thermal neutrons')),
    (fluxes[:, 50], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 51], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 52], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 53], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 54], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 55], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 56], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 57], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 58], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
    (fluxes[:, 59], water, [0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]),
])
def test_activation(irr_profile, rel_profile, ebins, flux, mat, gamma_yield):
    result = activation('test', mat, 400, (ebins, flux), irr_profile,
                        rel_profile, tab4=True, use_binary=True, inv_tol=(1.e+1, 1.e-6))
    for frame, expected in zip(result['spectrum'][-4:], gamma_yield):
        tot_flux = np.sum(frame) / 400
        #print(tot_flux / expected)
        assert tot_flux == pytest.approx(expected, rel=0.1)


@pytest.fixture
def act2_universe():
    return read_mcnp('tests/activ2.i')


@pytest.fixture
def cell_mesh(act2_universe):
    cm = {}
    vol_data = {
        3: {
            (0, 0, 0): 4363.303128629923, (0, 1, 0): 10926.737990230322,
            (0, 2, 0): 1210.5920724570751, (1, 0, 0): 10927.178978919983,
            (1, 1, 0): 18000.0, (1, 2, 0): 4926.807012408972,
            (2, 0, 0): 1210.692722350359, (2, 1, 0): 4926.640748977661,
            (2, 2, 0): 57.69944563508034
        },
        4: {
            (0, 0, 0): 2185.912571847439, (0, 0, 1): 2178.4597355872393,
            (0, 1, 0): 5474.039610475302, (0, 1, 1): 5455.369516275823,
            (0, 2, 0): 606.4782366156578, (0, 2, 1): 604.4117454439402,
            (1, 0, 0): 5474.260523915291, (1, 0, 1): 5455.5911757051945,
            (1, 1, 0): 5870.348867028952, (1, 1, 1): 5850.332002155483,
            (1, 2, 0): 2468.214802443981, (1, 2, 1): 2459.7999919205904,
            (2, 0, 0): 606.5286621451378, (2, 0, 1): 604.4617015868425,
            (2, 1, 0): 2468.1315198540688, (2, 1, 1): 2459.7155023366213,
            (2, 2, 0): 28.906065970659256, (2, 2, 1): 28.80797255784273
        },
        5: {
            (0, 0, 1): 3275.6691752001643, (0, 0, 2): 1092.4295503646135,
            (0, 1, 1): 8203.05297151208, (0, 1, 2): 2735.691202338785,
            (0, 2, 1): 908.8283451274037, (0, 2, 2): 303.09488251805305,
            (1, 0, 1): 8203.382547944784, (1, 0, 2): 2735.8038257807493,
            (1, 1, 1): 8796.932394616306, (1, 1, 2): 2933.756907004863,
            (1, 2, 1): 3698.7087735906243, (1, 2, 2): 1233.5134260356426,
            (2, 0, 1): 908.9042013511062, (2, 0, 2): 303.1196426600218,
            (2, 1, 1): 3698.585433885455, (2, 1, 2): 1233.4695970639586,
            (2, 2, 1): 43.31633448600769, (2, 2, 2): 14.44675074890256
        },
        6: {
            (0, 0, 2): 4362.233949825168, (0, 1, 2): 10924.066853709519,
            (0, 2, 2): 1210.2941628545523, (1, 0, 2): 10924.50625821948,
            (1, 1, 2): 11714.942165650427, (1, 2, 2): 4925.599230453372,
            (2, 0, 2): 1210.3950809687376, (2, 1, 2): 4925.434475764632,
            (2, 2, 2): 57.68485274165869
        },
        7: {
            (0, 0, 2): 2181.116974912584, (0, 0, 3): 2177.390556782484,
            (0, 1, 2): 5462.033426854759, (0, 1, 3): 5452.69837975502,
            (0, 2, 2): 605.1470814272761, (0, 2, 3): 604.1138358414173,
            (1, 0, 2): 5462.25312910974, (1, 0, 3): 5452.918455004692,
            (1, 1, 2): 8997.802734375, (1, 1, 3): 8982.421875,
            (1, 2, 2): 2462.799615226686, (1, 2, 3): 2458.5922099649906,
            (2, 0, 2): 605.1975404843688, (2, 0, 3): 604.1640602052212,
            (2, 1, 2): 2462.717237882316, (2, 1, 3): 2458.5092291235924,
            (2, 2, 2): 28.842426370829344, (2, 2, 3): 28.79337966442108
        }
    }
    for name, data in vol_data.items():
        cell = act2_universe.select_cell(name)
        cm[cell] = SparseData((3, 3, 5))
        for index, vol in data.items():
            cm[cell][index] = vol
    return cm


@pytest.mark.parametrize('fmesh', [
    read_meshtal('tests/activ2_0.m')[14]
])
def test_superposition_mesh_activation(ebins, cell_mesh, irr_profile, rel_profile, fmesh):
    mesh_result = mesh_activation(
        'test_mesh', fmesh, cell_mesh, irr_profile, rel_profile, simple=True,
        folder='tests/meshact2', use_binary=True, tab4=True, read_only=True,
        inv_tol=(0.1, 1.e-6)
    )
    if not Path('tests/arch.data').exists():
        result = {}
        for c, vols in cell_mesh.items():
            if c.material() is None:
                continue
            result[c] = {}

            for (i, j, k), vol in vols:
                print(i, j, k)
                result[c][(i, j, k)] = activation(
                    'test mesh', c.material(), vol, (ebins, fmesh._data[:, i, j, k]),
                    irr_profile, rel_profile, tab4=True, use_binary=True,
                    read_only=False, inventory='inventory_{0}_{1}_{2}_b_{3}'.format(i, j, k, c['name']),
                    inv_tol=(0.1, 1.e-6)
                )
        with open('tests/arch.data', 'wb') as f:
            save_result = {c['name']: data for c, data in result.items()}
            pickle.dump(save_result, f, pickle.HIGHEST_PROTOCOL)
    else:
        with open('tests/arch.data', 'rb') as f:
            save_result = pickle.load(f)
        result = {}
        for c in cell_mesh.keys():
            result[c] = save_result[c['name']]

    #print(mat_vol.keys())
    for i, time_frame in enumerate(mesh_result['spectrum']):
        for c, data in time_frame.items():
            for index, spec in data:
                e_x = np.sum(spec * mesh_result['ebins'][1:])
                e_y = np.sum(result[c][index]['spectrum'][i] * mesh_result['ebins'][1:])
                for j, (x, y) in enumerate(zip(spec, result[c][index]['spectrum'][i])):
                    if y == 0 and x == 0:
                        continue
                    diff = abs(x - y) / max(x, y)
                    xe_frac = x * mesh_result['ebins'][j + 1] / e_x
                    ye_frac = x * mesh_result['ebins'][j + 1] / e_y
                    if xe_frac > 2.e-3 or ye_frac > 2.e-3:
                        print('t=', i, 'e=', j, 'm=',
                              c.material().composition['name'], x / y,
                              cell_mesh[c][index], x, y,
                              x * mesh_result['ebins'][j + 1] / e_x)
                        assert diff < 0.05


@pytest.mark.parametrize('fmesh', [
    read_meshtal('tests/activ2_0.m')[14]
])
def test_full_mesh_activation(ebins, cell_mesh, irr_profile, rel_profile, fmesh):
    mesh_result = mesh_activation(
        'test_mesh', fmesh, cell_mesh, irr_profile, rel_profile, simple=False,
        folder='tests/meshact', use_binary=True, tab4=True, read_only=False,
        inv_tol=(0.1, 1.e-6)
    )
    if not Path('tests/arch.data').exists():
        result = {}
        for c, vols in cell_mesh.items():
            if c.material() is None:
                continue
            result[c] = {}

            for (i, j, k), vol in vols:
                print(i, j, k)
                result[c][(i, j, k)] = activation(
                    'test mesh', c.material(), vol, (ebins, fmesh._data[:, i, j, k]),
                    irr_profile, rel_profile, tab4=True, use_binary=True,
                    read_only=False, inventory='inventory_{0}_{1}_{2}_b_{3}'.format(i, j, k, c['name']),
                    inv_tol=(0.1, 1.e-6)
                )
        with open('tests/arch.data', 'wb') as f:
            save_result = {c['name']: data for c, data in result.items()}
            pickle.dump(save_result, f, pickle.HIGHEST_PROTOCOL)
    else:
        with open('tests/arch.data', 'rb') as f:
            save_result = pickle.load(f)
        result = {}
        for c in cell_mesh.keys():
            result[c] = save_result[c['name']]

    #print(mat_vol.keys())
    for i, time_frame in enumerate(mesh_result['spectrum']):
        for c, data in time_frame.items():
            for index, spec in data:
                np.testing.assert_array_almost_equal(
                    spec, result[c][index]['spectrum'][i]
                )