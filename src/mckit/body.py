from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import os

from collections.abc import Generator
from copy import deepcopy
from functools import reduce
from itertools import groupby, permutations, product
from logging import getLogger
from multiprocessing import Pool

import numpy as np

from click import progressbar

import mckit.material as mm

from mckit.box import GLOBAL_BOX, Box
from mckit.card import CARD_SLOTS, Card
from mckit.constants import MIN_BOX_VOLUME

# pyrefly: ignore [missing-import]
# pyright: reportMissingModuleSource=false
from mckit.geometry import Shape as _Shape
from mckit.printer import CELL_OPTIONS, print_option
from mckit.surface import Surface
from mckit.transformation import Transformation

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from collections.abc import Iterable, Iterator, Sequence

    from mckit import Universe
    from mckit.types import NPIntArray
    from mckit.utils.named import Name

    ShapeOperationCode = Literal["I", "U", "E", "R", "S", "C"]
    type TGeometry = list[Surface | ShapeOperationCode | Shape | Body] | Body | Shape


__all__ = ["GLOBAL_BOX", "Body", "Card", "Shape", "simplify"]

_LOG = getLogger(__name__)


# Shape and Body are defined in a single module because of tight coupling.
# It is not possible to separate them due to unavoidable cyclic dependency.


class Shape(_Shape):
    """Shape class.

    Note:
        Shape is immutable object.

    Parameters
    ----------
        opc
            Operation code. It may be different from opc passed in __init__.
        invert_opc
            Operation code, complement to the opc.
        args
            A tuple of shape's arguments.

    Methods
    -------
        test_box(box)
            Tests if the box intersects the shape.
        volume(box, min_volume)
            Calculates the volume of the shape with desired accuracy.
        bounding_box(box, tol)
            Finds bounding box for the shape with desired accuracy.
        test_points(points)
            Tests the senses of the points.
        is_complement(other)
            Checks if other is a complement to the shape.
        complement()
            Gets complement shape.
        union(*other)
            Creates a union of the shape with the others.
        intersection(*other)
            Creates an intersection of the shape with the others.
        transform(transformation)
            Gets transformed version of the shape.
        is_empty()
            Checks if this shape is empty - no space belong to it.
        get_surfaces()
            Gets all Surface objects that bounds the shape.
        complexity()
            Gets the complexity of the shape description.
        get_simplest()
            Gets the simplest description of the shape.
        replace_surfaces(replace_dict)
            Creates new Shape object by replacing surfaces.
    """

    _opc_hash: ClassVar = {
        "I": hash("I"),
        "U": ~hash("I"),
        "E": hash("E"),
        "R": ~hash("E"),
        "S": hash("S"),
        "C": ~hash("S"),
    }

    def __init__(self, _opc: ShapeOperationCode, *_args: Shape | Surface | Body) -> None:
        """Initialize Shape object.

        Parameters
        ----------
            _opc
                Operation code. Denotes operation to be applied.
                Possible values:
                'I' - for intersection;
                'U' - for union;
                'C' - for complement;
                'S' - (same) no operation;
                'E' - empty set - no space occupied;
                'R' - whole space.
            _args
                Geometry elements.
                It can be either Shape or Surface instances. But
                no arguments must be specified for 'E' or 'R' opc. Only one argument
                must present for 'C' or 'S' opc values.
        """
        opc, args = _clean_args(_opc, *_args)
        _Shape.__init__(self, opc, *args)
        self._calculate_hash(opc, *args)

    @property
    def args(self) -> tuple[Shape | Surface, ...]:  # ty: ignore[invalid-property-type-override]
        """Gets the shape's arguments as the wrapper objects defined in this module."""
        return cast("tuple[Shape | Surface, ...]", super().args)

    # TODO @dvp: remove this method (it's logically wrong), check usage in accept/visit
    def __iter__(self):
        return iter(self.args)

    def __getstate__(self):
        return self.opc, self.args, self._hash

    def __setstate__(self, state):
        opc, args, hash_value = state
        _Shape.__init__(self, opc, *args)
        self._hash = hash_value

    def __repr__(self):
        return f"Shape({self.opc}, {self.args})"

    def get_words(self, parent_opc: ShapeOperationCode | None = None) -> list[str]:
        """Gets list of words that describe the shape.

        Parameters
        ----------
        parent_opc
            Operation code of parent shape. It is needed for proper use of parenthesis.

        Returns
        -------
            List of words.
        """
        words = []
        if self.opc == "S":
            words.append(f"{cast(Surface, self.args[0]).name()}")
        elif self.opc == "C":
            words.append(f"-{cast(Surface, self.args[0]).name()}")
        elif self.opc == "E":
            words.append("EMPTY_SET")
        elif self.opc == "R":
            words.append("UNIVERSE_SET")
        else:
            sep = " " if self.opc == "I" else ":"
            args = cast("tuple[Shape, ...]", self.args)
            need_parentheses = self.opc == "U" and parent_opc == "I"
            if need_parentheses:
                words.append("(")
            for a in args[:-1]:
                words.extend(a.get_words(self.opc))
                words.append(sep)
            words.extend(args[-1].get_words(self.opc))
            if need_parentheses:
                words.append(")")
        return words

    _get_words = get_words  # old name was private

    def __eq__(self, other) -> bool:  # noqa: PLR0911
        if self is other:
            return True
        if self.opc != other.opc:
            return False
        if self.opc in {"E", "R"}:  # empty or whole space
            return True
        if len(self.args) != len(other.args):
            return False
        self_groups = {k: list(v) for k, v in groupby(self.args, key=hash)}
        other_groups = {k: list(v) for k, v in groupby(other.args, key=hash)}
        for hash_value, entities in self_groups.items():
            if hash_value not in other_groups:
                return False
            if len(entities) != len(other_groups[hash_value]):
                return False
            for other_entities in permutations(other_groups[hash_value]):
                for se, oe in zip(entities, other_entities, strict=False):
                    if not (se == oe):
                        break
                else:
                    return True
        return False

    def __hash__(self) -> int:
        return cast(int, self._hash)

    def _calculate_hash(self, opc, *args) -> None:
        """Calculates hash value for the object.

        Hash is 'xor' for hash values of all arguments together with opc hash.
        """
        if opc == "C":  # C and S can be present only with Surface instance.
            self._hash = ~hash(args[0])
        elif opc == "S":
            self._hash = hash(args[0])
        else:
            self._hash = self._opc_hash[opc]
            for a in args:
                self._hash ^= hash(a)

    def complement(self):
        """Gets complement to the shape.

        Returns
        -------
            Complement shape.
        """
        opc = self.opc
        args = self.args
        if opc == "S":
            return Shape("C", args[0])
        if opc == "C":
            return Shape("S", args[0])
        if opc == "E":
            return Shape("R")
        if opc == "R":
            return Shape("E")
        opc = self.invert_opc
        c_args = (cast(Shape, a).complement() for a in args)
        return Shape(opc, *c_args)

    def is_complement(self, other: Shape) -> bool:
        """Checks if this shape is complement to the other.

        Returns
        -------
            Test result.
        """
        if hash(self) != ~hash(other):
            return False
        if self.opc != other.invert_opc:
            return False
        if len(self.args) != len(other.args):
            return False
        if len(self.args) == 1:
            return self.args[0] == other.args[0]
        if len(self.args) > 1:
            for a in cast("tuple[Shape, ...]", self.args):
                for b in cast("tuple[Shape, ...]", other.args):
                    if a.is_complement(b):
                        break
                else:
                    return False  # not found complement to `a` in `other` args
        return True

    def intersection(self, *other: Shape | Surface | Body) -> Shape:
        """Gets intersection with other shape.

        Args:
            other: A list of Shape or Body objects, which must be intersected.

        Returns
        -------
            New shape.
        """
        return Shape("I", self, *other)

    def union(self, *other):
        """Gets union with other shape.

        Args:
            other :  A list of Shape or Body objects, which must be joined.

        Returns
        -------
            New shape.
        """
        return Shape("U", self, *other)

    def transform(self, transformation: Transformation) -> Shape:
        """Transforms the shape.

        Args:
            transformation : Transformation to be applied.

        Returns
        -------
            New shape.
        """
        opc = self.opc
        args = (a.transform(transformation) for a in self.args)
        return Shape(opc, *args)

    def apply_transformation(self):
        opc = self.opc
        args = [a.apply_transformation() for a in self.args]
        return Shape(opc, *args)

    def complexity(self) -> int:
        """Gets complexity of shape.

        Returns
        -------
            The complexity of the shape description. It is the number of
            surfaces needed to describe the shape. Repeats are taken into
            account.
        """
        args = self.args
        if len(args) == 1:
            return 1
        if len(args) > 1:
            result = 0
            for a in args:
                result += cast(Shape, a).complexity()
            return result
        return 0

    def get_surfaces(self) -> set[Surface]:
        """Gets all the surfaces that describe the shape."""
        return set(self.scan_surfaces())

    def scan_surfaces(self) -> Generator[Surface]:
        """Iterate over all the surfaces that describe the shape."""
        args = self.args
        _len = len(args)
        if _len == 1:
            yield cast(Surface, args[0])
        elif _len > 1:
            for a in cast("tuple[Shape, ...]", args):
                yield from a.scan_surfaces()

    def is_empty(self) -> bool:
        """Check, if the shape is empty."""
        return self.opc == "E"

    def split_shape(self) -> list[Shape]:
        def _scan() -> Generator[Shape]:
            if self.opc == "U":
                stat = self.get_stat_table()
                drop_index = np.nonzero(np.all(stat == -1, axis=1))[0]
                arg_results = np.delete(stat, drop_index, axis=0)
                index_groups = self._find_groups(arg_results == +1)
                for ig in index_groups:
                    index = np.nonzero(ig)[0]
                    args = (self.args[i] for i in index)
                    yield Shape("U", *args)
            elif self.opc == "I":
                arg_groups = (cast(Shape, arg).split_shape() for arg in self.args)
                for args in product(*arg_groups):
                    yield Shape("I", *args)
            else:
                yield self

        return list(_scan())

    @staticmethod
    def _find_groups(result: NPIntArray) -> list[NPIntArray]:
        groups = [result[i, :] for i in range(result.shape[0])]
        while True:
            index = len(groups) - 1
            for j in range(index - 1, -1, -1):
                if np.any(groups[index] & groups[j] == 1):
                    groups[j] |= groups[index]
                    groups.pop(index)
                    break
            else:
                break
        return groups

    def get_simplest(self, trim_size: int = 0) -> list[Shape]:  # noqa: PLR0911
        """Gets the simplest found description of the shape.

        Parameters
        ----------
        trim_size
            Shape variants with complexity greater than minimal one more than
            trim_size are thrown away.

        Returns
        -------
            A list of shapes with minimal complexity.
        """
        if self.opc not in {"I", "U"}:  # not an intersection or a union
            return [self]
        node_cases = []
        complexities = []
        stat = self.get_stat_table()
        if self.opc == "I":
            val = -1
        elif self.opc == "U":
            val = +1
        else:  # pragma: no cover - self.opc is restricted to "I"/"U" by the check above
            return [self]

        drop_index = np.nonzero(np.all(stat == -val, axis=1))[0]
        if len(drop_index) == 0:
            if self.opc == "I":
                return [Shape("E")]
            if self.opc == "U":  # pragma: no branch - only "U" gets here, "I" returned above
                return [Shape("R")]
        arg_results = np.delete(stat, drop_index, axis=0)
        if arg_results.shape[0] == 0:
            if self.opc == "I":
                return [Shape("R")]
            if self.opc == "U":  # pragma: no branch - only "U" gets here, "I" returned above
                return [Shape("E")]
        cases = self._find_coverages(arg_results, value=val)
        final_cases = {tuple(c) for c in cases}
        if len(final_cases) == 0:  # pragma: no cover - every stat row keeps a `val` entry
            msg = "No final cases found"
            raise ValueError(msg)
            # _LOG.debug(self)
            # return None  # TODO dvp: what's the logic here?
        unique = reduce(lambda a, b: a.union(b), (set(x) for x in final_cases))
        args = self.args
        node_variants = {i: cast(Shape, args[i]).get_simplest(trim_size) for i in unique}
        for indices in final_cases:
            variants = [node_variants[i] for i in indices]
            for args in product(*variants):
                node = Shape(self.opc, *args)
                node_cases.append(node)
                complexities.append(node.complexity())
        sort_ind = np.argsort(complexities)
        final_nodes = []
        min_complexity = complexities[sort_ind[0]]
        for i in sort_ind:
            final_nodes.append(node_cases[i])
            if complexities[i] > min_complexity + trim_size:
                break
        return final_nodes

    @staticmethod
    def _find_coverages(results: np.ndarray, value: int = +1, level: int = 0) -> list[list[int]]:
        """Create tables of ... .

        Given `results`, find counts of value occurrences over its rows.
        For the row with minimal counts, scan the columns and
        if value found, than extract `remainder` from `results`,
        where `value` is not found in the current column.
        Run the process recursively on `remainder`.

        Parameters
        ----------
        results
            ...
        value
            ...
        level
            for recursion logging

        Returns
        -------
            table with column numbers, where `value` is found ?
        """
        _LOG.debug(f"coverage level: {level}, results size: {results.size}, shape: {results.shape}")
        n = results.shape[1]
        cnt = np.count_nonzero(results == value, axis=1)
        i = np.argmin(cnt)
        cases = []
        for j in range(n):
            if results[i][j] == value:
                reminder = np.compress(results[:, j] != value, results, axis=0)
                if reminder.shape[0] == 0:  # in remaining rows the value of column `j` is the same
                    sub_cases = [[j]]
                else:
                    sub_cases = Shape._find_coverages(reminder, value=value, level=level + 1)
                    for s in sub_cases:
                        s.append(j)  # add `j` column index to subcases
                cases.extend(sub_cases)
        for c in cases:
            c.sort()
        return cases

    def replace_surfaces(self, replace_dict: dict[Surface, Surface | Shape]) -> Shape:
        """Creates new Shape instance by replacing surfaces.

        If shape's surface is in replace dict, it is replaced by surface in
        dictionary values. Otherwise, the original surface is used. But new
        shape is created anyway.

        Parameters
        ----------
        replace_dict
            A dictionary of surfaces to be replaced.

        Returns
        -------
            New Shape object obtained by replacing certain surfaces.
        """
        # TODO @dvp: dict[Surface, ...] is inefficient (hash is expensive), change to dict[Name, ...] mapping
        if self.opc in {"C", "S"}:  # complement or 'no operation'
            arg = cast(Surface, self.args[0])
            surf = replace_dict.get(arg)
            return Shape(self.opc, surf or arg)
        if self.opc in {"I", "U"}:  # intersection or union
            args = [cast(Shape, arg).replace_surfaces(replace_dict) for arg in self.args]
            return Shape(self.opc, *args)
        return self

    @staticmethod
    def from_polish_notation(polish: TGeometry) -> Shape:
        """Creates Shape instance from reversed Polish notation.

        Parameters
        ----------
        polish
            List of surfaces and operations written in reversed Polish Notation.

        Returns
        -------
            The geometry represented by Shape instance.
        """
        operands = []
        for _op in polish:
            op = _op
            if isinstance(op, Body):
                op = op.shape
            if isinstance(op, Surface):
                operands.append(Shape("S", op))
            elif isinstance(op, Shape):
                operands.append(op)
            elif op == "C":
                operands.append(operands.pop().complement())
            else:
                arg1 = operands.pop()
                arg2 = operands.pop()
                operands.append(Shape(op, arg1, arg2))
        return operands.pop()


def _clean_args(
    opc: ShapeOperationCode, *_args: Shape | Surface | Body
) -> tuple[ShapeOperationCode, Sequence[Shape]]:
    """Clean input arguments.

    If arg is a Body, extracts its shape.
    If arg is a Surface, creates a Shape('S',...).

    Try  to reduce levels of operations if only one arg is provided
    or one of the args is Empty or Universe

    Returns
    -------
    opc and args simplified and args being converted to Shape
    """
    shapes_or_surfaces = [a.shape if isinstance(a, Body) else a for a in _args]
    _verify_opc(opc, *shapes_or_surfaces)
    if opc in {"I", "U"}:  # intersect or union
        shapes = [Shape("S", a) if isinstance(a, Surface) else a for a in shapes_or_surfaces]
    else:
        shapes = cast(list[Shape], shapes_or_surfaces)
    if len(shapes) > 1:
        # Extend arguments
        i = 0
        while i < len(shapes):
            if shapes[i].opc == opc:
                a = shapes.pop(i)
                shapes.extend(cast("tuple[Shape, ...]", a.args))
            else:
                i += 1

        i = 0
        while i < len(shapes):
            a = shapes[i]
            if (a.opc == "E" and opc == "I") or (a.opc == "R" and opc == "U"):
                return a.opc, []
            if (a.opc == "E" and opc == "U") or (a.opc == "R" and opc == "I"):
                shapes.pop(i)
                continue
            for b in shapes[i + 1 :]:
                if a.is_complement(b):
                    if opc == "I":
                        return "E", []
                    return "R", []
            i += 1
        # TODO dvp: make args unique: args = list(set(args))
        shapes.sort(key=hash)
        if len(shapes) == 0:
            opc = "E" if opc == "U" else "R"
    if len(shapes) == 1 and isinstance(shapes[0], Shape):
        if opc in {"S", "I", "U"}:
            return shapes[0].opc, cast("tuple[Shape, ...]", shapes[0].args)
        if opc == "C":  # pragma: no branch - opc is restricted here, E/R args rejected above
            item = shapes[0].complement()
            return item.opc, cast("tuple[Shape, ...]", item.args)

    return opc, shapes


def _verify_opc(opc, *args):
    """Checks if such argument combination is valid."""
    if (opc in {"E", "R"}) and len(args) > 0:
        raise ValueError("No arguments are expected.")
    if (opc in {"S", "C"}) and len(args) != 1:
        raise ValueError("Only one operand is expected.")
    if opc in {"I", "U"} and len(args) == 0:
        raise ValueError("Operands are expected.")


class Filler:
    """Represents the FILL option of a cell: the filling universe
    and, optionally, a transformation to be applied to the filling universe.
    """

    __slots__ = ("_universe", "_transformation")

    def __init__(
        self,
        universe: Universe | int | None = None,
        transformation: Transformation | None = None,
    ) -> None:
        """Initialize a Filler.

        Parameters
        ----------
        universe
            The filling universe or its name. If None, the universe
            is to be attached later.

        transformation
            Transformation to be applied to the filling universe.
        """
        self._universe = universe
        self._transformation = transformation

    @property
    def universe(self) -> Universe | int | None:
        """The filling universe or its name."""
        return self._universe

    @universe.setter
    def universe(self, universe: Universe | int | None) -> None:
        self._universe = universe

    @property
    def transformation(self) -> Transformation | None:
        """Transformation to be applied to the filling universe."""
        return self._transformation

    @transformation.setter
    def transformation(self, transformation: Transformation | None) -> None:
        self._transformation = transformation

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Filler)
            and self._universe == other._universe
            and self._transformation == other._transformation
        )

    def __repr__(self) -> str:
        return f"Filler(universe={self._universe}, transformation={self._transformation})"


def _normalize_fill(fill: "Filler | dict[str, Any] | None") -> Filler | None:
    """Convert the legacy FILL options value to a Filler instance."""
    if fill is None or isinstance(fill, Filler):
        return fill
    if isinstance(fill, dict):
        return Filler(universe=fill.get("universe"), transformation=fill.get("transform"))
    raise TypeError(f"Invalid type of the FILL option value: {type(fill)}")


class Body(Card):
    """Represents MCNP cell.

    Parameters
    ----------
    geometry : list or Shape
        Geometry expression. It is either a list of Surface instances and
        operations (reverse Polish notation is used) or Shape object.
    options :
        A set of cell's options.

    Methods
    -------
    intersection(other)
        Returns an intersection of this cell with the other.
    fill(universe)
        Fills this cell by universe.
    simplify(box, split_disjoint, min_volume)
        Simplifies cell description.
    transform(transformation)
        Applies transformation 'transformation' to this cell.
    union(other)
        Returns a union of this cell with the other.
    """

    __slots__ = (
        *CARD_SLOTS,
        "_shape",
        "_mat",
        "_u",
        "_fill",
        "_trcl",
        "_vol",
        "_imp_n",
        "_imp_p",
        "_imp_e",
    )

    def __init__(self, geometry: TGeometry, name: Name | int | None = None, **options) -> None:
        if isinstance(geometry, list):
            geometry = Shape.from_polish_notation(geometry)
        elif isinstance(geometry, Body):
            geometry = geometry.shape
        elif not isinstance(geometry, Shape):
            raise TypeError("Geometry list or Shape is expected.")
        self._mat = options.pop("MAT", None)
        self._u = options.pop("U", None)
        self._fill = _normalize_fill(options.pop("FILL", None))
        self._trcl = options.pop("TRCL", None)
        self._vol = options.pop("VOL", None)
        self._imp_n = options.pop("IMPN", None)
        self._imp_p = options.pop("IMPP", None)
        self._imp_e = options.pop("IMPE", None)
        Card.__init__(self, name, **Card._split_options(options))
        self._shape = geometry

    def _cell_options(self) -> dict[str, Any]:
        """Transitional: the cell-level attributes in the legacy options dictionary form.

        Used to propagate the cell-level attributes to derived objects
        the way the whole options dictionary was propagated before.
        """
        result: dict[str, Any] = {}
        if self._mat is not None:
            result["MAT"] = self._mat
        if self._u is not None:
            result["U"] = self._u
        if self._fill is not None:
            result["FILL"] = self._fill
        if self._trcl is not None:
            result["TRCL"] = self._trcl
        if self._vol is not None:
            result["VOL"] = self._vol
        if self._imp_n is not None:
            result["IMPN"] = self._imp_n
        if self._imp_p is not None:
            result["IMPP"] = self._imp_p
        if self._imp_e is not None:
            result["IMPE"] = self._imp_e
        if self._extra:
            result.update(self._extra)
        return result

    def __repr__(self):
        options = self._cell_options()
        options_str = str(options) if options else ""
        return f"Body({self._shape}, {options_str})"

    def __iter__(self):
        return iter(self._shape)

    def __hash__(self) -> int:
        return Card.__hash__(self) ^ hash(self._shape)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Body)
            and Card.__eq__(self, other)
            and self._shape == other._shape
            and self._mat == other._mat
            and self._u == other._u
            and self._fill == other._fill
            and self._trcl == other._trcl
            and self._vol == other._vol
            and self._imp_n == other._imp_n
            and self._imp_p == other._imp_p
            and self._imp_e == other._imp_e
        )

    @property
    def shape(self) -> Shape:
        """Get this cell geometry specification."""
        return self._shape

    @property
    def mat(self) -> mm.Material | None:
        """The material of this cell (the MAT option)."""
        return self._mat

    @mat.setter
    def mat(self, mat: mm.Material | None) -> None:
        self._mat = mat

    @property
    def universe(self) -> "Universe | int | None":
        """The universe this cell belongs to (the U option)."""
        return self._u

    @universe.setter
    def universe(self, universe: "Universe | int | None") -> None:
        self._u = universe

    @property
    def fill(self) -> Filler | None:
        """The filling universe specification (the FILL option)."""
        return self._fill

    @fill.setter
    def fill(self, fill: Filler | None) -> None:
        self._fill = fill

    @property
    def transformation(self) -> Transformation | None:
        """Get this cell transformation."""
        return self._trcl

    @property
    def is_empty(self) -> bool:
        """Check if the body is empty.

        Returns
        -------
        True, if this body is empty, False otherwise.
        """
        return self._shape.is_empty()

    @property
    def is_graveyard(self) -> bool:
        """Check if this cell is in a graveyard.

        The graveyard cells have zero importance for all the kinds of particles.

        Returns
        -------
        True, if all cell is of zero importance for all the kinds of particles, otherwise - False
        """
        # noinspection PyTypeChecker
        # pyrefly: ignore[bad-argument-type]
        return all(self.importance(c) == 0.0 for c in ["N", "P", "E"])  # pyright: ignore[reportArgumentType]

    def importance(self, particle: Literal["N", "P", "E"] = "N") -> float:
        """Retrieve importance of a cell for a particle kind.

        Parameters
        ----------
        particle
            kind

        Returns
        -------
        The importance value, if specified, zero otherwise.
        """
        value = {"N": self._imp_n, "P": self._imp_p, "E": self._imp_e}.get(particle)
        return 0.0 if value is None else value

    def is_equivalent_to(self, other):
        result = self.shape == other.shape
        if result and self._fill is not None:
            if other._fill is None:
                return False
            my = self._fill.universe
            their = other._fill.universe
            return my.has_equivalent_cells(their)
        return result

    # TODO @dvp: the method is used for printing, we'd better introduce virtual method print(self, out: TextIO)?
    # TODO @dvp: in that case we could just return original text if available
    def mcnp_words(self, pretty=False) -> list[str]:
        words = [str(self.name()), " "]
        if self._mat is not None:
            words.append(str(self._mat.composition.name()))
            words.append(" ")
            words.append(str(-self._mat.density))
            words.append(" ")
        else:
            words.append("0")
            words.append(" ")
        words.extend(self._shape.get_words())
        words.append("\n")
        # insert options printing
        words.extend(self._options_list())
        for line in self.comment or []:
            words.append("$ " + str(line))
            words.append("\n")
        return words

    def _options_list(self):
        """Generates a list of option words.

        For __str__ method.
        """
        text = []
        options = self._cell_options()
        for key in CELL_OPTIONS:
            if key in options:
                text.extend(print_option(key, options[key]))
                text.append(" ")
        text.append("\n")
        return text

    def material(self) -> mm.Material | None:
        """Gets body's Material.

        Returns
        -------
        The material, if present, otherwise None

        Raises
        ------
        ValueError: if type of material object is not Material
        """
        composition = self._mat
        if composition is None or isinstance(composition, mm.Material):
            return composition
        msg = f"Unexpected type of composition: {type(composition)}"
        raise ValueError(msg)

    def intersection(self, other) -> Body:
        """Gets an intersection if this cell with the other.

        Other cell is a geometry that bounds this one. The resulting cell
        inherits all options of this one (the caller).

        Args:
            other:  Other cell.

        Returns
        -------
            The cell representing the intersection.
        """
        geometry = self._shape.intersection(other)
        return Body(
            geometry,
            name=self._name,
            **self._card_options(drop_original=True),
            **self._cell_options(),
        )

    def union(self, other: Body) -> Body:
        """Gets a union if this cell with the other.

        The resulting cell inherits all options of this one (the caller).

        Args:
            other: Other cell.

        Returns
        -------
            cell: The result.
        """
        geometry = self._shape.union(other)
        return Body(
            geometry,
            name=self._name,
            **self._card_options(drop_original=True),
            **self._cell_options(),
        )

    def simplify(
        self,
        box: Box = GLOBAL_BOX,
        split_disjoint: bool = False,
        min_volume: float = MIN_BOX_VOLUME,
        trim_size: int = 1,
    ) -> Body:
        """Simplifies this cell by removing unnecessary surfaces.

        The simplification procedure goes in the following way.
        # TODO: insert brief description!

        Args:
            box:
                Box where geometry should be simplified.
            split_disjoint:
                Whether to split disjoint geometries into separate geometries.
            min_volume:
                The smallest value of box's volume when the process of box splitting must be stopped.
            trim_size:
                Max size of set to return. It is used to prevent unlimited growth
                of the variant set.

        Returns
        -------
            Simplified version of this cell.
        """
        self._shape.collect_statistics(box, min_volume)
        variants = self._shape.get_simplest(trim_size)

        return Body(
            variants[0],
            name=self._name,
            **self._card_options(drop_original=True),
            **self._cell_options(),
        )

    def split(self, box: Box = GLOBAL_BOX, min_volume: float = MIN_BOX_VOLUME) -> list[Body]:
        """Splits cell into disjoint cells.

        Returns
        -------
            cells list
        """
        self.shape.collect_statistics(box, min_volume)
        shape_groups = self.shape.split_shape()
        return [
            Body(
                shape,
                name=self._name,
                **self._card_options(),
                **self._cell_options(),
            )
            for shape in shape_groups
        ]

    # noinspection PyShadowingNames
    def fill(
        self,
        universe: Universe | None = None,
        *,
        recurrent: bool = False,
        simplify: bool = False,
        split_disjoint: bool = False,
        min_volume: float = MIN_BOX_VOLUME,
        trim_size: int = 1,
    ) -> list[Body]:
        """Fills this cell by filling universe.

        If this cell doesn't contain fill options and universe is not
        specified, the cell itself is returned as list of length 1. Otherwise:
        a list of cells from filling universe bounded by cell being filled is
        returned.

        Parameters
        ----------
        universe:
            Universe which cells fill this one. If None, universe from 'FILL'
            option will be used. If no such universe, the cell itself will be
            returned. Default: None.
        recurrent:
            If filler universe also contains cells with fill option, they will
            be also filled. Default: False.
        simplify:
            If True, all cells obtained will be simplified.
        split_disjoint
            for simplify
        min_volume
            for simplify
        trim_size
            for simplify

        Returns
        -------
            The list of resulting cells.
        """
        if universe is None:
            if self._fill is not None:
                universe = cast("Universe", self._fill.universe)
                tr = self._fill.transformation
                if tr:
                    universe = universe.transform(tr)
            else:
                return [self]
        # Note: `recurrent` is implemented by filling cells of the filling universe first.
        if recurrent:
            source_cells: Iterable[Body] = [
                filled_cell
                for filling_cell in universe
                for filled_cell in filling_cell.fill(
                    recurrent=True,
                    simplify=simplify,
                    split_disjoint=split_disjoint,
                    min_volume=min_volume,
                    trim_size=trim_size,
                )
            ]
        else:
            source_cells = universe
        cells = []
        for c in source_cells:
            new_cell = c.intersection(self)  # because properties like MAT, etc
            # must be as in filling cell.
            if self._u is not None:
                new_cell.universe = self._u  # except universe.
            if simplify:
                new_cell = new_cell.simplify(
                    split_disjoint=split_disjoint, min_volume=min_volume, trim_size=trim_size
                )
            cells.append(new_cell)
        return cells

    def transform(self, transformation: Transformation) -> Body:
        """Applies transformation to this cell.

        Args:
            transformation: Transformation to be applied.

        Returns
        -------
            The result of this cell transformation.
        """
        geometry = self._shape.transform(transformation)
        cell = Body(
            geometry,
            name=self._name,
            **self._card_options(drop_original=True),
            **self._cell_options(),
        )
        fill = cell._fill
        if fill is not None:
            tr_in = fill.transformation
            new_tr = transformation if tr_in is None else transformation.apply2transform(tr_in)
            fill.transformation = new_tr
        return cell

    def apply_transformation(self) -> Body:
        """Actually apply transformation to this cell."""
        geometry = self._shape.apply_transformation()
        cell = Body(
            geometry,
            name=self._name,
            **self._card_options(drop_original=True),
            **self._cell_options(),
        )
        fill = cell._fill
        if fill is not None:
            tr_in = fill.transformation
            filling_universe = fill.universe
            new_filling_universe = (
                deepcopy(filling_universe).transform(tr_in).apply_transformation()
            )
            cell.fill = Filler(universe=new_filling_universe)
            # TODO dvp: this should create a lot of cell clashes on complex models with multiple filling with
            #           one universe. Should be resolved before saving.
        return cell


def simplify(
    cells: Iterable[Body], box: Box = GLOBAL_BOX, min_volume: float = 1.0
) -> Iterator[Body]:
    """Simplifies the cells.

    Args:
        cells:
            iterable over cells to simplify
        box :
            Box, from which simplification process starts. Default: GLOBAL_BOX.
        min_volume : float
            Minimal volume of the box, when splitting process terminates.
    """
    for c in cells:
        cs = c.simplify(box=box, min_volume=min_volume)
        if not cs.shape.is_empty():
            yield cs


class Simplifier:
    def __init__(self, box: Box = GLOBAL_BOX, min_volume: float = 1.0):
        self.box = box
        self.min_volume = min_volume

    def __call__(self, cell: Body):
        return cell.simplify(box=self.box, min_volume=self.min_volume)

    def __getstate__(self):
        return self.box, self.min_volume

    def __setstate__(self, state):
        box, min_volume = state
        self.__init__(box, min_volume)


def simplify_mp(
    cells: Iterable[Body], box: Box = GLOBAL_BOX, min_volume: float = 1.0, chunk_size=1
) -> Iterator[Body]:
    """Simplifies the cells in multiprocessing mode.

    Parameters
    ----------
    cells:
        iterable over cells to simplify
    box :
        Box, from which simplification process starts. Default: GLOBAL_BOX.
    min_volume : float
        Minimal volume of the box, when splitting process terminates.
    chunk_size: size of chunks to pass to child processes
    """
    cpus = os.cpu_count()
    with Pool(processes=cpus) as pool:
        yield from pool.imap(
            Simplifier(box=box, min_volume=min_volume), cells, chunksize=chunk_size
        )


def simplify_mpp(
    cells: Iterable[Body],
    box: Box = GLOBAL_BOX,
    min_volume: float = 1.0,
    chunk_size: int = 1,
) -> Iterator[Body]:
    """Simplifies the cells in multiprocessing mode with progress bar.

    Args:
        cells:
            iterable over cells to simplify
        box:
            Box, from which simplification process starts. Default: GLOBAL_BOX.
        min_volume:
            Minimal volume of the box, when splitting process terminates.
        chunk_size:
            size of chunks to pass to child processes
    """

    def fmt_fun(x):
        return f"Simplifying cell #{x.name() if x else x}"

    with progressbar(simplify_mp(cells, box, min_volume, chunk_size), item_show_func=fmt_fun) as pb:
        yield from pb
