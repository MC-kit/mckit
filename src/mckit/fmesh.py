from __future__ import annotations

from typing import cast

import numpy as np
import numpy.typing as npt

# noinspection PyUnresolvedReferences,PyPackageRequirements
from mckit.box import EX, EY, EZ, Box

from . import Body
from .transformation import Transformation
from .utils import mids


class RectMesh:
    """Represents rectangular mesh.

    Parameters
    ----------
    xbins
        Bins of mesh in X direction. The last bin value gives dimension of mesh in this direction.
    ybins
        ... Y
    zbins
        ... Z
    transform
        Transformation for the mesh. Default: None.
    """

    def __init__(
        self,
        xbins: npt.ArrayLike,
        ybins: npt.ArrayLike,
        zbins: npt.ArrayLike,
        transform: Transformation | None = None,
    ) -> None:
        self._xbins = np.asarray(xbins, dtype=np.float64)
        self._ybins = np.asarray(ybins, dtype=np.float64)
        self._zbins = np.asarray(zbins, dtype=np.float64)
        self._ex = EX
        self._ey = EY
        self._ez = EZ
        self._origin = np.array([self._xbins[0], self._ybins[0], self._zbins[0]], dtype=np.float64)
        self._tr = None
        if transform is not None:
            self.transform(transform)

    def bounding_box(self) -> Box:
        """Gets the bounding box of the cell.

        Returns
        -------
        bbox
            Bounding box.
        """
        origin = 0.5 * np.array(
            [
                (self._xbins[0] + self._xbins[-1]),
                (self._ybins[0] + self._ybins[-1]),
                (self._zbins[0] + self._zbins[-1]),
            ],
            dtype=np.float64,
        )
        if self._tr:
            origin = self._tr.apply2point(origin)
        dimx = self._xbins[-1] - self._xbins[0]
        dimy = self._ybins[-1] - self._ybins[0]
        dimz = self._zbins[-1] - self._zbins[0]
        return Box(origin, dimx, dimy, dimz, ex=self._ex, ey=self._ey, ez=self._ez)

    @property
    def shape(self) -> tuple[int, int, int]:
        """Gets the shape of the mesh."""
        return self._xbins.size - 1, self._ybins.size - 1, self._zbins.size - 1

    def transform(self, tr: Transformation):
        """Transforms this mesh."""
        self._origin = tr.apply2point(self._origin)
        self._ex = tr.apply2vector(self._ex)
        self._ey = tr.apply2vector(self._ey)
        self._ez = tr.apply2vector(self._ez)
        if (
            self._tr is not None
        ):  # TODO @dvp: check if transformation is not applied twice: on E and as _tr
            self._tr = tr.apply2transform(self._tr)
        else:
            self._tr = tr

    def get_voxel(self, i: int, j: int, k: int) -> Box:
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
        cx = 0.5 * (self._xbins[i] + self._xbins[i + 1])
        cy = 0.5 * (self._ybins[j] + self._ybins[j + 1])
        cz = 0.5 * (self._zbins[k] + self._zbins[k + 1])
        center = np.array([cx, cy, cz])
        if self._tr:
            center = self._tr.apply2point(center)
        xdim = self._xbins[i + 1] - self._xbins[i]
        ydim = self._ybins[j + 1] - self._ybins[j]
        zdim = self._zbins[k + 1] - self._zbins[k]
        return Box(center, xdim, ydim, zdim, ex=self._ex, ey=self._ey, ez=self._ez)

    def voxel_index(
        self, point: npt.ArrayLike, local: bool = False
    ) -> tuple[int, int, int] | list[tuple[int, int, int]] | None:
        """Gets index of voxel that contains specified point.

        Parameters
        ----------
        point
            Coordinates of the point or multiple points to be checked.
        local
            If point is specified in local coordinate system.

        Returns
        -------
        i, j, k : int
            Indices along each dimension of voxel, where the point is located.
        """
        point = np.asarray(point, dtype=np.float64)
        point = self._tr.reverse().apply2point(point) if self._tr and not local else point
        x_proj = np.dot(point, EX)
        y_proj = np.dot(point, EY)
        z_proj = np.dot(point, EZ)
        i = np.searchsorted(self._xbins, x_proj) - 1
        j = np.searchsorted(self._ybins, y_proj) - 1
        k = np.searchsorted(self._zbins, z_proj) - 1
        if len(point.shape) == 1:
            return self.check_indices(i.item(), j.item(), k.item())
        # indices = []
        # for x, y, z in zip(
        #     cast(npt.NDArray, i), cast(npt.NDArray, j), cast(npt.NDArray, k), strict=False
        # ):
        #     _t = self.check_indices(x, y, z)
        #     indices.append(_t)
        # return indices
        return [
            self.check_indices(x, y, z)
            for x, y, z in zip(
                cast(npt.NDArray, i), cast(npt.NDArray, j), cast(npt.NDArray, k), strict=False
            )
        ]

    def check_indices(self, i: int, j: int, k: int) -> tuple[int, int, int] | None:
        """Check if the voxel with such indices really exists.

        Parameters
        ----------
        i, j, k
            Indices along x, y and z dimensions.

        Returns
        -------
        index_tuple
            A tuple of indices if such voxel exists. None otherwise.
        """
        _i = self._check_x(i)
        if _i is None:
            return None

        _j = self._check_y(j)
        if _j is None:
            return None

        _k = self._check_z(k)
        if _k is None:
            return None

        return _i, _j, _k

    def _check_x(self, i: int) -> int | None:
        if i < 0 or i >= self._xbins.size - 1:
            return None
        return i

    def _check_y(self, j: int) -> int | None:
        if j < 0 or j >= self._ybins.size - 1:
            return None
        return j

    def _check_z(self, k: int) -> int | None:
        if k < 0 or k >= self._zbins.size - 1:
            return None
        return k

    def slice_axis_index(
        self, X: float | None = None, Y: float | None = None, Z: float | None = None
    ) -> tuple[int, int, npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """Gets index and axis of slice.

        Parameters
        ----------
        X, Y, Z
            Point of slice in local coordinate system.

        Returns
        -------
        axis
            Number of axis.
        index
            ... along axis.
        x, y
            Centers of bins along free axes.
        """
        none = 0
        axis = 0
        for i, a in enumerate([X, Y, Z]):
            if a is not None:
                none += 1
                axis = i
        if none != 1:
            raise ValueError("Wrong number of fixed spatial variables.")

        if X is not None:
            index = self._check_x(np.searchsorted(self._xbins, X).item() - 1)
        elif Y is not None:
            index = self._check_y(np.searchsorted(self._ybins, Y).item() - 1)
        elif Z is not None:
            index = self._check_z(np.searchsorted(self._zbins, Z).item() - 1)
        else:
            index = None

        if index is None:
            raise ValueError("Specified point lies outside of the mesh.")

        x = mids(self._xbins) if axis > 0 else mids(self._ybins)
        y = mids(self._zbins) if axis < 2 else mids(self._ybins)

        return axis, index, x, y


class CylMesh:
    """Represents cylindrical mesh.

    Parameters
    ----------
    origin
        Bottom center of the cylinder, that bounds the mesh.
    axis
        Cylinder's axis.
    vec
        Vector defining along with axis the plane for theta=0.
    rbins, zbins, tbins
        Bins of mesh in radial, extend and angle directions respectively.
        Angles are specified in revolutions.
    """

    def __init__(
        self,
        origin: npt.ArrayLike,
        axis: npt.ArrayLike,
        vec: npt.ArrayLike,
        rbins: npt.ArrayLike,
        zbins: npt.ArrayLike,
        tbins: npt.ArrayLike,
    ):
        self._origin = np.asarray(origin, dtype=np.float64)
        self._axis = np.asarray(axis, dtype=np.float64)
        self._vec = np.asarray(vec, dtype=np.float64)
        self._rbins = np.asarray(rbins, dtype=np.float64)
        self._zbins = np.asarray(zbins, dtype=np.float64)
        self._tbins = np.asarray(tbins, dtype=np.float64)
        # self._voxels = {}

    @property
    def shape(self) -> tuple[int, int, int]:
        """Gets the shape of the mesh."""
        return self._rbins.size - 1, self._zbins.size - 1, self._tbins.size - 1

    def transform(self, tr: Transformation) -> None:
        """Transforms this mesh."""
        raise NotImplementedError

    def calculate_volumes(
        self,
        cells: list[Body],
        with_mat_only: bool = True,
        verbose: bool = False,
        min_volume: float = 1.0e-3,
    ):
        """Calculates volumes of cells.

        Parameters
        ----------
        cells
            List of cells.
        verbose
            ... output during calculations.
        min_volume
            Minimum volume for cell volume calculations

        Returns
        -------
        volumes
            ... of cells for every voxel. It is dictionary cell -> vol_matrix.
            vol_matrix is SparseData instance - volume of cell for each voxel.
        """
        raise NotImplementedError

    def get_voxel(self, i: int, j: int, k: int) -> Box:
        """Gets voxel.

        Parameters
        ----------
        i, j, k
            Indices of the voxel.

        Returns
        -------
        voxel : Box
            The box that describes the voxel.
        """
        raise NotImplementedError

    def voxel_index(self, point: npt.ArrayLike, local: bool = False) -> tuple[int, int, int] | None:
        """Gets index of voxel that contains specified point.

        Parameters
        ----------
        point
            Coordinates of the point to be checked.
        local
            If point is specified in local coordinate system.

        Returns
        -------
        i, j, k : int
            Indices along each dimension of voxel, where the point is located.
        """
        raise NotImplementedError

    def check_indices(self, i: int, j: int, k: int) -> tuple[int, int, int] | None:
        """Check if the voxel with such indices really exists.

        Parameters
        ----------
        i, j, k
            Indices along x, y and z dimensions.

        Returns
        -------
        index_tuple
            A tuple of indices if such voxel exists. None otherwise.
        """
        _i = self._check_r(i)
        _j = self._check_z(j)
        _k = self._check_t(k)
        if _i is None or _j is None or _k is None:
            return None
        return _i, _j, _k

    def _check_r(self, i: int) -> int | None:
        if i < 0 or i >= self._rbins.size - 1:
            return None
        return i

    def _check_z(self, j: int) -> int | None:
        if j < 0 or j >= self._zbins.size - 1:
            return None
        return j

    def _check_t(self, k: int) -> int | None:
        if k < 0 or k >= self._tbins.size - 1:
            return None
        return k

    def slice_axis_index(
        self, R: float | None = None, Z: float | None = None, T: float | None = None
    ) -> tuple[int, int, npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """Gets index and axis of slice.

        Parameters
        ----------
        R, Z, T
            Point of slice in local coordinate system.

        Returns
        -------
        axis
            Number of axis.
        index
            Index along axis.
        x, y
            Centers of bins along free axes.
        """
        raise NotImplementedError


class FMesh:
    """Fmesh tally object.

    Parameters
    ----------
    name
        Tally name.
    particle
        Particle type (neutron, photon, electron).
    ebins
        Bin boundaries for energies.
    xbins, ybins, zbins
        Bin boundaries in X, Y and Z directions respectively for rectangular mesh.
    rbins, zbins, tbins
        Bin boundaries in R, Z and Theta directions for cylindrical mesh.
    origin
        Bottom center of the cylinder (For cylindrical mesh only).
    axis
        Axis of the cylinder (for cylindrical mesh only).
    vec
        Vector defining along with axis the plane for theta=0.
    data
        Fmesh data - quantity estimation averaged over voxel volume. It has
        shape (Ne-1)x(Nx-1)x(Ny-1)x(Nz-1), where Ne, Nx, Ny and Nx - the number
        of corresponding bin boundaries.
    error
        Fmesh relative error. Shape - see data.
    transform
        Transformation to be applied to the spatial mesh.
    histories
        The number of histories run to obtain meshtal data.
    modifier
        Data transformation.

    Methods
    -------
    get_slice()
        Gets specific slice of data.
    get_spectrum(point)
        Gets energy spectrum at the specified point.
    get_spectrum_by_index(index)
        Gets energy spectrum at the specified mesh index.
    mean_flux()
        Gets average flux for every energy bin.
    """

    def __init__(
        self,
        name: int,
        particle: str,
        data: npt.ArrayLike,
        error: npt.ArrayLike,
        ebins: npt.ArrayLike | None = None,
        xbins: npt.ArrayLike | None = None,
        ybins: npt.ArrayLike | None = None,
        zbins: npt.ArrayLike | None = None,
        rbins: npt.ArrayLike | None = None,
        tbins: npt.ArrayLike | None = None,
        dtbins: npt.ArrayLike | None = None,
        transform: Transformation | None = None,
        modifier: str | None = None,
        origin: npt.ArrayLike | None = None,
        axis: npt.ArrayLike | None = None,
        vec: npt.ArrayLike | None = None,
        histories: int | None = None,
    ):
        self._data = np.asarray(data, dtype=np.float64)
        self._error = np.asarray(error, dtype=np.float64)
        self._name = name
        self._histories = histories
        self._particle = particle
        if ebins is not None:
            self._ebins = np.asarray(ebins, dtype=np.float64)
        else:
            self._ebins = np.array([0, 1.0e36], dtype=np.float64)
        if dtbins is not None:
            self._dtbins = np.asarray(dtbins, dtype=np.float64)
        self._modifier = modifier
        if rbins is None and tbins is None:
            if xbins is None or ybins is None or zbins is None:
                msg = "Bins are not specified."
                raise ValueError(msg)
            self._mesh = RectMesh(xbins, ybins, zbins, transform=transform)
        elif xbins is None and ybins is None:
            if origin is None:
                msg = "Origin not specified."
                raise ValueError(msg)
            if axis is None:
                msg = "Axis not specified."
                raise ValueError(msg)
            if rbins is None:
                msg = "rbins not specified."
                raise ValueError(msg)
            if zbins is None:
                msg = "zbins not specified."
                raise ValueError(msg)
            if tbins is None:
                msg = "tbins not specified."
                raise ValueError(msg)
            if vec is None:
                #TODO @dvp: vec is not provided by MCNP5 (check for MCNP6 difference)
                vec = np.array([1.0, 0.0, 0.0], dtype=np.float64)
            self._mesh = CylMesh(origin, axis, vec, rbins, zbins, tbins)
        if self._data.shape[1:] != self._mesh.shape:
            raise ValueError("Incorrect data shape")
        if self._error.shape[1:] != self._mesh.shape:
            raise ValueError("Incorrect error shape")

    @property
    def mesh(self) -> RectMesh | CylMesh:
        return self._mesh

    @property
    def particle(self) -> str:
        return self._particle

    @property
    def histories(self) -> int | None:
        """The number of histories in the run."""
        return self._histories

    def mean_flux(self) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """Gets average flux over spatial bins.

        Returns
        -------
        ebins
            Energy bin boundaries.
        flux
            Average flux in each energy bin.
        """
        return self._ebins.copy(), np.mean(self._data, axis=(1, 2, 3))

    def get_spectrum(self, point):
        """Gets energy spectrum at the specified point.

        Parameters
        ----------
        point
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
            raise ValueError(f"Point {point} lies outside of the mesh.")
        return self.get_spectrum_by_index(index)

    def get_spectrum_by_index(self, index):
        """Gets energy spectrum in the specified voxel.

        Parameters
        ----------
        index : tuple[int]
            Indices of spatial mesh bins.

        Returns
        -------
        energies: ndarray[float]
            Energy bins for the spectrum at the point - group boundaries.
        flux : ndarray[float]
            Group flux at the point.
        err : ndarray[float]
            Relative errors for flux components.
        """
        i, j, k = index
        flux = self._data[:, i, j, k]
        err = self._error[:, i, j, k]
        return self._ebins, flux, err

    def get_slice(self, E="total", X=None, Y=None, Z=None, R=None, T=None):
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

        data = self._data.take(index, axis=axis + 1)  # +1 because the first axis is for energy.
        err = self._error.take(index, axis=axis + 1)

        if E == "total":
            abs_err = (data * err) ** 2
            abs_tot_err = np.sqrt(np.sum(abs_err, axis=0))
            data = np.sum(data, axis=0)
            err = np.nan_to_num(abs_tot_err / data)
        else:
            if self._ebins[0] >= E or self._ebins[-1] < E:
                raise ValueError("Specified energy lies outside of energy bins.")
            i = np.searchsorted(self._ebins, E) - 1
            data = data.take(i, axis=0)
            err = err.take(i, axis=0)
        return x, y, data, err
