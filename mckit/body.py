from functools import reduce
from itertools import product

import numpy as np

from .geometry import Shape as _Shape
from .surface import Surface
from .constants import GLOBAL_BOX, MIN_BOX_VOLUME


class Shape(_Shape):
    """Describes shape.

    Parameters
    ----------
    opc : str
        Operation code. Denotes operation to be applied. Possible values:
        'I' - for intersection;
        'U' - for union;
        'C' - for complement;
        'S' - (same) no operation;
        'E' - empty set - no space occupied;
        'R' - whole space.
    args : list of Shape or Surface
        Geometry elements. It can be either Shape or Surface instances. But
        no arguments must be specified for 'E' or 'R' opc. Only one argument
        must present for 'C' or 'S' opc values.

    Returns
    -------
    shape : Shape
        Shape instance.
    """
    _inv_opc = {'I': 'U', 'E': 'R', 'C': 'S', 'U': 'I', 'R': 'E', 'S': 'C'}
    _opc_hash = {'I': hash('I'), 'U': ~hash('I'), 'E': hash('E'), 'R': ~hash('E')}

    def __init__(self, opc, *args):
        opc, args = Shape.clean_args(opc, *args)
        self._args = tuple(args)
        self._opc = opc
        _Shape.__init__(self, opc, *args)
        self._calculate_hash(opc, *args)

    def __hash__(self):
        return self._hash

    @classmethod
    def clean_args(cls, opc, *args):
        cls._verify_opc(opc, *args)
        if len(args) == 1 and isinstance(args[0], Shape) and opc == 'S':
            return args[0]._opc, args[0]._args
        elif len(args) == 1 and isinstance(args[0], Shape) and opc == 'C':
            item = args[0].complement()
            return item._opc, item._args
        elif len(args) > 1:
            # Extend arguments
            args = list(args)
            i = 0
            while i < len(args):
                if args[i]._opc == opc:
                    a = args.pop(i)
                    args.extend(a._args)
                i += 1

            i = 0
            while i < len(args):
                a = args[i]
                if a._opc == 'E' and opc == 'I' or a._opc == 'R' and opc == 'U':
                    return 'E', []
                elif a._opc == 'E' and opc == 'U' or a._opc == 'R' and opc == 'I':
                    args.pop(i)
                    continue
                for j, b in enumerate(args[i + 1:]):
                    if a.is_complement(b):
                        cls.already = True
                        if opc == 'I':
                            return 'E', []
                        else:
                            return 'R', []
                i += 1
            args.sort(key=hash)
        return opc, args

    def __eq__(self, other):
        if self is other:
            return True
        if self._opc != other._opc:
            return False
        if len(self._args) != len(other._args):
            return False
        for a, o in zip(self._args, other._args):
            if not (a == o):
                return False
        return True

    def complement(self):
        """Gets complement to the shape."""
        if self._opc == 'S':
            return Shape('C', self._args[0])
        elif self._opc == 'C':
            return Shape('S', self._args[0])
        elif self._opc == 'E':
            return Shape('R')
        elif self._opc == 'R':
            return Shape('E')
        else:
            opc = self._inv_opc[self._opc]
            args = [a.complement() for a in self._args]
            return Shape(opc, *args)

    def is_complement(self, other):
        """Checks if this shape is complement to the other."""
        if hash(self) != ~hash(other):
            return False
        if self._opc != self._inv_opc[other._opc]:
            return False
        if len(self._args) != len(other._args):
            return False
        if len(self._args) == 1:
            return self._args[0] == other._args[0]
        elif len(self._args) > 1:
            for a in self._args:
                for b in other._args:
                    if a.is_complement(b):
                        break
                else:
                    return False
        return True

    def _calculate_hash(self, opc, *args):
        """Calculates hash value for the object.

        Hash is 'xor' for hash values of all arguments together with opc hash.
        """
        if opc == 'C':  # C and S can be present only with Surface instance.
            self._hash = ~hash(args[0])
        elif opc == 'S':
            self._hash = hash(args[0])
        else:
            self._hash = self._opc_hash[opc]
            for a in args:
                self._hash ^= hash(a)

    def intersection(self, *other):
        """Gets intersection with other shape."""
        return Shape('I', self, *other)

    def union(self, *other):
        """Gets union with other shape."""
        return Shape('U', self, *other)

    def transform(self, tr):
        opc = self._opc
        args = []
        for a in self._args:
            args.append(a.transform(tr))
        return Shape(opc, *args)

    @staticmethod
    def _verify_opc(opc, *args):
        """Checks if such argument combination is valid."""
        if (opc == 'E' or opc == 'R') and len(args) > 0:
            raise ValueError("No arguments are expected.")
        elif (opc == 'S' or opc == 'C') and len(args) != 1:
            raise ValueError("Only one operand is expected.")
        elif opc == 'I' or opc == 'U':
            if len(args) == 0:
                raise ValueError("Operands are expected.")
            for a in args:
                if not isinstance(a, Shape):
                    raise TypeError("Shape instance is expected for 'I' and 'U' operations.")

    def get_simplest(self, trim_size=0):
        if self._opc != 'I' and self._opc != 'U':
            return [self]
        node_cases = []
        complexities = []
        stat = self.get_stat_table()
        if self._opc == 'I':
            val = -1
        elif self._opc == 'U':
            val = +1
        else:
            return {self}

        drop_index = np.nonzero(np.all(stat == val, axis=1))[0]
        if len(drop_index) == 0:
            if self._opc == 'I':
                return [Shape('E')]
            if self._opc == 'U':
                return [Shape('R')]

        arg_results = np.delete(stat, drop_index, axis=0)
        final_cases = self.find_coverages(arg_results, value=val)
        if len(final_cases) == 0:
            print(self)
            return None
        unique = reduce(set.union, map(set, final_cases))
        node_variants = {i: self._args[i].get_simplest(trim_size) for i in unique}
        for indices in final_cases:
            variants = [node_variants[i] for i in indices]
            for args in product(*variants):
                node = Shape(self._opc, args)
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
    def find_coverages(results, value=+1):
        n = results.shape[1]
        cnt = np.count_nonzero(results == value, axis=1)
        i = np.argmin(cnt)
        cases = []
        for j in range(n):
            if results[i][j] == value:
                reminder = np.compress(results[:, j] != value, results, axis=0)
                if reminder.shape[0] == 0:
                    sub_cases = [[j]]
                else:
                    sub_cases = Shape.find_coverages(reminder, value=value)
                    for s in sub_cases:
                        s.append(j)
                cases.extend(sub_cases)
        for c in cases:
            c.sort()
        final_cases = set(tuple(c) for c in cases)
        return final_cases


def from_polish_notation(polish):
    """Creates Shape instance from reversed Polish notation.

    Parameters
    ----------
    polish : list
        List of surfaces and operations written in reversed Polish Notation.

    Returns
    -------
    shape : Shape
        The geometry represented by Shape instance.
    """
    operands = []
    for op in polish:
        if isinstance(op, Surface):
            operands.append(Shape('S', op))
        elif op == 'C':
            operands.append(operands.pop().complement())
        else:
            arg1 = operands.pop()
            arg2 = operands.pop()
            operands.append(Shape(op, arg1, arg2))
    return operands.pop()


class Body(dict):
    """Represents MCNP's cell.

    Parameters
    ----------
    geometry : list or Shape
        Geometry expression. It is either a list of Surface instances and
        operations (reverse Polish notation is used) or Shape object.
    options : dict
        A set of cell's options.

    Methods
    -------
    intersection(other)
        Returns an intersection of this cell with the other.
    populate(universe)
        Fills this cell by universe.
    simplify(box, split_disjoint, min_volume)
        Simplifies cell description.
    transform(tr)
        Applies transformation tr to this cell.
    union(other)
        Returns an union of this cell with the other.
    """
    def __init__(self, geometry, **options):
        if isinstance(geometry, list):
            geometry = from_polish_notation(geometry)
        self._shape = geometry
        dict.__init__(self, options)

    def __str__(self):
        from .model import MCPrinter
        text = [str(self['name'])]
        if 'MAT' in self.keys():
            text.append(str(self['MAT']))
            text.append(str(self['RHO']))
        else:
            text.append('0')
        text += Shape.str_tokens(self)
        printer = MCPrinter()
        text += printer.print_cell_options(self, 5)
        return MCPrinter.print_card(text)

    def intersection(self, other):
        """Gets an intersection if this cell with the other.

        Other cell is a geometry that bounds this one. The resulting cell
        inherits all options of this one (the caller).

        Parameters
        ----------
        other : Cell
            Other cell.

        Returns
        -------
        cell : Cell
            The result.
        """
        geometry = Shape.intersection(self._shape, other._shape)
        return Body(geometry, **self)

    def union(self, other):
        """Gets an union if this cell with the other.

        The resulting cell inherits all options of this one (the caller).

        Parameters
        ----------
        other : Cell
            Other cell.

        Returns
        -------
        cell : Cell
            The result.
        """
        geometry = Shape.union(self._shape, other._shape)
        return Body(geometry, **self)

    def simplify(self, box=GLOBAL_BOX, split_disjoint=False,
                 min_volume=MIN_BOX_VOLUME, trim_size=1):
        """Simplifies this cell by removing unnecessary surfaces.

        The simplification procedure goes in the following way.
        # TODO: insert brief description!

        Parameters
        ----------
        box : Box
            Box where geometry should be simplified.
        split_disjoint : bool
            Whether to split disjoint geometries into separate geometries.
        min_volume : float
            The smallest value of box's volume when the process of box splitting
            must be stopped.
        trim_size : int
            Max size of set to return. It is used to prevent unlimited growth
            of the variant set.

        Returns
        -------
        simple_cell : Cell
            Simplified version of this cell.
        """
        print('Collect stage...')
        self._shape.collect_statistics(box, min_volume)
        print('finding optimal solution...')
        #variants = self._shape.get_simplest(trim_size)
        #return Body(variants[0], **self)

    def populate(self, universe=None):
        """Fills this cell by filling universe.

        If this cell doesn't contain fill options, the cell itself is returned
        as list of length 1. Otherwise a list of cells from filling universe
        bounded by cell being filled is returned.

        Parameters
        ----------
        universe : Universe
            Universe which cells fill this one. If None, universe from 'FILL'
            option will be used. If no such universe, the cell itself will be
            returned.

        Returns
        -------
        cells : list[Cell]
            Resulting cells.
        """
        if universe is None:
            if 'FILL' in self.keys():
                universe = self['FILL']
            else:
                return [self]
        cells = []
        for c in universe.cells:
            new_cell = c.intersection(self)  # because properties like MAT, etc
                                             # must be as in filling cell.
            if 'U' in self.keys():
                new_cell['U'] = self['U']    # except universe.
            cells.append(new_cell)
        return cells

    def transform(self, tr):
        """Applies transformation to this cell.

        Parameters
        ----------
        tr : Transform
            Transformation to be applied.

        Returns
        -------
        cell : Cell
            The result of this cell transformation.
        """
        geometry = self._shape.transform(tr)
        return Body(geometry, **self)
