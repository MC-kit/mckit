# This is not real surface objects. They need only to test function.
# String object utilizing here is acceptable.
from __future__ import annotations

surf_obj = {
    1: "S1",
    2: "S2",
    3: "S3",
    4: "S4",
    5: "S5",
    6: "S6",
    7: "S7",
    8: "S8",
    9: "S9",
    10: "S10",
    11: "S11",
    12: "S12",
}

cell_cases = [
    {
        1: {
            "geometry": [1, "C", 2, "U", 3, "I", 4, "U"],
            "answer": ["S1", "C", "S2", "U", "S3", "I", "S4", "U"],
        }
    },
    {
        1: {
            "reference": 2,
            "answer": ["S1", "C", "S2", "C", "I", "S3", "C", "U", "S4", "I"],
        },
        2: {
            "geometry": [1, "C", 2, "C", "I", 3, "C", "U", 4, "I"],
            "answer": ["S1", "C", "S2", "C", "I", "S3", "C", "U", "S4", "I"],
        },
    },
    {
        1: {
            "geometry": [1, "C", 2, "C", "I", 3, "C", "U", 4, "I"],
            "answer": ["S1", "C", "S2", "C", "I", "S3", "C", "U", "S4", "I"],
        },
        2: {
            "reference": 1,
            "answer": ["S1", "C", "S2", "C", "I", "S3", "C", "U", "S4", "I"],
        },
    },
    {
        1: {
            "geometry": [4, "C", 5, "U", 6, "I", 7, "U"],
            "answer": ["S4", "C", "S5", "U", "S6", "I", "S7", "U"],
        },
        2: {
            "geometry": [1, 2, "I", 3, "C", 1, "#", "I", "U", 8, "I"],
            "answer": [
                "S1",
                "S2",
                "I",
                "S3",
                "C",
                "S4",
                "C",
                "S5",
                "U",
                "S6",
                "I",
                "S7",
                "U",
                "C",
                "I",
                "U",
                "S8",
                "I",
            ],
        },
        3: {
            "geometry": [1, "#", 2, "U"],
            "answer": ["S4", "C", "S5", "U", "S6", "I", "S7", "U", "C", "S2", "U"],
        },
        4: {
            "geometry": [1, "C", 2, "U", 6, "#", "I"],
            "answer": ["S1", "C", "S2", "U", "S8", "S9", "I", "S10", "U", "C", "I"],
        },
        5: {"geometry": [6, "#"], "answer": ["S8", "S9", "I", "S10", "U", "C"]},
        6: {"geometry": [8, 9, "I", 10, "U"], "answer": ["S8", "S9", "I", "S10", "U"]},
    },
]
