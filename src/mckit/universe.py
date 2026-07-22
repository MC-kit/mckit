"""Classes and methods to work with MCNP universe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, SupportsIndex, cast

import sys

from collections import defaultdict
from collections.abc import Callable, Container, Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from functools import reduce
from io import StringIO
from itertools import chain
from logging import getLogger
from pathlib import Path

import numpy as np

from click import progressbar

from mckit.utils import filter_dict

from .body import Body, Shape
from .box import GLOBAL_BOX, Box
from .material import Composition, Material
from .surface import Plane, Surface
from .transformation import Transformation
from .utils import accept, on_unknown_acceptor

if TYPE_CHECKING:
    from .types import NPFloat64Array, NPInt32Array

__all__ = [
    "NameClashError",
    "Universe",
    "UniverseAnalyser",
    "cell_selector",
    "collect_transformations",
    "produce_universes",
    "surface_selector",
]

from .utils.indexes import IndexOfNamed, StatisticsCollector
from .utils.named import Name, default_name_key, map_names

ZERO_NAME = cast(Name, 0)

_LOG = getLogger("mckit.universe")


Replaceable = Surface | Composition


class NameClashError(ValueError):
    """Exception to present information on name clashes over universes."""

    def __init__(self, clashes: str | dict[str, dict[Name, set[Universe]]]) -> None:
        if isinstance(clashes, str):
            ValueError.__init__(self, clashes)
        else:
            msg = StringIO()
            msg.write("\n")
            for kind, index in clashes.items():
                for i, universes in index.items():
                    universes_names = [u.name() for u in universes]
                    msg.write(f"{kind} {i} is found in universes {universes_names}\n")
            ValueError.__init__(self, msg.getvalue())


def cell_selector(cell_names: int | Iterable[int]) -> Callable[[Body], list[Body]]:
    """Produces cell selector function for specific cell names.

    Args:
        cell_names:
            Names of cells to be selected.

    Returns
    -------
        Selector function.
    """
    if isinstance(cell_names, int):

        def selector(cell: Body) -> list[Body]:
            if cell.name() == cell_names:
                return [cell]
            return []

    else:
        # TODO @dvp: no need to create set here, caller can provide better container with fast search
        cell_names = set(cell_names)

        def selector(cell: Body) -> list[Body]:
            if cell.name() in cell_names:
                return [cell]
            return []

    return selector


def surface_selector(surface_names: int | Container[int]) -> Callable[[Body], list[Surface]]:
    """Produces surface selector function for specific surface names.

    Parameters
    ----------
    surface_names
        Names of surfaces (or a single name) to be selected.

    Returns
    -------
    Selector function
    """
    if isinstance(surface_names, int):

        def selector(cell: Body) -> list[Surface]:
            surfs = cell.shape.scan_surfaces()
            return [s for s in surfs if s.name() == surface_names]
    elif isinstance(surface_names, Container):

        def selector(cell: Body) -> list[Surface]:
            surfs = cell.shape.scan_surfaces()
            return [
                s
                for s in surfs
                # pyrefly: ignore[not-iterable]
                if cast(Name, s.name()) in surface_names  # ty: ignore unsupported-operator
            ]
    else:
        msg = f"Invalid type of surface_names parameter: {type(surface_names)}"  # type: ignore[unreachable]
        raise TypeError(msg)

    return selector


class Universe:
    """Describes universe - a set of cells.

    Universe is a list of cells. Each cell can be filled
    with other universe. In this case, cells of other (inner) universe are bounded by
    cell being filled.

    Parameters
    ----------
    cells : iterable
        A list of cells this universe consist of.
    name : int
        Name of the universe, usually used in MCNP. 0 - means global universe.
    verbose_name : str
        Optional verbose name. This name also can be used to retrieve inner
        universe.
    comment : list[str] or str
        String or list of strings that describes the universe.
    common_materials : set
        A set of common materials. Default: None.

    Methods
    -------
    add_cells(cell)
        Adds new cell to the universe.
    apply_fill(cell, universe)
        Applies fill operations to all or selected cells or universes.
    bounding_box(tol, box)
        Gets bounding box of the universe.
    copy()
        Makes a copy of the universe.
    find_common_materials()
        Finds all common materials among universes.
    get_surfaces()
        Gets all surfaces of the universe.
    get_materials()
        Gets all materials of the universe.
    get_compositions()
        Gets all compositions of the universe.
    get_transformations()
        Gets all transformations of the universe.
    get_universes()
        Gets all inner universes.
    name()
        Gets numeric name of the universe.
    name_clashes()
        Checks if there is name clashes.
    rename(start_cell, start_surf, start_mat, start_tr)
        Renames all entities contained in the universe.
    save(filename)
        Saves the universe to file.
    select(cell, selector)
        Selects specified entities.
    set_common_materials(com_mat)
        Sets new common materials for universe and all nested universes.
    simplify(box, split_disjoint, min_volume)
        Simplifies all cells of the universe.
    test_points(points)
        Tests to which cell each point belongs.
    verbose_name()
        Gets verbose name of the universe.
    """

    def __init__(
        self,
        cells: list[Body],
        name: Name = ZERO_NAME,
        verbose_name: str | None = None,
        comment: str | None = None,
        name_rule: Literal["new", "keep", "clash"] = "keep",
        common_materials: set[Composition] | None = None,
    ):
        self._name = name
        self._comment = comment
        self._verbose_name = verbose_name
        self._cells: list[Body] = []
        if common_materials is None:
            common_materials = set()
        self._common_materials = common_materials

        self.add_cells(cells, name_rule=name_rule)

    @property
    def cells(self):
        return self._cells

    def __iter__(self):
        return iter(self._cells)

    def __len__(self):
        return len(self._cells)

    def __setitem__(self, key: int, value: Body):
        raise NotImplementedError("Renaming rules should be applied.")

    def __getitem__(self, item: SupportsIndex):
        return self._cells.__getitem__(item)

    def __str__(self):
        return f"Universe(name={self.name()})"

    def has_equivalent_cells(self, other: Universe) -> bool:
        if len(self) != len(other):
            return False
        return all(c.is_equivalent_to(other[i]) for i, c in enumerate(self))

    def add_cells(
        self, cells: list[Body] | Body, name_rule: Literal["new", "keep", "clash"] = "new"
    ) -> None:
        """Adds new cell to the universe.

        Modifies current universe.

        Args:
            cells: An array of cells to be added to the universe.
            name_rule: Rule, what to do with entities' names:
                 - 'keep' - keep all names; in case of clashes NameClashError exception is raised.
                 - 'clash' - rename entity only in case of name clashes.
                 - 'new' - set new sequential name to all inserted entities.
        """
        if isinstance(cells, Body):
            cells = [cells]

        surfs = self.get_surfaces()
        surf_replace = {s: s for s in surfs}
        comps = self._common_materials.union(self.get_compositions())
        comp_replace = {c: c for c in comps}
        cell_names: set[Name] = {default_name_key(c) for c in self}
        surf_names: set[Name] = {default_name_key(s) for s in surfs}
        comp_names: set[Name] = {default_name_key(c) for c in comps}

        for cell in cells:
            if cell.shape.is_empty():
                continue

            new_shape = self._get_cell_replaced_shape(cell, surf_replace, surf_names, name_rule)

            new_cell = Body(new_shape, **cell.options)
            mat = new_cell.material()

            if mat:
                new_comp = cast(
                    Composition,
                    Universe._update_replace_dict(
                        mat.composition,
                        cast(dict[Replaceable, Replaceable], comp_replace),
                        comp_names,
                        name_rule,
                        "Material",
                    ),
                )
                new_cell.options["MAT"] = Material(composition=new_comp, density=mat.density)

            if name_rule == "keep" and cell.name() in cell_names:
                msg = f"Cell name clash: {cell.name()}"
                raise NameClashError(msg)

            if name_rule == "new" or (name_rule == "clash" and cell.name() in cell_names):
                new_name = max(cell_names, default=0) + 1
                new_cell.rename(cast(Name, new_name))

            cell_names.add(cast(Name, new_cell.name()))
            new_cell.options["U"] = self
            self._cells.append(new_cell)

    def set_common_materials(self, common_materials):
        """Sets common materials for this one and all nested universes.

        Parameters
        ----------
        common_materials : set
            A set of common materials.
        """
        universes = self.get_universes()
        for u in universes:
            u._set_common_materials(common_materials)

    def _set_common_materials(self, common_materials):
        """Sets common materials for individual universe.

        Parameters
        ----------
        common_materials : set
            A set of common_materials
        """
        self._common_materials = common_materials
        cmd = {m: m for m in common_materials}
        for c in self:
            mat = c.material()
            if mat:
                comp = mat.composition
                if comp in common_materials:
                    c.options["MAT"] = Material(composition=cmd[comp], density=mat.density)

    @staticmethod
    def _get_cell_replaced_shape(
        cell: Body,
        surf_replace: dict[Surface, Surface],
        surf_names: set[Name],
        name_rule: Literal["keep", "new", "clash"],
    ) -> Shape:
        cell_surfs = cell.shape.get_surfaces()
        replace_dict: dict[Surface, Surface] = {}
        for s in cell_surfs:
            if isinstance(s, Plane):
                rev_s = s.reverse()  #  Plane(-s._v, -s._k)
                if rev_s in surf_replace:
                    # dvp: use reverse of a Plane, if already present
                    rev_s = surf_replace[rev_s]
                    replace_dict[s] = Shape("C", rev_s)
                    continue
            replace_dict[s] = cast(
                Surface,
                Universe._update_replace_dict(
                    s,
                    cast(dict[Replaceable, Replaceable], surf_replace),
                    surf_names,
                    name_rule,
                    "Surface",
                ),
            )
        return cell.shape.replace_surfaces(replace_dict)

    @staticmethod
    def _update_replace_dict(
        entity: Replaceable,
        replace: dict[Replaceable, Replaceable],
        names: set[Name],
        rule: Literal["keep", "new", "clash"],
        err_desc: str,
    ) -> Replaceable:
        if entity in replace:
            return replace[entity]

        new_entity = entity.copy()

        if rule == "keep" and new_entity.name() in names:
            msg = f"{err_desc} name clash: {entity.name()}"
            _LOG.error(msg)
            _LOG.error("Failed entity:")
            _LOG.error(entity.mcnp_repr())
            _LOG.error("Replacements:")
            for c in replace:
                _LOG.error(c.mcnp_repr())
            raise NameClashError(msg)

        if rule == "new" or (rule == "clash" and new_entity.name() in names):
            new_name = max(names, default=0) + 1
            new_entity.rename(cast(Name, new_name))

        replace[new_entity] = new_entity
        names.add(cast(Name, new_entity.name()))

        return new_entity

    @staticmethod
    def _fill_check(predicate: Callable[[Body], bool]) -> Callable[[Body], bool]:
        def _predicate(cell):
            fill = cell.options.get("FILL", None)
            if fill:
                return predicate(cell)
            return False

        return _predicate

    def alone(self) -> Universe:
        """Gets this universe alone, without inner universes.

        Returns
        -------
            A copy of the universe with FILL cards removed.
        """
        cells = []

        for c in self:
            options = {k: v for k, v in c.options.items() if k != "FILL"}
            cells.append(Body(c.shape, **options))

        return Universe(cells)

    def apply_fill(
        self,
        cell: Body | int | None = None,
        universe: Universe | int | None = None,
        predicate: Callable[[Body], bool] | None = None,
    ) -> None:
        """Applies fill operations to all or selected cells or universes.

        Modifies current universe.

        Args:
            cell:
                Cell or name of cell which is filled by filling universe. The cell
                can only belong to this universe. Cells of inner universes are not
                taken into account.
            universe:
                Filler-universe or its name. Cells, that have this universe as a
                filler will be filled. Only cells of this universe will be checked.
            predicate:
                Function that accepts Body instance and return True, if this cell
                must be filled.
        """
        if predicate is None:
            if cell is not None:
                if isinstance(cell, Body):
                    cell = cell.name()

                def _predicate(_c: Body, /) -> bool:
                    return _c.name() == cell
            elif universe is not None:
                if isinstance(universe, Universe):
                    universe = universe.name()

                def _predicate(_c: Body, /) -> bool:
                    return cast(int, _c.options["FILL"]["universe"].name()) == universe
            else:

                def _predicate(_c: Body, /) -> bool:
                    return True
        else:
            _predicate = predicate

        _predicate = self._fill_check(_predicate)  # ty: ignore conflicting-declarations
        extra_cells = []
        del_indices = []
        for i, c in enumerate(self):
            if _predicate(c):
                extra_cells.extend(c.fill())
                del_indices.append(i)
        for i in reversed(del_indices):
            self._cells.pop(i)
        self.add_cells(extra_cells, name_rule="new")

    def bounding_box(
        self,
        tol: float = 100.0,
        box: Box = GLOBAL_BOX,
        skip_graveyard_cells: bool = False,
    ) -> Box:
        """Gets bounding box for the universe.

        It finds all bounding boxes for universe cells and then constructs
        box, that covers all cells' bounding boxes. The main purpose of this
        method is to find boundaries of the model geometry to compare
        transformation and surface objects for equality. It is recommended to
        choose tol value not too small to reduce computation time.

        Args:
            tol:
                Linear tolerance for the bounding box. The distance [in cm] between
                every box's surface and universe in every direction won't exceed
                this value. Default: 100 cm.
            box:
                Starting box for the search. The user must be sure that box covers
                all geometry, because cells, that already contains corners of the
                box will be considered as infinite and will be excluded from
                analysis.
            skip_graveyard_cells:
                Don't compute boxes for 'graveyard' cells (with zero importance for all the kinds of particles).

        Returns
        -------
            Universe bounding box.
        """
        # TODO @dvp: очень неэффективное решение, незачем запоминать
        #            все boxes, достаточно вычислить lo- и up-corners
        # TODO @dvp: make the cycle parallel
        boxes = []
        for c in self._cells:
            if skip_graveyard_cells and c.is_graveyard:
                continue
            test = c.shape.test_points(box.corners)
            if np.any(test == +1):
                continue
            boxes.append(c.shape.bounding_box(tol=tol, box=box))
        all_corners = np.empty((8 * len(boxes), 3))
        for i, b in enumerate(boxes):
            all_corners[i * 8 : (i + 1) * 8, :] = b.corners
        min_pt = np.min(all_corners, axis=0)
        max_pt = np.max(all_corners, axis=0)
        center = 0.5 * (min_pt + max_pt)
        dims = max_pt - min_pt
        return Box(center, *dims)

    def copy(self):
        """Makes a copy of the universe."""
        return Universe(
            self._cells,
            name=self._name,
            verbose_name=self._verbose_name,
            comment=self._comment,
            common_materials=self._common_materials,
        )

    def find_common_materials(self):
        """Finds common materials among universes included.

        Returns
        -------
            A set of common materials.
        """
        comp_count = defaultdict(int)
        for u in self.get_universes():
            for c in u.get_compositions():
                comp_count[c] += 1
        return {c for c, cnt in comp_count.items() if cnt > 1}

    def get_surfaces(self, inner: bool = False) -> set[Surface]:
        """Gets all surfaces of the universe.

        Args:
            inner:  Whether to take surfaces of inner universes. Default: False -
                    return surfaces of this universe only.

        Returns
        -------
            A set of surfaces that belong to the universe.
        """
        return set(self.scan_surfaces(inner=inner))

    def scan_surfaces(self, *, inner: bool = False) -> Generator[Surface]:
        """Gets all surfaces of the universe.

        Parameters
        ----------
        inner
            Whether to take surfaces of inner universes.
            Default: False - return surfaces of this universe only.

        Yields
        ------
        Surfaces, that belong to the universe.
        """
        for c in self:
            yield from c.shape.scan_surfaces()
            if inner and "FILL" in c.options:
                yield from c.options["FILL"]["universe"].scan_surfaces(inner=inner)

    def get_surfaces_list(self, inner: bool = False):
        return list(self.scan_surfaces(inner=inner))

    def get_compositions(self, exclude_common: bool = False) -> set[Composition]:
        """Gets all compositions of the universe.

        Args:
            exclude_common :  Exclude common compositions from the result. Default: False.

        Returns
        -------
            A set of Composition objects.
        """
        compositions = set()
        for c in self:
            material = c.material()
            if material:
                compositions.add(material.composition)
        if exclude_common:
            compositions.difference_update(self._common_materials)
        return compositions

    def get_universes(self) -> set[Universe]:
        """Gets set of self and all inner universes.

        Returns
        -------
            A set of all the universes.
        """
        universes: set[Universe] = {self}
        for c in self:
            if "FILL" in c.options:
                u = c.options["FILL"]["universe"]
                universes.update(u.get_universes())
        return universes

    def name(self) -> Name:
        """Gets numeric name of the universe."""
        return self._name

    def name_clashes(self) -> dict[str, dict[Name, set[Universe]]]:
        """Checks, if there is name clashes.

        Returns
        -------
            Description of found clashes. If no clashes - the dictionary is empty.
        """
        universes = self.get_universes()
        universe_to_cell_name_map = {u: cast(list[Name], list(map_names(u))) for u in universes}
        universe_to_surface_name_map = {
            u: cast(list[Name], list(map_names(u.get_surfaces())))
            for u in universes  # use get_surfaces() for unique names
        }
        # noinspection PyTypeChecker
        mats: dict[Universe | None, list[Name]] = {
            None: cast(list[Name], list(map_names(self._common_materials)))
        }
        for u in universes:
            mats[u] = cast(
                list[Name], list(map_names(u.get_compositions().difference(self._common_materials)))
            )
        universe_to_name_dummy = {u: [u.name()] for u in universes}
        cell_stat = Universe._produce_stat(universe_to_cell_name_map)
        stat = {}
        if cell_stat:
            stat["cell"] = cell_stat
        surface_stat = Universe._produce_stat(universe_to_surface_name_map)
        if surface_stat:
            stat["surf"] = surface_stat
        materials_stat = Universe._produce_stat(cast(dict[Universe, list[Name]], mats))
        if materials_stat:
            stat["material"] = materials_stat
        universe_stat = Universe._produce_stat(universe_to_name_dummy)
        if universe_stat:
            stat["universe"] = universe_stat
        # TODO @dvp: handle transformations here
        return stat

    @staticmethod
    def _produce_stat(names: dict[Universe, list[Name]]) -> dict[Name, set[Universe]]:
        stat = defaultdict(list)
        for u, u_names in names.items():
            for name in u_names:
                stat[name].append(u)
        return {k: set(v) for k, v in stat.items() if len(v) > 1}

    def rename(
        self,
        start_cell: int | None = None,
        start_surf: int | None = None,
        start_mat: int | None = None,
        start_tr: int | None = None,
        name: int | None = None,
    ) -> None:
        """Renames all entities contained in the universe.

        All new names are sequential starting from the specified name.
        If an argument is None, then names of corresponding entities are leaved untouched.

        Parameters
        ----------
        start_cell
            Starting name for cells. Default: None.
        start_surf
            Starting name for surfaces. Default: None.
        start_mat
            Starting name for materials. Default: None.
        start_tr
            Starting name for transformations. Default: None.
        name
            ... for the universe. Default: None.
        """
        # TODO dvp: implement transformations renaming
        assert start_tr is None, "Transformation renaming is not implemented yet"
        if name is not None:  # name may be 0 to convert this to root universe
            if name < 0:
                msg = f"Universe name {name} < 0"
                raise ValueError(msg)
            self._name = cast(Name, name)
            self._verbose_name = None
            for c in self:
                c.options = filter_dict(c.options, "original")
        if start_cell is not None:
            t: int = start_cell
            for c in self:
                c.rename(cast(Name, t))
                # TODO @dvp: add check, if there's no filling subuniverses in the cells
                #            if, there are fills, then what to do with cells in them?
                #            what if filling universe occurs multiple times?
                t += 1
        if start_surf is not None:
            surfs = self.get_surfaces()
            # TODO @dvp: using set and sorted change the order of surfaces, do we need this?
            #            may be we need just scan the surfaces
            for s in sorted(surfs, key=_key):
                s.rename(cast(Name, start_surf))
                start_surf += 1
        if start_mat is not None:
            mats = self.get_compositions()
            for m in sorted(mats, key=_key):
                if m not in self._common_materials:
                    m.rename(cast(Name, start_mat))
                    start_mat += 1

    def check_clashes(self) -> None:
        result = self.name_clashes()
        if result:
            raise NameClashError(result)

    def save(
        self,
        filename: str | Path,
        encoding: str = "utf8",
        check_clashes: bool = True,
    ):
        """Saves the universe into file."""
        # NOTE dvp: Don't try to resolve names here, the object shouldn't change on save() function.
        # self.check_clashes()

        if check_clashes:
            analyser = UniverseAnalyser(self)
            if not analyser.we_are_all_clear():
                out = StringIO()
                out.write("Duplicates found:\n")
                analyser.print_duplicates_map(stream=out)
                raise NameClashError(out.getvalue())

        transformations_set = collect_transformations(self)
        if transformations_set:
            transformations = sorted(transformations_set, key=_key)
        else:
            transformations = None
        universes = self.get_universes()
        cells: list[Body] = []
        surfaces: list[Surface] = []
        materials = sorted(self._common_materials, key=_key)

        for u in sorted(universes, key=_key):
            cells.extend(sorted(u, key=lambda x: cast(Name, x.name())))
            surfaces.extend(sorted(u.get_surfaces(), key=_key))
            materials.extend(sorted(u.get_compositions(True), key=_key))
        cards: list[str] = [self.verbose_name]
        # TODO @dvp: output comment here prepending each line with "c ", if not present already
        cards.extend(x.mcnp_repr() for x in cells)
        cards.append("")
        cards.extend(x.mcnp_repr() for x in surfaces)
        cards.append("")
        if transformations:
            cards.extend(x.mcnp_repr() for x in transformations)
        if materials:
            cards.extend(x.mcnp_repr() for x in materials)
        cards.append("")
        if isinstance(filename, str):
            filename = Path(filename)
        with filename.open(mode="w", encoding=encoding) as f:
            f.write("\n".join(cards))

    def select(self, selector: Callable[[Body], list[Body | Surface]], inner: bool = False):
        """Selects specified entities.

        Parameters
        ----------
        selector
            A function that accepts 1 argument, Body instance, and returns
            selected entities.
        inner : bool
            Whether to consider inner universes. Default: False - only this
            universe will be taken into account.

        Returns
        -------
        items
            List of selected items.
        """
        items = []
        taken_ids = set()
        for c in self:
            portion = selector(c)
            if inner:
                u = c.options.get("FILL", {}).get("universe")
                if u is not None:
                    portion.extend(u.select(selector, True))
            for item in portion:
                if id(item) not in taken_ids:
                    taken_ids.add(id(item))
                    items.append(item)
        return items

    def simplify(
        self,
        box: Box = GLOBAL_BOX,
        min_volume: float = 1.0,
        split_disjoint: bool = False,
        verbose: bool = True,
    ) -> None:
        """Simplifies all cells of the universe.

        Modifies current universe.

        Parameters
        ----------
        box
            ... from which simplification process starts. Default: GLOBAL_BOX.
        min_volume
            Minimal volume of the box, when splitting process terminates.
        split_disjoint
            Whether to split disjoint cells (not implemented yet).
        verbose
            Turns on verbose output. Default: True.
        """
        new_cells = []
        if verbose:

            def fmt_fun(x):
                return f"Simplifying cell #{x.name() if x else x}"

            # TODO @dvp: bad design, use dependency injection instead direct dependency to click.progressbar
            universe_iterator: Iterable[Body] = progressbar(
                self, item_show_func=fmt_fun
            ).__enter__()
        else:
            universe_iterator = self

        for c in universe_iterator:
            cs = c.simplify(box=box, split_disjoint=split_disjoint, min_volume=min_volume)
            if not cs.shape.is_empty():
                new_cells.append(cs)

        _LOG.info(f"Universe {self.name()} simplification has been finished.")
        _LOG.info(f"{len(self._cells) - len(new_cells)} empty cells were deleted.")

        self._cells = new_cells

    def test_points(self, points: NPFloat64Array) -> NPInt32Array:
        """Finds cell to which each point belongs to.

        Parameters
        ----------
        points:
            An array of point coordinates. If there is only one point it has
            shape (3,); if there are n points, it has shape (n, 3).

        Returns
        -------
        An array of cell indices to which a particular point belongs to.
        Its length equals to the number of points.
        """
        points = np.asarray(points, dtype=float)
        result = np.zeros(points.size // 3, dtype=np.int32)
        for i, c in enumerate(self._cells):
            test = c.shape.test_points(points)
            result[test == +1] = i
        return result

    def transform(self, transformation: Transformation) -> Universe:
        """Applies transformation to this universe.

        Returns
        -------
             a new universe with applied transformation.
        """
        new_cells = [c.transform(transformation).apply_transformation() for c in self]
        return Universe(
            new_cells,
            name=self._name,
            name_rule="clash",
            verbose_name=self._verbose_name,
            comment=self._comment,
        )

    def apply_transformation(self) -> Universe:
        """Applies transformations specified in cells.

        Returns
        -------
             a new universe.
        """
        new_cells = [c.apply_transformation() for c in self]
        return Universe(
            new_cells,
            name=self._name,
            name_rule="clash",
            verbose_name=self._verbose_name,
            comment=self._comment,
        )

    @property
    def verbose_name(self) -> str:
        """Gets verbose name of the universe."""
        return str(self.name()) if self._verbose_name is None else self._verbose_name

    @verbose_name.setter
    def verbose_name(self, value: str):
        if "\n" in value:
            msg = f"Cannot use multiple lines as a universe verbose name. Got: {value}"
            raise ValueError(msg)
        if len(value) > 80:
            msg = f"Too long universe verbose name. Got: {value}"
            raise ValueError(msg)
        self._verbose_name = value

    @property
    def comment(self):
        return self._comment


@dataclass
class _UniverseCellsGroup:
    universe: Universe
    cells: list[Body]


def produce_universes(cells: Iterable[Body]) -> Universe:
    """Creates groups from cells.

    The function groups all the cells by 'universe' option value,
    and creates corresponding groups.

    Parameters
    ----------
    cells
        ... to process.

    Returns
    -------
    universe
        The top level universe with name = 0.
    """
    groups: dict[Name, _UniverseCellsGroup] = {}
    for c in cells:
        universe_no: Name = cast(Name, c.options.get("U", 0))
        if universe_no in groups:
            groups[universe_no].cells.append(c)
        else:
            new_group = _UniverseCellsGroup(universe=Universe([], universe_no), cells=[c])
            groups[universe_no] = new_group
    for c in cells:
        fill: dict[str, Any] | None = c.options.get("FILL")
        if fill is not None:
            fill_universe_no = fill["universe"]
            fill["universe"] = groups[fill_universe_no].universe
    for group in groups.values():
        group.universe.add_cells(group.cells, name_rule="keep")
    top_universe = groups[ZERO_NAME].universe
    top_universe.set_common_materials(top_universe.find_common_materials())
    return top_universe


def collect_transformations(universe: Universe, recursive: bool = True) -> set[Transformation]:
    def add_surface_transformation(aggregator: set[Transformation], surface: Surface) -> None:
        transformation = surface.transformation
        if transformation and transformation.name():
            aggregator.add(transformation)

    def at_surface(
        aggregator: set[Transformation], s: Surface | Shape | Body
    ) -> set[Transformation]:
        if isinstance(s, Surface):
            add_surface_transformation(aggregator, s)
        elif isinstance(s, Shape):
            aggregator.update(accept(s, visit_shape))
        else:
            assert isinstance(s, Body)
            aggregator.update(accept(s, visit_body))
        return aggregator

    @contextmanager
    def visit_shape(
        s: Surface | Body | Shape,
    ) -> Generator[
        tuple[Callable[[set[Transformation], Surface], set[Transformation]], set[Transformation]]
    ]:
        if isinstance(s, Surface | Body | Shape):
            yield at_surface, set()
        else:
            on_unknown_acceptor(s)  # type: ignore[unreachable]

    def at_shape(aggregator: set[Transformation], s: Surface | Body | Shape) -> set[Transformation]:
        if isinstance(s, Surface):
            add_surface_transformation(aggregator, s)
            return aggregator
        aggregator.update(accept(s, visit_shape))
        return aggregator

    @contextmanager
    def visit_body(b: Body):
        if isinstance(b, Body):
            yield at_shape, set()
        else:
            on_unknown_acceptor(b)  # type: ignore[unreachable]

    def at_body(aggregator: set[Transformation], b: Body) -> set[Transformation]:
        body_transformation = b.transformation
        if body_transformation and body_transformation.name():
            aggregator.add(body_transformation)
        if recursive:
            fill = b.options.get("FILL")
            if fill:
                fill_universe = fill["universe"]
                fill_transformation = fill.get("transform")
                if fill_transformation and fill_transformation.name():
                    aggregator.add(fill_transformation)
                aggregator.update(collect_transformations(fill_universe))
        aggregator.update(accept(b, visit_body))
        return aggregator

    @contextmanager
    def visit_universe(
        u: Universe,
    ) -> Generator[
        tuple[Callable[[set[Transformation], Body], set[Transformation]], set[Transformation]]
    ]:
        if isinstance(u, Universe):
            yield at_body, set()
            # TODO dvp:  set() is not a valid choice as aggregator considering
            #        cases when names differ but transformations are equal by values
        else:
            on_unknown_acceptor(u)  # type: ignore[unreachable]

    return cast(set[Transformation], accept(universe, visit_universe))


# TODO dvp: it's possible to generalize visiting introducing class Visitor
#           See: all visit_... functions will be probably not changed on deriving
#           Use functools partial to hide self parameter when passing the method as a function to accept()


# TODO dvp: make names of cards not optional
IU = tuple[list[Name], Name]
"""Entities, Universe name."""

E2U = dict[Name, dict[Name, int]]
"""Map Entity name -> Universe Name -> Count."""


def entity_to_universe_map_reducer(result: E2U, entry: IU) -> E2U:
    entities_names, universe_name = entry

    def inner_reducer(_result: E2U, entity_name: Name) -> E2U:
        _result[entity_name][universe_name] += 1
        return _result

    return reduce(inner_reducer, entities_names, result)


def cells_to_universe_mapper(universe: Universe) -> IU:
    return cast(list[Name], list(map_names(universe))), universe.name()


def surfaces_to_universe_mapper(universe: Universe) -> IU:
    return (
        cast(list[Name], list(map_names(universe.scan_surfaces(inner=False)))),
        universe.name(),
    )


def compositions_to_universe_mapper(universe: Universe) -> IU:
    return (
        cast(list[Name], list(map_names(universe.get_compositions(exclude_common=False)))),
        universe.name(),
    )


def transformations_to_universe_mapper(universe: Universe) -> IU:
    return (
        cast(list[Name], list(map_names(collect_transformations(universe, recursive=False)))),
        universe.name(),
    )


def is_shared_between_universes(item: tuple[Name, dict[Name, int]]) -> bool:
    _, universes_counts = item
    return len(universes_counts.keys()) > 1


def make_universe_counter_map() -> dict[Name, int]:
    return defaultdict(int)


def collect_shared_entities(
    entities_extractor: Callable[[Universe], IU], universes: Iterable[Universe]
) -> E2U:
    return dict(
        filter(
            is_shared_between_universes,
            reduce(
                entity_to_universe_map_reducer,
                map(entities_extractor, universes),
                cast(E2U, defaultdict(make_universe_counter_map)),
            ).items(),
        )
    )


class UniverseAnalyser:
    def __init__(self, universe: Universe) -> None:
        self.universe = universe
        universes = self.universe.get_universes()
        self.universe_duplicates: StatisticsCollector = StatisticsCollector(ignore_equal=True)
        self.universes_index = IndexOfNamed.from_iterable(
            universes,
            on_duplicate=self.universe_duplicates,
        )
        self.cell_duplicates: StatisticsCollector = StatisticsCollector()
        cells: list[Body] = list(chain(*universes))
        self.cell_index = IndexOfNamed[Name, Body].from_iterable(
            cells,
            on_duplicate=self.cell_duplicates,
        )
        self.cell_to_universe_map = collect_shared_entities(cells_to_universe_mapper, universes)
        self.surface_duplicates: StatisticsCollector = StatisticsCollector(ignore_equal=True)
        self.surface_index = IndexOfNamed[Name, Surface].from_iterable(
            universe.get_surfaces_list(inner=True),
            on_duplicate=self.surface_duplicates,
        )
        self.surface_to_universe_map = collect_shared_entities(
            surfaces_to_universe_mapper, universes
        )
        self.composition_duplicates: StatisticsCollector = StatisticsCollector(ignore_equal=True)
        self.composition_index = IndexOfNamed[Name, Composition].from_iterable(
            universe.get_compositions(),
            on_duplicate=self.composition_duplicates,
        )
        self.compositions_to_universe_map = collect_shared_entities(
            compositions_to_universe_mapper, universes
        )
        self.transformation_duplicates: StatisticsCollector = StatisticsCollector(ignore_equal=True)
        self.transformation_index = IndexOfNamed[Name, Transformation].from_iterable(
            collect_transformations(universe, recursive=True),
            on_duplicate=self.transformation_duplicates,
        )
        self.transformations_to_universe_map = collect_shared_entities(
            transformations_to_universe_mapper, universes
        )

    def duplicates(self):
        return (
            self.universe_duplicates,  # equal universes are ignored - they should differ by fill transformation
            self.cell_duplicates,
            self.surface_duplicates,
            self.composition_duplicates,
            self.transformation_duplicates,
        )

    def duplicates_maps(
        self,
    ) -> tuple[
        dict[Name, dict[Name, int]],
        dict[Name, dict[Name, int]],
        dict[Name, dict[Name, int]],
        dict[Name, dict[Name, int]],
    ]:
        return (
            self.cell_to_universe_map,
            self.surface_to_universe_map,
            self.compositions_to_universe_map,
            self.transformations_to_universe_map,
        )

    def we_are_all_clear(self) -> bool:
        return not any(self.duplicates())

    def print_duplicates_map(self, stream=sys.stdout):
        def printer(_, item: tuple[str, E2U]):
            tag, info = item
            entities = sorted(info.keys())
            for e in entities:
                universes_count_map = info[e]
                universes = sorted(universes_count_map.keys())
                print(f"{tag} {e} occurs", file=stream)
                for u in universes:
                    print(
                        f"   in universe {u} {universes_count_map[u]} times",
                        file=stream,
                    )

        reduce(
            printer,
            zip(
                ["cell", "surface", "composition", "transformation"],
                self.duplicates_maps(),
                strict=False,
            ),
            None,
        )


def _key(c: Body | Surface | Composition | Universe | Transformation) -> Name:
    return cast(Name, c.name())
