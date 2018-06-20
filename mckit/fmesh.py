# -*- coding: utf-8 -*-

from itertools import product
from abc import ABC, abstractmethod

import numpy as np

from .constants import GLOBAL_BOX, EX, EY, EZ
from .transformation import Transformation
from .meshtal_parser import meshtal_parser, meshtal_lexer

from .geometry import Box


_BIN_NAMES = {'ENERGY': 'ebins', 'X': 'xbins', 'Y': 'ybins', 'Z': 'zbins', 'R': 'rbins', 'THETA': 'tbins'}


def read_meshtal(filename):
    """Reads MCNP meshtal file.

    Parameters
    ----------
    filename : str
        File that contains MCNP meshtally data.

    Returns
    -------
    tallies : dict
        Dictionary of mesh tallies contained in the file. It is
        tally_name -> Fmesh pairs.
    """
    with open(filename) as f:
        text = f.read()
    meshtal_lexer.begin('INITIAL')
    meshtal_data = meshtal_parser.parse(text, lexer=meshtal_lexer)
    histories = meshtal_data['histories']
    tallies = {}
    for t in meshtal_data['tallies']:
        name = t['name']
        particle = t['particle']
        data = t['result']
        error = t['error']
        kwdata = {}
        for k, v in tallies['bins'].items():
            kwdata[_BIN_NAMES[k]] = v
        tallies[name] = FMesh(name, particle, data, error, histories=histories, **kwdata)
    return tallies


class AbstractMesh:
    pass


class RectMesh:
    """Represents rectangular mesh.

    Parameters
    ----------
    xbins, ybins, zbins : array_like[float]
        Bins of mesh in every direction. The last bin value gives dimension of
        mesh in this direction.
    transform : Trnasformation
        Transformation for the mesh. Default: None.

    Methods
    -------
    shape() - gets the shape of mesh.
    get_voxel(i, j, k) - gets the voxel of RectMesh with indices i, j, k.
    """
    def __init__(self, xbins, ybins, zbins, transform=None):
        self._xbins = np.array(xbins)
        self._ybins = np.array(ybins)
        self._zbins = np.array(zbins)
        self._ex = EX
        self._ey = EY
        self._ez = EZ
        self._origin = np.array([self._xbins[0], self._ybins[0], self._zbins[0]])
        if transform is not None:
            self._ex = transform.apply2vector(self._ex)
            self._ey = transform.apply2vector(self._ey)
            self._ez = transform.apply2vector(self._ez)
            self._origin = transform.apply2point(self._origin)
            self._tr = transform
        else:
            self._tr = None

    def __eq__(self, other):
        return self is other

    @property
    def shape(self):
        """Gets the shape of the mesh."""
        return self._xbins.size - 1, self._ybins.size - 1, self._zbins.size - 1

    def calculate_volumes(self, cells, verbose=False, min_volume=1.e-3):
        """Calculates volumes of cells.

        Parameters
        ----------
        cells : list[Body]
            List of cells.
        verbose : bool
            Verbose output during calculations.
        min_volume : float
            Minimum volume for cell volume calculations

        Returns
        -------
        volumes : dict
            Volumes of cells for every voxel. It is dictionary cell -> vol_matrix.
            vol_matrix is SparseData instance - volume of cell for each voxel.
        """
        volumes = {}
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                for k in range(self.shape[2]):
                    box = self.get_voxel(i, j, k)
                    for c in cells:
                        vol = c.volume(box=box, min_volume=min_volume)
                        if vol > 0:
                            if c not in volumes.keys():
                                volumes[c] = SparseData(self)
                            volumes[c][i, j, k] = vol
                    if verbose and volumes[i, j, k]:
                        print('Voxel ({0}, {1}, {2})'.format(i, j, k))
        return volumes

    def get_voxel(self, i, j, k):
        """Gets voxel.

        Parameters
        ----------
        i, j, k : int
            Indices of the voxel.

        Returns
        -------
        voxel : Box
            The box that describes the voxel.
        """
        cx = 0.5 * (self._xbins[i] + self._xbins[i+1])
        cy = 0.5 * (self._ybins[j] + self._ybins[j+1])
        cz = 0.5 * (self._zbins[k] + self._zbins[k+1])
        center = np.array([cx, cy, cz])
        if self._tr:
            center = self._tr.apply2point(center)
        xdim = self._xbins[i+1] - self._xbins[i]
        ydim = self._ybins[j+1] - self._ybins[j]
        zdim = self._zbins[k+1] - self._zbins[k]
        return Box(center, xdim, ydim, zdim, ex=self._ex, ey=self._ey, ez=self._ez)

    def voxel_index(self, point, local=False):
        """Gets index of voxel that contains specified point.

        Parameters
        ----------
        point : array_like[float]
            Coordinates of the point to be checked.
        local : bool
            If point is specified in local coordinate system.

        Returns
        -------
        i, j, k : int
            Indices along each dimension of voxel, where the point is located.
        """
        if self._tr and not local:
            point = self._tr.reverse().apply2point(point)
        else:
            point = np.array(point)
        x_proj = np.dot(EX, point)
        y_proj = np.dot(EY, point)
        z_proj = np.dot(EZ, point)
        i = np.searchsorted(self._xbins, x_proj) - 1
        j = np.searchsorted(self._ybins, y_proj) - 1
        k = np.searchsorted(self._zbins, z_proj) - 1
        if isinstance(i, int):
            return self.check_indices(i, j, k)
        else:
            indices = []
            for x, y, z in zip(i, j, k):
                indices.append(self.check_indices(x, y, z))
            return indices

    def check_indices(self, i, j, k):
        """Check if the voxel with such indices really exists.

        Parameters
        ----------
        i, j, k : int
            Indices along x, y and z dimensions.

        Returns
        -------
        index_tuple : tuple(int)
            A tuple of indices if such voxel exists. None otherwise.
        """
        i = self._check_x(i)
        j = self._check_y(j)
        k = self._check_z(k)
        if i is None or j is None or k is None:
            return None
        else:
            return i, j, k

    def _check_x(self, i):
        if i < 0 or i >= self._xbins.size - 1:
            return None
        return i

    def _check_y(self, j):
        if j < 0 or j >= self._ybins.size - 1:
            return None
        return j

    def _check_z(self, k):
        if k < 0 or k >= self._zbins.size - 1:
            return None
        return k

    def slice_axis_index(self, X=None, Y=None, Z=None):
        """Gets index and axis of slice.

        Parameters
        ----------
        X, Y, Z : float
            Point of slice in local coordinate system.

        Returns
        -------
        axis : int
            Number of axis.
        index : int
            Index along axis.
        x, y : ndarray[float]
            Centers of bins along free axes.
        """
        none = 0
        for i, a in enumerate([X, Y, Z]):
            if a is not None:
                none += 1
                axis = i
        if none != 1:
            raise ValueError('Wrong number of fixed spatial variables.')

        if X is not None:
            index = np.searchsorted(self._xbins, X) - 1
        elif Y is not None:
            index = np.searchsorted(self._ybins, Y) - 1
        elif Z is not None:
            index = np.searchsorted(self._zbins, Z) - 1
        else:
            index = None

        if index is None:
            raise ValueError('Specified point lies outside of the mesh.')

        if axis > 0:
            x = 0.5 * (self._xbins[1:] + self._xbins[:-1])
        else:
            x = 0.5 * (self._ybins[1:] + self._ybins[:-1])
        if axis < 2:
            y = 0.5 * (self._zbins[1:] + self._zbins[:-1])
        else:
            y = 0.5 * (self._ybins[1:] + self._ybins[:-1])

        return axis, index, x, y


class CylMesh:
    """Represents cylindrical mesh.

    Parameters
    ----------
    origin : array_like[float]
        Bottom center of the cylinder, that bounds the mesh.
    axis : array_like[float]
        Cylinder's axis.
    vec : array_like[float]
        Vector defining along with axis the plane for theta=0.
    rbins, zbins, tbins: array_like[float]
        Bins of mesh in radial, extend and angle directions respectively.
        Angles are specified in revolutions.
    """
    def __init__(self, origin, axis, vec, rbins, zbins, tbins):
        self._origin = np.array(origin)
        self._axis = np.array(axis)
        self._vec = np.array(vec)
        self._voxels = {}
        raise NotImplementedError


class SparseData:
    """Describes sparse spatial data.

    Parameters
    ----------
    mesh : RectMesh
        Reference spatial mesh.

    Properties
    ----------
    shape : tuple[int]
        Mesh shape.
    mesh : RectMesh
        Mesh object
    size : int
        The quantity of nonzero elements.

    Methods
    -------
    copy()
        Makes a copy of the data.
    """
    def __init__(self, mesh):
        self._mesh = mesh
        self._data = {}

    def __setitem__(self, index, value):
        """Adds new data element by its index."""
        index = self._mesh.check_indices(*index)
        if index is None:
            raise IndexError('Index value is out of range')
        if value == 0:
            self._data.pop(index, None)
        else:
            self._data[index] = value

    def __getitem__(self, index):
        """Gets data value with specified indices."""
        return self._data.get(index, 0)

    def __iter__(self):
        return iter(self._data.items())

    def copy(self):
        result = SparseData(self.mesh)
        result._data = self._data.copy()
        return result

    @property
    def shape(self):
        return self._mesh.shape

    @property
    def mesh(self):
        return self._mesh

    @property
    def size(self):
        return len(self._data.keys())

    def __add__(self, other):
        result = self.copy()
        result += other
        return result

    def __mul__(self, other):
        result = self.copy()
        result *= other
        return result

    def __truediv__(self, other):
        result = self.copy()
        result /= other
        return result

    def __sub__(self, other):
        result = self.copy()
        result -= other
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__sub__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return self.__truediv__(other)

    def __iadd__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for index, value in self:
                self[index] += other
        elif not isinstance(other, SparseData):
            raise TypeError('Unsupported operand type')
        elif self.mesh != other.mesh:
            raise ValueError('These data belong to different meshes.')
        else:
            for index, value in other:
                self[index] += value
        return self

    def __imul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for index, value in self:
                self[index] *= other
        elif not isinstance(other, SparseData):
            raise TypeError('Unsupported operand type')
        elif self.mesh != other.mesh:
            raise ValueError('These data belong to different meshes.')
        else:
            for index, value in other:
                self[index] *= value
        return self

    def __isub__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for index, value in self:
                self[index] -= other
        elif not isinstance(other, SparseData):
            raise TypeError('Unsupported operand type')
        elif self.mesh != other.mesh:
            raise ValueError('These data belong to different meshes.')
        else:
            for index, value in other:
                self[index] -= value
        return self

    def __itruediv__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for index, value in self:
                self[index] = value / other
        elif not isinstance(other, SparseData):
            raise TypeError('Unsupported operand type')
        elif self.mesh != other.mesh:
            raise ValueError('These data belong to different meshes.')
        else:
            for index, value in other:
                self[index] /= value
        return self


class ElementData:
    """Represents a snapshot of activation results for a specific time.

    Parameters
    ----------
    mesh : RectMesh
        Reference spatial mesh.
    time : float
        Time moment in seconds.
    duration : float
        Duration of the time frame.
    units : str
        Describes units for data supplied.

    Methods
    -------
    add(cell, isotope, index, value)
        Adds new data item to the storage.
    """
    def __init__(self, mesh, time, duration, units='Bq'):
        self._mesh = mesh
        self._time = time
        self._duration = duration
        self._units = units
        self._data = {}

    def add(self, cell, isotope, index, value):
        """Adds new value to the storage.

        Parameters
        ----------
        cell : Body
            Cell, for which the value is given.
        isotope : Element
            Isotope, for which the value is given.
        index : tuple[int]
            Three indices, which specifies voxel location.
        value : float
            Data value.
        """
        if cell not in self._data.keys():
            self._data[cell] = {}
        data_cell = self._data[cell]
        if isotope not in data_cell.keys():
            data_cell[isotope] = SparseData(self._mesh)
        data_cell[isotope][index] = value


class SpectrumData:
    """Represents a snapshot of activation gamma spectrum for a specific time.

    Parameters
    ----------
    mesh : RectMesh
        Reference spatial mesh.
    ebins : array_like[float]
        Energy bin boundaries.
    time : float
        Time moment in seconds.
    duration : float
        Duration of the time frame.
    volumes : dict
        Dictionary of volumes.
    """
    def __init__(self, mesh, ebins, time, duration, volumes):
        self._mesh = mesh
        self._ebins = np.array(ebins)
        self._time = time
        self._duration = duration
        self._volumes = volumes
        self._data = {}

    def add(self, cell, index, flux):
        """Adds new spectrum to the storage.

        Parameters
        ----------
        cell : Body
            Cell, for which the value is given.
        index : tuple[int]
            Three indices, which specifies voxel location.
        flux : array_like[float]
            Flux data.
        """
        if len(flux) != self._ebins.size - 1:
            raise ValueError("Wrong length of flux vector.")
        if cell not in self._data.keys():
            self._data[cell] = SparseData(self._mesh)
        self._data[cell][index] = np.array(flux)


class FMesh:
    """Fmesh tally object.
    
    Parameters
    ----------
    name : int
        Tally name.
    particle : str
        Particle type (neutron, photon, electron).
    ebins : array_like[float]
        Bin boundaries for energies.
    xbins, ybins, zbins : array_like[float]
        Bin boundaries in X, Y and Z directions respectively for rectangular mesh.
    rbins, zbins, tbins : array_like[float]
        Bin boundaries in R, Z and Theta directions for cylindrical mesh.
    origin : array_like[float]
        Bottom center of the cylinder (For cylindrical mesh only).
    axis : array_like[float]
        Axis of the cylinder (for cylindrical mesh only).
    vec : array_like[float]
        Vector defining along with axis the plane for theta=0.
    data : arraylike[float]
        Fmesh data - quantity estimation averaged over voxel volume. It has
        shape (Ne-1)x(Nx-1)x(Ny-1)x(Nz-1), where Ne, Nx, Ny and Nx - the number
        of corresponding bin boundaries.
    error : arraylike[float]
        Fmesh relative error. Shape - see data.
    transform : Transformation
        Transformation to be applied to the spatial mesh.
    histories : int
        The number of histories run to obtain meshtal data.
    modifier : None
        Data transformation.
        
    Methods
    -------
    get_slice() - gets specific slice of data.
    get_spectrum(point) - gets energy spectrum at the specified point.
    calculate_volumes(cells, min_volume, verbose) - calculates volumes of cells for every voxel.
    """
    def __init__(self, name, particle, data, error, ebins=None, xbins=None, ybins=None, zbins=None, rbins=None,
                 tbins=None, transform=None, modifier=None, origin=None, axis=None, vec=None, histories=None):
        self._data = np.array(data)
        self._error = np.array(error)
        self._name = name
        self._histories = histories
        self._particle = particle
        if ebins is not None:
            self._ebins = np.array(ebins)
        else:
            self._ebins = np.array([0, 1.e+36])
        self._modifier = modifier
        if rbins is None and tbins is None:
            self._mesh = RectMesh(xbins, ybins, zbins, transform=transform)
        elif xbins is None and ybins is None:
            self._mesh = CylMesh(origin, axis, vec, rbins, zbins, tbins)
        if self._data.shape != self._mesh.shape:
            raise ValueError("Incorrect data shape")
        elif self._error.shape != self._mesh.shape:
            raise ValueError("Incorrect error shape")

    @property
    def mesh(self):
        return self._mesh

    @property
    def histories(self):
        """The number of histories in the run."""
        return self._histories

    def get_spectrum(self, point):
        """Gets energy spectrum at the specified point.
        
        Parameters
        ----------
        point : arraylike[float]
            Point energy spectrum must be get at.
            
        Returns
        -------
        energies: ndarray[float]
            Energy bins for the spectrum at the point - group boundaries.
        flux : ndarray[float]
            Group flux at the point.
        err : ndarray[float]
            Relative errors for flux components.
        """
        index = self._mesh.voxel_index(point)
        if index is None:
            raise ValueError("Point {0} lies outside of the mesh.".format(point))
        i, j, k = index
        flux = self._data[:, i, j, k]
        err = self._error[:, i, j, k]
        return self._ebins, flux, err

    def get_slice(self, E='total', X=None, Y=None, Z=None, R=None, T=None):
        """Gets data in the specified slice. Only one spatial letter is allowed.

        Parameters
        ----------
        E : str or float
            Energy value of interest. It specifies energy bin. If 'total' - then data
            is summed across energy axis.
        X, Y, Z : float
            Spatial point which belongs to the slice plane. Other two dimensions are free.

        Returns
        -------
        x, y : ndarray[float]
            Centers of spatial bins in free directions.
        data : ndarray[float]
            Data
        err : ndarray[float]
            Relative errors for data.
        """
        if isinstance(self._mesh, RectMesh):
            axis, index, x, y = self._mesh.slice_axis_index(X=X, Y=Y, Z=Z)
        else:
            axis, index, x, y = self._mesh.slice_axis_index(R=R, Z=Z, T=T)

        data = self._data.take(index, axis=axis + 1)   # +1 because the first axis is for energy.
        err = self._error.take(index, axis=axis + 1)

        if E == 'total':
            abs_err = (data * err) ** 2
            abs_tot_err = np.sqrt(np.sum(abs_err, axis=0))
            data = np.sum(data, axis=0)
            err = np.nan_to_num(abs_tot_err / data)
        else:
            if E <= self._ebins[0] or E > self._ebins[-1]:
                raise ValueError("Specified energy lies outside of energy bins.")
            i = np.searchsorted(self._ebins, E)
            data = data.take(i, axis=0)
            err = err.take(i, axis=0)
        return x, y, data, err

