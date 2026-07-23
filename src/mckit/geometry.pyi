from .types import NPFloatArray

class Box: ...

class Surface:
    ...

class Shape:
    opc: str
    args: Shape | list[Shape] | None
    def __init__(self, _opc: str, *_args: Shape | Surface) -> None:
        ...


class BOX: ...
class RCC: ...

class Cone:
    _apex: NPFloatArray
    _axis: NPFloatArray
    _t2: float
    _sheet: int

class Cylinder:
    _pt: NPFloatArray
    _axis: NPFloatArray
    _radius: float
    def __init__(self, pt: NPFloatArray, axis: NPFloatArray, radius: float) -> None: ...

class GQuadratic:
    _m: NPFloatArray
    _v: NPFloatArray
    _k: float
    _factor: float
    def __init__(self, m: NPFloatArray, v: NPFloatArray, k: float, factor: float): ...

class Plane:
    _v: NPFloatArray
    _k: float
    def __init__(self, norm: NPFloatArray, offset: float) -> None: ...

class Sphere:
    _center: NPFloatArray
    _radius: float

class Torus:
    _center: NPFloatArray
    _axis: NPFloatArray
    _R: float
    _a: float
    _b: float
    def __init__(
        self, center: NPFloatArray, axis: NPFloatArray, r: float, a: float, b: float
    ) -> None: ...

EX: NPFloatArray
EY: NPFloatArray
EZ: NPFloatArray
GLOBAL_BOX: Box
MIN_VOLUME: float
ORIGIN: NPFloatArray
