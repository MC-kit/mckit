"""The mckit package code root."""

from __future__ import annotations

import sys
import sysconfig

from mckit.body import Body, Shape
from mckit.box import GLOBAL_BOX, Box
from mckit.fmesh import FMesh
from mckit.material import AVOGADRO, Composition, Element, Material
from mckit.parser import ParseResult, from_file, from_stream, from_text, read_meshtal
from mckit.parser.mctal_parser import read_mctal
from mckit.surface import Cone, Cylinder, GQuadratic, Plane, Sphere, Torus, create_surface
from mckit.transformation import Transformation, calc_z_rotation
from mckit.universe import Universe
from mckit.version import (
    __copyright__,
    __title__,
    __version__,
)

WIN = sys.platform.startswith("win32") and "mingw" not in sysconfig.get_platform()
MACOS = sys.platform.startswith("darwin")

__all__: list[str] = [
    "AVOGADRO",
    "GLOBAL_BOX",
    "MACOS",
    "WIN",
    "Body",
    "Box",
    "Composition",
    "Cone",
    "Cylinder",
    "Element",
    "FMesh",
    "GQuadratic",
    "Material",
    "ParseResult",
    "Plane",
    "Shape",
    "Sphere",
    "Torus",
    "Transformation",
    "Universe",
    "__copyright__",
    "__title__",
    "__version__",
    "calc_z_rotation",
    "create_surface",
    "from_file",
    "from_stream",
    "from_text",
    "read_mctal",
    "read_meshtal",
]
