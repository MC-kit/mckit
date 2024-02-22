"""The mckit package code root."""

from __future__ import annotations

import mckit._init_dynamic_libraries

from mckit.body import Body, Shape
from mckit.fmesh import FMesh
from mckit.material import AVOGADRO, Composition, Element, Material
from mckit.parser import ParseResult, from_file, from_stream, from_text, read_meshtal
from mckit.parser.mctal_parser import read_mctal
from mckit.surface import Cone, Cylinder, GQuadratic, Plane, Sphere, Torus, create_surface
from mckit.transformation import Transformation
from mckit.universe import Universe
from mckit.version import (
    __author__,
    __copyright__,
    __license__,
    __summary__,
    __title__,
    __version__,
)

__all__: list[str] = [
    "AVOGADRO",
    "Body",
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
    "__author__",
    "__copyright__",
    "__license__",
    "__summary__",
    "__title__",
    "__version__",
    "__version__",
    "create_surface",
    "from_file",
    "from_stream",
    "from_text",
    "read_mctal",
    "read_meshtal",
]
