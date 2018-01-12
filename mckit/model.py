# -*- coding: utf-8 -*-

from collections import deque
from functools import reduce
from copy import deepcopy

import numpy as np

from .parser import lexer, parser
from .surface import create_surface, Surface
from .cell import Cell
from .universe import Universe
from .transformation import Transformation
from .material import Material
from .constants import RELATIVE_DENSITY_TOLERANCE


def read_mcnp(filename):
    """Reads MCNP model from file and creates corresponding objects.

    Parameters
    ----------
    filename : str
        File that contains MCNP model.

    Returns
    -------
    model : Model
        Calculation model.
    """
    with open(filename) as f:
        text = f.read()
    lexer.begin('INITIAL')
    title, cells, surfaces, data = parser.parse(text)
    return Model(title, cells, surfaces, data)


class Model:
    """Represents calculation model.
    
    Parameters
    ----------
    title : str
        Title that briefly describes the model.
    cells : dict
        A dictionary of cell data. It is pairs cell_name -> cell_params. 
        Cell_params is also a dictionary of raw cell parameters. It contains
        indices (references) of other model objects like transformations, 
        surfaces, materials, etc.
    surfaces : dict
        A dictionary of raw surface data. It is pairs surf_name -> surf_params.
    data : dict
        Dictionary of raw data, that describes datacards.
    base_universe : int
        A name of base universe for model. Cells of this universe will have
        parameter U=0. The model will contain only cells that belong to
        inner universes of this one.
    take_inserted : bool
        Whether to take cells inserted by fill operations. If False, no filling
        universes are taken, fill options are moved in comments. Default True.
        
    Methods
    -------
    extract_submodel(uname, title, take_inserted)
        Gets the Model instance that corresponds to the specified universe.
    list_universes()
        Gets the list of universe names.
    universe()
        Gets the model in object representation (as Universe instance).
    save(filename)
        Saves model.
    """
    def __init__(self, title, cells, surfaces, data, base_universe=0,
                 take_inserted=True):
        self.title = deepcopy(title)
        self.cells = _get_contained_cells(cells, base_universe, take_inserted)
        surf_ind = _get_surface_indices(self.cells)
        self.surfaces = {si: deepcopy(surfaces[si]) for si in surf_ind}
        self.data = deepcopy(data)
        self.data.pop('M', None)
        self.data.pop('TR', None)
        mat_ind = _get_composition_indices(self.cells)
        tr_ind = _get_transformation_indices(self.cells, self.surfaces)
        if mat_ind:
            self.data['M'] = {mi: deepcopy(data['M'][mi]) for mi in mat_ind}
        if tr_ind:
            self.data['TR'] = {ti: deepcopy(data['TR'][ti]) for ti in tr_ind}

    def save(self, filename):
        """Saves the model into file.
        
        Parameters
        ----------
        filename : str
            Name of file.
        """
        printer = MCPrinter()
        printer.print(self, filename)

    def list_universes(self):
        """Gets the list of universe names.

        Returns
        -------
        unames : list[int]
            List of included universe names.
        """
        unames = set()
        for cell_data in self.cells.values():
            if 'U' in cell_data.keys():
                unames.add(cell_data['U'])
        return sorted(list(unames))

    def extract_submodel(self, uname, title=None, take_inserted=True):
        """Gets the Model instance that corresponds to the specified universe.

        Parameters
        ----------
        uname : int
            The name of universe under consideration.
        title : str
            A brief description of the universe.
        take_inserted : bool
            Whether to take cells inserted by fill operations. If False, no 
            filling universes are taken, fill options are moved in comments. 
            Default True.
            
        Returns
        -------
        model : Model
            Model, that corresponds to the specified universe.
        """
        if title is None:
            title = "Universe {0}".format(uname)
        return Model(title, self.cells, self.surfaces, self.data, uname,
                     take_inserted=take_inserted)

    def universe(self, title=""):
        """Gets the model in object representation.
        
        Returns
        -------
        universe : Universe
            The model represented as universe object.
        title : str, optional
            A brief description.
        """
        self._transformations = {}
        self._surfaces = {}
        self._materials = {}
        self._universes = {}
        return self._get_universe_object(0, title)

    def _get_universe_object(self, uname, title=""):
        """Creates new universe from data of this model.

        Parameters
        ----------
        uname : int
            A name of universe to be created.
        title : str, optional
            A brief description.

        Returns
        -------
        universe : Universe
        """
        if uname not in self._universes.keys():
            cells = []
            for name, cell in self.cells.items():
                if cell.get('U', 0) == uname:
                    cells.append(self._produce_cell(name))
            self._universes[uname] = Universe(cells, name=uname, title=title)
        return self._universes[uname]

    def _produce_cell(self, cell_name):
        """Creates Cell instance."""
        geometry = self._produce_cell_geometry(cell_name)
        # TODO: Handle like but cell options properly.
        options = self.cells[cell_name].copy()
        options.pop('geometry', None)
        options.pop('reference', None)
        fill = options.pop('FILL', None)
        if fill:
            universe = self._get_universe_object(fill.pop('universe'))
            tr = self._get_transform_object(fill.pop('transform', None))
            if tr:
                universe = universe.transform(tr)
            options['FILL'] = universe

        tr = options.pop('TRCL', None)
        if tr:
            for i, s in enumerate(geometry):
                if isinstance(s, Surface):
                    geometry[i] = s.transform(tr)
            if 'FILL' in options.keys():
                options['FILL'] = universe.transform(tr)
        return Cell(geometry, **options)

    def _produce_cell_geometry(self, cell_name):
        """Creates a list that describes cell geometry.
        
        This function can use reference geometry. It replaces cell complement
        operations, replaces surface numbers by surface objects.
        
        Parameters
        ----------
        cell_name : int
            A name of the cell under consideration.
            
        Returns
        -------
        geometry : list
            List that describes cell geometry in object representation.
        """
        geometry = self._get_reference_geometry(cell_name).copy()
        i = 0
        while i < len(geometry):
            elem = geometry[i]
            if isinstance(elem, int) and geometry[i+1] == '#':
                geometry[i:i+2] = self._get_reference_geometry(elem) + ['C']
                continue
            elif isinstance(elem, int):
                geometry[i] = self._get_surface_object(elem)
            i += 1
        return geometry

    def _get_reference_geometry(self, cell_no):
        """Gets geometry of the cell with name cell_no."""
        ref_cell = cell_no
        while 'reference' in self.cells[ref_cell].keys():
            ref_cell = self.cells[ref_cell]['reference']
        return self.cells[ref_cell]['geometry']

    def _get_material_object(self, comp_no, density):
        """Gets material object that corresponds to comp_no and density.
        
        Parameters
        ----------
        comp_no : int
            Composition name.
        density : float
            Density of material.
            
        Returns 
        -------
        material : Material
            Material object.
        """
        if comp_no not in self._compositions.keys():
            self._densities[comp_no] = [0]
            self._materials[comp_no] = [None]
        i = np.searchsorted(self._densities[comp_no], density)
        test_indices = []
        if i-1 > 0:
            test_indices.append(i-1)
        if i < len(self._densities):
            test_indices.append(i)
        rels = []
        for ti in test_indices:
            t_den = self._densities[ti]
            rels.append(abs(t_den - density) / abs(t_den + density))
        min_ind = np.argmin(rels)
        if rels[min_ind] >= RELATIVE_DENSITY_TOLERANCE:
            mat_params = {}
            if density > 0:
                mat_params['concentration'] = density
            elif density < 0:
                mat_params['density'] = abs(density)
            if 'atomic' in self.data['M'][comp_no].keys():
                mat_params['atomic'] = self.data['M'][comp_no]['atomic']
            if 'wgt' in self.data['M'][comp_no].keys():
                mat_params['wgt'] = self.data['M'][comp_no]['wgt']
            mat = Material(**mat_params)
            self._densities[comp_no].insert(i, density)
            if density > 0:
                self._densities[comp_no].insert(-i, mat.density())
            else:
                self._densities[comp_no].insert(-i, mat.concentration())
            self._materials[comp_no].insert(i, mat)
            self._materials[comp_no].insert(-i, mat)
            min_ind = i
        return self._materials[min_ind]

    def _get_surface_object(self, surf_no):
        """Gets surface object that corresponds to surf_no."""
        if surf_no not in self._surfaces.keys():
            kind, params, options = self.surfaces[surf_no]
            if 'transform' in options.keys():
                tr_name = options['transform']
                options = options.copy()
                options['transform'] = self._get_transform_object(tr_name)
            self._surfaces[surf_no] = create_surface(kind, *params, **options)
        return self._surfaces[surf_no]

    def _get_transform_object(self, tr):
        """Gets transformation object that corresponds to tr."""
        if isinstance(tr, dict):
            return Transformation(**tr)
        elif isinstance(tr, int):
            if tr not in self._transformations.keys():
                tr_data = self.data['TR'][tr]
                self._transformations[tr] = Transformation(**tr_data)
            return self._transformations[tr]


def _get_contained_cells(cells, uname, take_inserted=True):
    """Gets all cells contained in universe uname, directly or indirectly.

    Parameters
    ----------
    cells : dict
        Dictionary of cells.
    uname : int
        Name of universe to start search from.
    take_inserted : bool
        Whether to take cells inserted by fill operations. If False, no filling
        universes are taken, fill options are moved in comments. Default True.

    Returns
    -------
    new_cells : dict
        Dictionary of contained cells.
    """
    universes = {uname}
    if take_inserted:
        u_dep = _get_universe_dependencies(cells)
        check_queue = deque([uname])
        while check_queue:
            u = check_queue.popleft()
            contained = u_dep[u]
            for c in contained:
                if c not in universes:
                    universes.add(c)
                    check_queue.append(c)

    new_cells = {}
    for cell_name, cell_params in cells.items():
        u = cell_params.get('U', 0)
        if u in universes:
            new_params = deepcopy(cell_params)
            if u == uname:
                new_params.pop('U', 0)
            if not take_inserted and 'FILL' in new_params.keys():
                # TODO: Add transition of FILL param to comment.
                new_params.pop('FILL')
            new_cells[cell_name] = new_params
    return new_cells


def _get_universe_dependencies(cells):
    """Gets a dictionary of universe dependencies.

    Parameters
    ----------
    cells : dict
        Dictionary of cells.

    Returns
    -------
    universes : dict
        Dictionary of universe name -> set of contained universe names.
    """
    universes = {}
    for cell_name, cell_params in cells.items():
        uname = cell_params.get('U', 0)
        if uname not in universes.keys():
            universes[uname] = set()
        if 'FILL' in cell_params.keys():
            universes[uname].add(cell_params['FILL']['universe'])
    return universes


def _get_surface_indices(cells):
    """Gets a set of surface indices included in the geometry.
    
    Parameters
    ----------
    cells : dict
        Dictionary of cells to be considered.
        
    Returns
    -------
    surfs : set
        A set of surface names.
    """
    surfs = set()
    for cell in cells.values():
        geometry = cell.get('geometry', None)
        if not geometry:
            continue
        L = len(geometry) - 1
        for i, c in enumerate(geometry):
            if isinstance(c, int) and (i < L and geometry[i+1] != '#' or i == L):
                surfs.add(c)
    return surfs


def _get_transformation_indices(cells, surfaces):
    """Gets a set of transformation indices included in the cells.
    
    Parameters
    ----------
    cells : dict
        Dictionary of cells under consideration.
    surfaces : dict
        Dictionary of surfaces under consideration.
        
    Returns
    -------
    trans : set
        A set of transformation names.
    """
    trans = set()
    for cell in cells.values():
        trcl = cell.get('TRCL', None)
        if isinstance(trcl, int):
            trans.add(trcl)
        if 'FILL' in cell.keys():
            utr = cell['FILL'].get('transform', None)
            if isinstance(utr, int):
                trans.add(utr)

    for surf in surfaces.values():
        if 'transform' in surf[2].keys():
            trans.add(surf[2]['transform'])

    return trans


def _get_composition_indices(cells):
    """Gets a set of composition indices included in the cells.
    
    Parameters
    ----------
    cells : dict
        Dictionary of cells under consideration.
        
    Returns
    -------
    comps : set
        A set of composition names.
    """
    comps = set()
    for cell in cells.values():
        if 'MAT' in cell.keys():
            comps.add(cell['MAT'])
    return comps


class MCPrinter:
    """MCNP input file printer"""
    def __init__(self, cell_acc=1.e-6, surf_acc=1.e-10, mat_acc=1.e-6,
                 tr_acc=1.e-6):
        self.cell_acc = cell_acc
        self.surf_acc = surf_acc
        self.mat_acc = mat_acc
        self.tr_acc = tr_acc
        self.option_list = ['IMPN', 'IMPP', 'IMPE', 'U', 'TRCL', 'FILL']

    def print(self, model, filename):
        """Prints model to file.
        
        Parameters
        ----------
        model : Model
            Model to be printed.
        filename : str
            File name.
        """
        cards = [model.title, 'C cell section']
        for i, cell_obj in model.cells.items():
            cards.append(self.print_card(self.cell_print(cell_obj, name=i)))

        cards.append('\nC surface section')
        for i, surf_obj in model.surfaces.items():
            cards.append(self.print_card(self.surface_print(surf_obj, name=i)))

        cards.append('\nC data section')
        if 'TR' in model.data.keys():
            cards.append('C transformations')
            for i, tr_obj in model.data['TR'].items():
                cards.append(self.print_card(
                    self.transformation_print(tr_obj, name=i))
                )

        if 'M' in model.data.keys():
            cards.append('C materials')
            for i, mat_obj in model.data['M'].items():
                cards.append(self.print_card(
                    self.material_print(mat_obj, name=i))
                )

        cards.append('\n')
        text = '\n'.join(cards)
        with open(filename, mode='w') as f:
            f.write(text)

    @staticmethod
    def print_card(card, offset=8):
        """Format card words to satisfy MCNP rules.
        
        Parameters
        ----------
        card : list[str]
            List of words.
        offset : int
            The number of spaces to make continuation of line. Minimum 5.
            
        Returns
        -------
        text : str
            Text string that describes the card.
        """
        length = 0
        words = []
        line_sep = '\n' + ' ' * offset
        for w in card:
            if length + len(w) + 1 > 80:
                words.append(line_sep)
                length = offset
            words.append(w)
            length += len(w) + 1
        return ' '.join(words)

    def transformation_print(self, tr_obj, name=None):
        """Gets array of words that describe a tr card.
        
        Parameters
        ----------
        tr_obj : dict
            Dictionary that describes transformation. 
        name : int
            Name of transformation.
                    
        Returns
        -------
        card : list[str]
            List of words that describes transformation.
        """
        card = []
        if name is not None:
            card.append('TR{0:d}'.format(name))
            if tr_obj.get('indegrees', False):
                card[0] = '*' + card[0]
        places = int(np.ceil(np.log10(1 / self.tr_acc))) + 1
        for t in tr_obj.get('translation', [0, 0, 0]):
            card.append(('{0:.' + '{0}'.format(places) + 'g}').format(t))
        for t in tr_obj.get('rotation', []):
            card.append(('{0:.' + '{0}'.format(places) + 'g}').format(t))
        if tr_obj.get('inverted', False):
            card.append('-1')
        return card

    def material_print(self, mat_obj, name=None):
        """Gets array of words that describe material card.
        
        Parameters
        ----------
        mat_obj : dict
            Dictionary that describes material.
        name : int
            Name of material.
                    
        Returns
        -------
        card : list[str]
            List of words that describes material.
        """
        card = ['M{0:d}'.format(name)]
        places = int(np.ceil(np.log10(1 / self.mat_acc))) + 1
        # atomic data
        for pair in mat_obj.get('atomic', []):
            if len(pair) == 2:
                card.append('{0:5d}'.format(pair[0]))
            else:
                card.append('{0:5d}.{1}'.format(pair[0], pair[2]))
            card.append(('{0:.' + '{0}'.format(places) + 'g}').format(pair[1]))
        # weight data
        for pair in mat_obj.get('wgt', []):
            if len(pair) == 2:
                card.append('{0:5d}'.format(pair[0]))
            else:
                card.append('{0:5d}.{1}'.format(pair[0], pair[2]))
            card.append(('{0:.' + '{0}'.format(places) + 'g}').format(-pair[1]))
        # keywords
        for key in set(mat_obj.keys()).difference({'atomic', 'wgt'}):
            card.append('{0}={1}'.format(key, mat_obj[key]))
        return card

    def surface_print(self, surf_obj, name=None):
        """Gets array of words that describe surface card.
        
        Parameters
        ----------
        surf_obj : tuple
            Tuple of surface parameters.
        name : int
            Name of surface.
                    
        Returns
        -------
        card : list[str]
            List of words that describe surface.
        """
        surf_spec, params, options = surf_obj
        card = ['{0}{1:d}'.format(options.get('modifier', ''), name)]
        if 'transform' in options.keys():
            card.append('{0:d}'.format(options['transform']))
        card.append(surf_spec)
        places = int(np.ceil(np.log10(1 / self.surf_acc))) + 1
        for p in params:
            card.append(('{0:.' + '{0}'.format(places) + 'g}').format(p))
        return card

    def cell_print(self, cell_obj, name=None):
        """Gets array of words that describe cell card.
        
        Parameters
        ----------
        cell_obj : dict
            Dictionary of cell parameters.
        name : int
            Name of cell.
                
        Returns
        -------
        card : list[str]
            List of words that describe cell.
        """
        card = ['{0:d}'.format(name)]
        places = int(np.ceil(np.log10(1 / self.cell_acc))) + 1
        if 'geometry' in cell_obj.keys():
            mat = cell_obj.get('MAT', 0)
            card.append('{0:d}'.format(mat))
            if mat:
                den = cell_obj.get('RHO')
                card.append(('{0:.' + '{0}'.format(places) + 'g}').format(den))

        # Geometry description
        if 'geometry' in cell_obj.keys():
            expr = self._get_geometry_description(cell_obj['geometry'].copy())
            card.extend(expr)
        else:
            card.extend(['LIKE', str(cell_obj['reference']), 'BUT'])

        # Cell options
        for key in self.option_list:
            if key not in cell_obj.keys():
                continue
            item = cell_obj[key]
            if key[:3] == 'IMP':
                card.append(key[:3] + ':' + key[3] + '=' +
                            ('{0:.' + '{0}'.format(places) + 'g}').format(item))
            elif key == 'TRCL':
                if isinstance(item, int):
                    card.append('TRCL={0:d}'.format(item))
                else:
                    if 'indegrees' in item.keys():
                        key = '*' + key
                    card.append(key + '=')
                    tr_rep = self.transformation_print(item)
                    card.extend(self._parentheses(tr_rep))
            elif key == 'FILL':
                u = item['universe']
                card.append('FILL={0:d}'.format(u))
                if 'transform' in item.keys():
                    tr = item['transform']
                    if isinstance(tr, int):
                        card[-1] = card[-1] + '({0:d})'.format(tr)
                    else:
                        if 'indegrees' in tr.keys():
                            card[-1] = '*' + card[-1]
                        tr_rep = self.transformation_print(tr)
                        card.extend(self._parentheses(tr_rep))
            else:
                card.append(key + '=' +
                            ('{0:.' + '{0}'.format(places) + 'g}').format(item))
        return card

    @classmethod
    def _get_geometry_description(cls, expr, priority=3):
        """Converts inverse Polish notation into MCNP description.
        
        It modifies expr list, so it's copy should be passed.
        
        Parameters
        ----------
        expr : list
            Geometry expression list.
        priotity : int
            External operation priority. 1 - number, complement; 
            2 - intersection, 3 - union.
        
        Returns
        -------
        geom : list
            List of MCNP geometry tokens.
        """
        operation = expr.pop()
        if operation == 'U':
            op2 = cls._get_geometry_description(expr, 3)
            op1 = cls._get_geometry_description(expr, 3)
            op1.append(':')
            op = op1 + op2
            if priority < 3:
                op = cls._parentheses(op, priority == 1)
        elif operation == 'I':
            op2 = cls._get_geometry_description(expr, 2)
            op1 = cls._get_geometry_description(expr, 2)
            op = op1 + op2
            if priority < 2:
                op = cls._parentheses(op, priority == 1)
        elif operation == 'C':
            op = cls._get_geometry_description(expr, 1)
        elif operation == '#':
            cell = expr.pop()
            op = ['#{0:d}'.format(cell)]
        else:
            sign = -1 if priority == 1 else +1
            op = ['{0:d}'.format(operation * sign)]
        return op

    @classmethod
    def _parentheses(cls, expr, complement=False):
        """Rounds expr with parentheses."""
        left = '#(' if complement else '('
        right = ')'
        expr.insert(0, left)
        expr.append(right)
        return expr