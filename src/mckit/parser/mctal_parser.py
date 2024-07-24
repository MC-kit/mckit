from __future__ import annotations

import re

from collections import deque
from itertools import product
from pathlib import Path

import numpy as np


def read_mctal(filename: str | Path, encoding="utf-8"):
    """Reads tally file.

    Args:
        filename: Name of mctal file.
        encoding: Name of encoding. Default: utf-8.

    Returns:
        A dictionary of tally data.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    with filename.open(encoding=encoding) as f:
        text = f.read()
    flags = re.MULTILINE + re.IGNORECASE
    header, *tally_texts = re.split("tally", text, flags=flags)
    tallies = {}
    for text in tally_texts:
        tally = parse_tally(text)
        tallies[tally["name"]] = tally
    return tallies


def parse_tally(text):
    """Parses text of tally."""
    tally = {}
    header_text, bin_text, val_text, tfc_text, comment = split_topics(text)

    tally["comment"] = comment.strip()
    tally.update(parse_tally_header(header_text))
    tally.update(parse_bins(bin_text))
    data, error = parse_values(val_text, tally["dims"])
    tally["data"] = data
    tally["error"] = error
    return tally


def parse_values(text, shape):
    tokens = deque(text.split())
    data = np.empty(shape)
    err = np.empty_like(data)
    for index in product(*map(range, shape)):
        data[index] = float(tokens.popleft())
        err[index] = float(tokens.popleft())
    return data, err


def split_topics(text):
    flags = re.MULTILINE + re.IGNORECASE
    text, tfc_text = re.split("tfc", text, maxsplit=1, flags=flags)
    text, val_text = re.split("vals", text, maxsplit=1, flags=flags)
    text, bin_text = re.split("^f", text, maxsplit=1, flags=flags)
    header_text, comment = re.split("\n", text, maxsplit=1)
    return header_text, bin_text, val_text, tfc_text, comment


PARTICLE_CODES = {1: "N", 2: "P", 4: "E"}
DETECTOR_TYPES = {0: "Non", 1: "Point", 2: "Ring", 3: "FIP", 4: "FIR", 5: "FIC"}


def parse_tally_header(text):
    """Parses text of tally header."""
    result = {}
    values = deque(text.split())
    result["name"] = int(values.popleft())
    p_code = int(values.popleft())
    result["particles"] = {par for code, par in PARTICLE_CODES.items() if code & p_code}
    result["type"] = DETECTOR_TYPES[int(values.popleft())]
    return result


def parse_bins(text):
    bin_texts = deque(re.split("^[a-z]", text, flags=re.MULTILINE + re.IGNORECASE))
    result = {"dims": [], "bins": [], "vars": []}
    # f: cells, surfaces, detector bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), True, int)
    update_bins(result, dim_size, bin_values, "f")
    # d: detectors
    dim_size, bin_values = parse_bin(bin_texts.popleft(), False)
    update_bins(result, dim_size, bin_values, "d")
    # u: user bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), False)
    update_bins(result, dim_size, bin_values, "u")
    # s: segment bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), False)
    update_bins(result, dim_size, bin_values, "s")
    # m: multiplier bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), False)
    update_bins(result, dim_size, bin_values, "m")
    # c: cosine bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), True, float)
    update_bins(result, dim_size, bin_values, "c")
    # e: energy bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), True, float)
    update_bins(result, dim_size, bin_values, "e")
    # t: time bins
    dim_size, bin_values = parse_bin(bin_texts.popleft(), True, float)
    update_bins(result, dim_size, bin_values, "t")
    return result


def update_bins(result, dim_size, bin_values, var):
    if dim_size > 0:
        result["dims"].append(dim_size)
        result["bins"].append(bin_values)
        result["vars"].append(var)


def parse_bin(text, read_values=True, val_type=float):
    bin_header, values_list = text.split("\n", maxsplit=1)
    tokens = deque(bin_header.split())
    t = tokens.popleft()
    if t.isdigit():
        tokens.appendleft(t)
    dim_size = int(tokens.popleft())
    if dim_size == 1:
        dim_size = 0
    # if extra:
    #     tokens.popleft()
    tokens = deque(values_list.split())
    if read_values:
        bin_values = [val_type(t) for t in tokens]
    else:
        bin_values = list(range(dim_size))
    return dim_size, bin_values
