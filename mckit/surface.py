# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from itertools import product, groupby, permutations

import numpy as np

from . import constants
# noinspection PyUnresolvedReferences,PyPackageRequirements
from .geometry import Plane      as _Plane,    \
                      Sphere     as _Sphere,   \
                      Cone       as _Cone,     \
                      Cylinder   as _Cylinder, \
                      Torus      as _Torus,    \
                      GQuadratic as _GQuadratic, \
                      RCC        as _RCC, \
                      ORIGIN, EX, EY, EZ
from mckit.box import GLOBAL_BOX
from .printer import print_card, pretty_float
from .transformation import Transformation
from .utils import *
from .card import Card
from mckit import body


# noinspection PyUnresolvedReferences,PyPackageRequirements
__all__ = [
    'create_surface',
    'Plane',
    'Sphere',
    'Cone',
    'Torus',
    'GQuadratic',
    'Cylinder',
    'Surface',
    'RCC',
    'ORIGIN',
    'EX',
    'EY',
    'EZ',
]


def create_surface(kind, *params, **options):
    """Creates new surface.

    Parameters
    ----------
    kind : str
        Surface kind designator. See MCNP manual.
    params : list[float]
        List of surface parameters.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to the surface being
                             created. Transformation instance.

    Returns
    -------
    surf : Surface
        New surface.
    """
    kind = kind.upper()
    if kind[-1] == 'X':
        axis = EX
    elif kind[-1] == 'Y':
        axis = EY
    elif kind[-1] == 'Z':
        axis = EZ
    # -------- Plane -------------------
    if kind[0] == 'P':
        if len(kind) == 2:
            return Plane(axis, -params[0], **options)
        else:
            return Plane(params[:3], -params[3], **options)
    # -------- SQ -------------------
    elif kind == 'SQ':
        A, B, C, D, E, F, G, x0, y0, z0 = params
        m = np.diag([A, B, C])
        v = 2 * np.array([D - A*x0, E - B*y0, F - C*z0])
        k = A*x0**2 + B*y0**2 + C*z0**2 - 2 * (D*x0 + E*y0 + F*z0) + G
        return GQuadratic(m, v, k, **options)
    # -------- Sphere ------------------
    elif kind[0] == 'S':
        if kind == 'S':
            r0 = np.array(params[:3])
        elif kind == 'SO':
            r0 = ORIGIN
        else:
            r0 = axis * params[0]
        R = params[-1]
        return Sphere(r0, R, **options)
    # -------- Cylinder ----------------
    elif kind[0] == 'C':
        A = 1 - axis
        if kind[1] == '/':
            Ax, Az = np.dot(A, EX), np.dot(A, EZ)
            r0 = params[0] * (Ax * EX + (1 - Ax) * EY) + \
                 params[1] * ((1 - Az) * EY + Az * EZ)
        else:
            r0 = ORIGIN
        R = params[-1]
        return Cylinder(r0, axis, R, **options)
    # -------- Cone ---------------
    elif kind[0] == 'K':
        if kind[1] == '/':
            r0 = np.array(params[:3])
            ta = np.sqrt(params[3])
        else:
            r0 = params[0] * axis
            ta = np.sqrt(params[1])
        sheet = 0 if len(params) % 2 == 0 else int(params[-1])
        return Cone(r0, axis, ta, sheet, **options)
    # ---------- GQ -----------------
    elif kind == 'GQ':
        A, B, C, D, E, F, G, H, J, k = params
        m = np.array([[A, 0.5*D, 0.5*F], [0.5*D, B, 0.5*E], [0.5*F, 0.5*E, C]])
        v = np.array([G, H, J])
        return GQuadratic(m, v, k, **options)
    # ---------- Torus ---------------------
    elif kind[0] == 'T':
        x0, y0, z0, R, a, b = params
        return Torus([x0, y0, z0], axis, R, a, b, **options)
    # ---------- Macrobodies ---------------
    elif kind == 'RPP':
        xmin, xmax, ymin, ymax, zmin, zmax = params
        center = [xmin, ymin, zmin]
        dirx = [xmax - xmin, 0, 0]
        diry = [0, ymax - ymin, 0]
        dirz = [0, 0, zmax - zmin]
        return BOX(center, dirx, diry, dirz, **options)
    elif kind == 'BOX':
        center = params[:3]
        dirx = params[3:6]
        diry = params[6:9]
        dirz = params[9:]
        return BOX(center, dirx, diry, dirz, **options)
    elif kind == 'RCC':
        center = params[:3]
        axis = params[3:6]
        radius = params[6]
        return RCC(center, axis, radius, **options)
    # ---------- Axisymmetric surface defined by points ------
    else:
        if len(params) == 2:
            return Plane(axis, -params[0], **options)
        elif len(params) == 4:
            # TODO: Use special classes instead of GQ
            h1, r1, h2, r2 = params
            if abs(h2 - h1) < constants.RESOLUTION * max(abs(h1), abs(h2)):
                return Plane(axis, -0.5 * (h1 + h2), **options)
            elif abs(r2 - r1) < constants.RESOLUTION * max(abs(r2), abs(r1)):
                R = 0.5 * (abs(r1) + abs(r2))
                return Cylinder([0, 0, 0], axis, R, **options)
            else:
                if r1 * r2 < 0:
                    raise ValueError('Points must belong to the one sheet.')
                h0 = (abs(r1) * h2 - abs(r2) * h1) / (abs(r1) - abs(r2))
                ta = abs((r1 - r2) / (h1 - h2))
                s = round((h1 - h0) / abs(h1 - h0))
                return Cone(axis * h0, axis, ta, sheet=s, **options)
        elif len(params) == 6:
            # TODO: Implement creation of surface by 3 points.
            raise NotImplementedError


def create_replace_dictionary(surfaces, unique=None, box=GLOBAL_BOX, tol=1.e-10):
    """Creates surface replace dictionary for equal surfaces removing.

    Parameters
    ----------
    surfaces : set[Surface]
        A set of surfaces to be checked.
    unique: set[Surface]
        A set of surfaces that are assumed to be unique. If not None, than
        'surfaces' are checked for coincidence with one of them.
    box : Box
        A box, which is used for comparison.
    tol : float
        Tolerance

    Returns
    -------
    replace : dict
        A replace dictionary. surface -> (replace_surface, sense). Sense is +1
        if surfaces have the same direction of normals. -1 otherwise.
    """
    replace = {}
    uniq_surfs = set() if unique is None else unique
    for s in surfaces:
        for us in uniq_surfs:
            t = s.equals(us, box=box, tol=tol)
            if t != 0:
                replace[s] = (us, t)
                break
        else:
            uniq_surfs.add(s)
    return replace


class Surface(Card):
    """Base class for all surface classes.

    Methods
    -------
    equals(other, box, tol)
        Checks if this surface and surf are equal inside the box.
    test_point(p)
        Checks the sense of point p with respect to this surface.
    transform(tr)
        Applies transformation tr to this surface.
    test_box(box)
        Checks whether this surface crosses the box.
    projection(p)
        Gets projection of point p on the surface.
    """
    def __init__(self, **options):
        Card.__init__(self, **options)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

    def __getstate__(self):
        return self.options

    def __setstate__(self, state):
        self.options = state

    @abstractmethod
    def transform(self, tr):
        """Applies transformation to this surface.

        Parameters
        ----------
        tr : Transform
            Transformation to be applied.

        Returns
        -------
        surf : Surface
            The result of this surface transformation.
        """

    def mcnp_words(self):
        words = []
        mod = self.options.get('modifier', None)
        if mod:
            words.append(mod)
        words.append(str(self.name()))
        words.append(' ')
        return words


class Macrobody(Surface, body._Shape):
    

    def __getstate__(self):
        surf_state = Surface.__getstate__(self)
        args = [a.args[0] for a in self.args]
        return args, self._hash, surf_state

    def __setstate__(self, state):
        args, hash_value, surf_state = state
        Surface.__setstate__(self, surf_state)
        new_args = [body._Shape('S', a) for a in args]
        body._Shape.__init__(self, 'U', *new_args)
        self._hash = hash_value

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Macrobody):
            return False
        if len(self.args) != len(other.args):
            return False
        args_this = [a.args[0] for a in self.args]
        for a in args_this:
            print('{0:3} |'.format(hash(a)), a.mcnp_repr())
        args_other = [a.args[0] for a in other.args]
        print(len(args_this), len(args_other))
        self_groups = {k: list(v) for k, v in groupby(sorted(args_this, key=hash), key=hash)}
        other_groups = {k: list(v) for k, v in groupby(sorted(args_other, key=hash), key=hash)}
        for hval, entities in self_groups.items():
            flag = False
            print('hval=', hval)
            for e in entities:
                print('    ', e.mcnp_repr())
            if hval not in other_groups.keys():
                return False
            if len(entities) != len(other_groups[hval]):
                return False
            for other_entities in permutations(other_groups[hval]):
                for se, oe in zip(entities, other_entities):
                    print(se == oe, ' | ', se.mcnp_repr(), ' | ', oe.mcnp_repr())
                    if not (se == oe):
                        break
                else:
                    flag = True
                    break
            if not flag:
                return False

        if flag:
            return True
        return False

    def __hash__(self):
        return self._hash


class RCC(Surface, _RCC):
    def __init__(self, center, direction, radius, **options):
        center = np.array(center)
        direction = np.array(direction)
        opt_surf = options.copy()
        opt_surf['name'] = 1
        norm = np.array(direction) / np.linalg.norm(direction)
        cyl = Cylinder(center, norm, radius, **opt_surf)
        center2 = center + direction
        offset2 = -np.dot(norm, center2)
        offset3 = np.dot(norm, center)
        opt_surf['name'] = 2
        plane2 = Plane(norm, offset2, **opt_surf)
        opt_surf['name'] = 3
        plane3 = Plane(-norm, offset3, **opt_surf)
        _RCC.__init__(self, cyl, plane2, plane3)
        options.pop('transform', None)
        Surface.__init__(self, **options)
        self._hash = hash(cyl) ^ hash(plane2) ^ hash(plane3)
    
    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, RCC):
            return False
        args_this = self.surfaces
        args_other = other.surfaces
        return args_this == args_other

    def surface(self, number):
        args = self.surfaces
        if 1 <= number <= len(args):
            return args[number - 1]
        else:
            raise ValueError("There is no such surface in macrobody: {0}".format(number))

    def get_params(self):
        args = self.surfaces
        for a in args:
            print(a.mcnp_repr())
        center = args[0]._pt - args[2]._k * args[0]._axis * np.dot(args[0]._axis, args[2]._v)
        direction = -(args[1]._k + args[2]._k) * args[1]._v 
        radius = args[0]._radius
        return center, direction, radius

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        words.append('RCC')
        words.append(' ')
        center, direction, radius = self.get_params()
        values = list(center)
        values.extend(direction)
        values.append(radius)
        for v in values:
            fd = significant_digits(v, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
            words.append(pretty_float(v, fd))
            words.append(' ')
        return words

    def transform(self, tr):
        """Transforms the shape.

        Parameters
        ----------
        tr : Transformation
            Transformation to be applied.

        Returns
        -------
        result : Shape
            New shape.
        """
        center, direction, radius = self.get_params()
        return RCC(center, direction, radius, transform=tr)

    def __getstate__(self):
        surf_state = Surface.__getstate__(self)
        args = self.surfaces
        return args, self._hash, surf_state

    def __setstate__(self, state):
        args, hash_value, surf_state = state
        Surface.__setstate__(self, surf_state)
        _RCC.__init__(self, *args)
        self._hash = hash_value

class BOX:
    """Macrobody RPP surface.

    Parameters
    ----------
    """
    def __init__(self, center, dirx, diry, dirz, **options):
        dirx = np.array(dirx)
        diry = np.array(diry)
        dirz = np.array(dirz)
        center = np.array(center)
        center2 = center + dirx + diry + dirz
        lenx = np.linalg.norm(dirx)
        leny = np.linalg.norm(diry)
        lenz = np.linalg.norm(dirz)
        normx = dirx / lenx
        normy = diry / leny
        normz = dirz / lenz
        offsetx = np.dot(normx, center)
        offsety = np.dot(normy, center)
        offsetz = np.dot(normz, center)
        offset2x = -np.dot(normx, center2)
        offset2y = -np.dot(normy, center2)
        offset2z = -np.dot(normz, center2)
        opt_surf = options.copy()
        opt_surf['name'] = 1
        surf1 = body._Shape('S', Plane(normx, offset2x, **opt_surf))
        opt_surf['name'] = 2
        surf2 = body._Shape('S', Plane(-normx, offsetx, **opt_surf))
        opt_surf['name'] = 3
        surf3 = body._Shape('S', Plane(normy, offset2y, **opt_surf))
        opt_surf['name'] = 4
        surf4 = body._Shape('S', Plane(-normy, offsety, **opt_surf))
        opt_surf['name'] = 5
        surf5 = body._Shape('S', Plane(normz, offset2z, **opt_surf))
        opt_surf['name'] = 6
        surf6 = body._Shape('S', Plane(-normz, offsetz, **opt_surf))
        body._Shape.__init__(self, 'U', surf1, surf2, surf3, surf4, surf5, surf6)
        options.pop('transform', None)
        Surface.__init__(self, **options)
        self._calculate_hash("U", surf1, surf2, surf3, surf4, surf5, surf6)

    @staticmethod
    def _get_plane_intersection(s1, s2, s3):
        matrix = np.zeros((3, 3))
        matrix[0, :] = -s1._v
        matrix[1, :] = -s2._v
        matrix[2, :] = -s3._v
        vector = np.array([s1._k, s2._k, s3._k])
        return np.linalg.solve(matrix, vector)

    def get_params(self):
        args = [a.args[0] for a in self.args]
        center = self._get_plane_intersection(args[1], args[3], args[5])
        point2 = self._get_plane_intersection(args[0], args[2], args[4])
        normx = args[0]._v
        normy = args[2]._v
        normz = args[4]._v
        diag = point2 - center
        dirx = np.dot(normx, diag) * normx
        diry = np.dot(normy, diag) * normy
        dirz = np.dot(normz, diag) * normz
        return center, dirx, diry, dirz

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        words.append('BOX')
        words.append(' ')
        center, dirx, diry, dirz = self.get_params()
        values = list(center)
        values.extend(dirx)
        values.extend(diry)
        values.extend(dirz)
        for v in values:
            fd = significant_digits(v, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
            words.append(pretty_float(v, fd))
            words.append(' ')
        return words

    def transform(self, tr):
        """Transforms the shape.

        Parameters
        ----------
        tr : Transformation
            Transformation to be applied.

        Returns
        -------
        result : Shape
            New shape.
        """
        center, dirx, diry, dirz = self.get_params()
        return BOX(center, dirx, diry, dirz, transform=tr)


class Plane(Surface, _Plane):
    """Plane surface class.

    Parameters
    ----------
    normal : array_like[float]
        The normal to the plane being created.
    offset : float
        Free term.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to this plane.
                             Transformation instance.
    """
    def __init__(self, normal, offset, **options):
        if 'transform' in options.keys():
            tr = options.pop('transform')
            v, k = tr.apply2plane(normal, offset)
        else:
            v = np.array(normal)
            k = offset
        length = np.linalg.norm(v)
        v = v / length
        k /= length
        self._k_digits = significant_digits(k, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._v_digits = significant_array(v, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        Surface.__init__(self, **options)
        _Plane.__init__(self, v, k)
        self.normal = normal
        self.offset = offset

    def copy(self):
        instance = Plane.__new__(Plane, self._v, self._k)
        instance._k_digits = self._k_digits
        instance._v_digits = self._v_digits
        Surface.__init__(instance, **self.options)
        _Plane.__init__(instance, self._v, self._k)
        return instance

    def __hash__(self):
        result = hash(self._get_k())
        for v in self._get_v():
            result ^= hash(v)
        return result

    def __eq__(self, other):
        if not isinstance(other, Plane):
            return False
        else:
            for x, y in zip(self._get_v(), other._get_v()):
                if x != y:
                    return False
            return self._get_k() == other._get_k()

    def _get_k(self):
        return round_scalar(self._k, self._k_digits)

    def _get_v(self):
        return round_array(self._v, self._v_digits)

    def reverse(self):
        """Gets the surface with reversed normal."""
        return Plane(-self._v, -self._k)

    def transform(self, tr):
        return Plane(self._v, self._k, transform=tr, **self.options)

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        if np.all(self._get_v() == EX):
            words.append('PX')
        elif np.all(self._get_v() == EY):
            words.append('PY')
        elif np.all(self._get_v() == EZ):
            words.append('PZ')
        else:
            words.append('P')
            for v, p in zip(self._get_v(), self._v_digits):
                words.append(' ')
                words.append(pretty_float(v, p))
        words.append(' ')
        words.append(pretty_float(-self._get_k(), self._k_digits))
        return print_card(words)

    def __getstate__(self):
        return self._v, self._k, self._k_digits, self._v_digits, Surface.__getstate__(self)

    def __setstate__(self, state):
        v, k, _k_digits, _v_digits, options = state
        _Plane.__init__(self, v, k)
        Surface.__setstate__(self, options)
        self._k_digits, self._v_digits = _k_digits, _v_digits


class Sphere(Surface, _Sphere):
    """Sphere surface class.
    
    Parameters
    ----------
    center : array_like[float]
        Center of the sphere.
    radius : float
        The radius of the sphere.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to the sphere being
                             created. Transformation instance.
    """
    def __init__(self, center, radius, **options):
        if 'transform' in options.keys():
            tr = options.pop('transform')
            center = tr.apply2point(center)
        Surface.__init__(self, **options)
        self._center_digits = significant_array(np.array(center), constants.FLOAT_TOLERANCE,
                                                resolution=constants.FLOAT_TOLERANCE)
        self._radius_digits = significant_digits(radius, constants.FLOAT_TOLERANCE,
                                                 resolution=constants.FLOAT_TOLERANCE)
        _Sphere.__init__(self, center, radius)

    def __getstate__(self):
        return self._center, self._radius, Surface.__getstate__(self)

    def __setstate__(self, state):
        c, r, options = state
        _Sphere.__init__(self, c, r)
        Surface.__setstate__(self, options)

    def copy(self):
        instance = Sphere.__new__(Sphere, self._center, self._radius)
        instance._center_digits = self._center_digits
        instance._radius_digits = self._radius_digits
        Surface.__init__(instance, **self.options)
        _Sphere.__init__(instance, self._center, self._radius)
        return instance

    def __hash__(self):
        result = hash(self._get_radius())
        for c in self._get_center():
            result ^= hash(c)
        return result

    def __eq__(self, other):
        if not isinstance(other, Sphere):
            return False
        else:
            for x, y in zip(self._get_center(), other._get_center()):
                if x != y:
                    return False
            return self._get_radius() == other._get_radius()

    def _get_center(self):
        return round_array(self._center, self._center_digits)

    def _get_radius(self):
        return round_scalar(self._radius, self._radius_digits)

    def transform(self, tr):
        return Sphere(self._center, self._radius, transform=tr, **self.options)

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        if np.all(self._get_center() == np.array([0.0, 0.0, 0.0])):
            words.append('SO')
        elif self._get_center()[0] == 0.0 and self._get_center()[1] == 0.0:
            words.append('SZ')
            words.append(' ')
            v = self._get_center()[2]
            p = self._center_digits[2]
            words.append(pretty_float(v, p))
        elif self._get_center()[1] == 0.0 and self._get_center()[2] == 0.0:
            words.append('SX')
            words.append(' ')
            v = self._get_center()[0]
            p = self._center_digits[0]
            words.append(pretty_float(v, p))
        elif self._get_center()[0] == 0.0 and self._get_center()[2] == 0.0:
            words.append('SY')
            words.append(' ')
            v = self._get_center()[1]
            p = self._center_digits[1]
            words.append(pretty_float(v, p))
        else:
            words.append('S')
            for v, p in zip(self._center, self._center_digits):
                words.append(' ')
                words.append(pretty_float(v, p))
        words.append(' ')
        v = self._get_radius()
        p = self._radius_digits
        words.append(pretty_float(v, p))
        return print_card(words)


class Cylinder(Surface, _Cylinder):
    """Cylinder surface class.
    
    Parameters
    ----------
    pt : array_like[float]
        Point on the cylinder's axis.
    axis : array_like[float]
        Cylinder's axis direction.
    radius : float
        Cylinder's radius.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to the cylinder being
                             created. Transformation instance.
    """
    def __init__(self, pt, axis, radius, **options):
        if 'transform' in options.keys():
            tr = options.pop('transform')
            pt = tr.apply2point(pt)
            axis = tr.apply2vector(axis)
        axis = np.array(axis) / np.linalg.norm(axis)
        maxdir = np.argmax(np.abs(axis))
        if axis[maxdir] < 0:
            axis *= -1
        pt = np.array(pt)
        self._axis_digits = significant_array(axis, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        pt = pt - axis * np.dot(pt, axis)
        self._pt_digits = significant_array(pt, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._radius_digits = significant_digits(radius, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        Surface.__init__(self, **options)
        _Cylinder.__init__(self, pt, axis, radius)

    def __getstate__(self):
        return self._pt, self._axis, self._radius, self._pt_digits, self._axis_digits, self._radius_digits, Surface.__getstate__(self)

    def __setstate__(self, state):
        pt, axis, radius, self._pt_digits, self._axis_digits, self._radius_digits, options = state
        _Cylinder.__init__(self, pt, axis, radius)
        Surface.__setstate__(self, options)

    def copy(self):
        instance = Cylinder.__new__(Cylinder, self._pt, self._axis, self._radius)
        instance._axis_digits = self._axis_digits
        instance._pt_digits = self._pt_digits
        instance._radius_digits = self._radius_digits
        Surface.__init__(instance, **self.options)
        _Cylinder.__init__(instance, self._pt, self._axis, self._radius)
        return instance

    def __hash__(self):
        result = hash(self._get_radius())
        for c in self._get_pt():
            result ^= hash(c)
        for a in self._get_axis():
            result ^= hash(a)
        return result

    def __eq__(self, other):
        if not isinstance(other, Cylinder):
            return False
        else:
            for x, y in zip(self._get_pt(), other._get_pt()):
                if x != y:
                    return False
            for x, y in zip(self._get_axis(), other._get_axis()):
                if x != y:
                    return False
            return self._get_radius() == other._get_radius()

    def _get_pt(self):
        return round_array(self._pt, self._pt_digits)

    def _get_axis(self):
        return round_array(self._axis, self._axis_digits)

    def _get_radius(self):
        return round_scalar(self._radius, self._radius_digits)

    def transform(self, tr):
        return Cylinder(self._pt, self._axis, self._radius, transform=tr,
                        **self.options)

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        if np.all(self._get_axis() == np.array([1.0, 0.0, 0.0])):
            if self._get_pt()[1] == 0.0 and self._get_pt()[2] == 0.0:
                words.append('CX')
            else:
                words.append('C/X')
                words.append(' ')
                v = self._get_pt()[1]
                p = self._pt_digits[1]
                words.append(pretty_float(v, p))
                words.append(' ')
                v = self._get_pt()[2]
                p = self._pt_digits[2]
                words.append(pretty_float(v, p))
        elif np.all(self._get_axis() == np.array([0.0, 1.0, 0.0])):
            if self._get_pt()[0] == 0.0 and self._get_pt()[2] == 0.0:
                words.append('CY')
            else:
                words.append('C/Y')
                words.append(' ')
                v = self._get_pt()[0]
                p = self._pt_digits[0]
                words.append(pretty_float(v, p))
                words.append(' ')
                v = self._get_pt()[2]
                p = self._pt_digits[2]
                words.append(pretty_float(v, p))
        elif np.all(self._get_axis() == np.array([0.0, 0.0, 1.0])):
            if self._get_pt()[0] == 0.0 and self._get_pt()[1] == 0.0:
                words.append('CZ')
            else:
                words.append('C/Z')
                words.append(' ')
                v = self._get_pt()[0]
                p = self._pt_digits[0]
                words.append(pretty_float(v, p))
                words.append(' ')
                v = self._get_pt()[1]
                p = self._pt_digits[1]
                words.append(pretty_float(v, p))
        else:
            nx, ny, nz = self._axis
            m = np.array([[1-nx**2, -nx*ny, -nx*nz],
                          [-nx*ny, 1-ny**2, -ny*nz],
                          [-nx*nz, -ny*nz, 1-nz**2]])
            v = np.zeros(3)
            k = -self._radius**2
            m, v, k = Transformation(translation=self._pt).apply2gq(m, v, k)
            return GQuadratic(m, v, k, **self.options).mcnp_repr()
        words.append(' ')
        v = self._get_radius()
        p = self._radius_digits
        words.append(pretty_float(v, p))
        return print_card(words)


class Cone(Surface, _Cone):
    """Cone surface class.

    Parameters
    ----------
    apex : array_like[float]
        Cone's apex.
    axis : array_like[float]
        Cone's axis.
    ta : float
        Tangent of angle between axis and generatrix.
    sheet : int
        Cone's sheet.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to the cone being
                             created. Transformation instance.
    """
    def __init__(self, apex, axis, ta, sheet=0, **options):
        if 'transform' in options.keys():
            tr = options.pop('transform')
            apex = tr.apply2point(apex)
            axis = tr.apply2vector(axis)
        axis = np.array(axis) / np.linalg.norm(axis)
        maxdir = np.argmax(np.abs(axis))
        if axis[maxdir] < 0:
            axis *= -1
            sheet *= -1
        apex = np.array(apex)
        self._axis_digits = significant_array(axis, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._apex_digits = significant_array(apex, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)

        Surface.__init__(self, **options)
        # TODO: Do something with ta! It is confusing. _Cone accept ta, but returns t2.
        _Cone.__init__(self, apex, axis, ta, sheet)
        self._t2_digits = significant_digits(self._t2, constants.FLOAT_TOLERANCE)

    def copy(self):
        ta = np.sqrt(self._t2)
        instance = Cone.__new__(Cone, self._apex, self._axis, ta, self._sheet)
        instance._axis_digits = self._axis_digits
        instance._apex_digits = self._apex_digits
        instance._t2_digits = self._t2_digits
        Surface.__init__(instance, **self.options)
        _Cone.__init__(instance, self._apex, self._axis, ta, self._sheet)
        return instance

    def __getstate__(self):
        return self._apex, self._axis, self._t2, self._sheet, Surface.__getstate__(self)

    def __setstate__(self, state):
        apex, axis, ta, sheet, options = state
        _Cone.__init__(self, apex, axis, np.sqrt(ta), sheet)
        Surface.__setstate__(self, options)

    def __hash__(self):
        result = hash(self._get_t2()) ^ hash(self._sheet)
        for c in self._get_apex():
            result ^= hash(c)
        for a in self._get_axis():
            result ^= hash(a)
        return result

    def __eq__(self, other):
        if not isinstance(other, Cone):
            return False
        else:
            for x, y in zip(self._get_apex(), other._get_apex()):
                if x != y:
                    return False
            for x, y in zip(self._get_axis(), other._get_axis()):
                if x != y:
                    return False
            return self._get_t2() == other._get_t2() and self._sheet == other._sheet

    def _get_axis(self):
        return round_array(self._axis, self._axis_digits)

    def _get_apex(self):
        return round_array(self._apex, self._apex_digits)

    def _get_t2(self):
        return round_scalar(self._t2, self._t2_digits)

    def transform(self, tr):
        cone = Cone(self._apex, self._axis, np.sqrt(self._t2),
                    sheet=0, transform=tr, **self.options)
        if self._sheet != 0:
            plane = Plane(self._axis, -np.dot(self._axis, self._apex), name=1, transform=tr)
            if self._sheet == +1:
                op = 'C'
            else:
                op = 'S'
            return body.Shape('U', cone, body.Shape(op, plane))
        return cone

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        if np.all(self._get_axis() == np.array([1.0, 0.0, 0.0])):
            if self._get_apex()[1] == 0.0 and self._get_apex()[2] == 0.0:
                words.append('KX')
                words.append(' ')
                v = self._apex[0]
                p = self._apex_digits[0]
                words.append(pretty_float(v, p))
            else:
                words.append('K/X')
                for v, p in zip(self._apex, self._apex_digits):
                    words.append(' ')
                    words.append(pretty_float(v, p))
        elif np.all(self._get_axis() == np.array([0.0, 1.0, 0.0])):
            if self._get_apex()[0] == 0.0 and self._get_apex()[2] == 0.0:
                words.append('KY')
                words.append(' ')
                v = self._apex[1]
                p = self._apex_digits[1]
                words.append(pretty_float(v, p))
            else:
                words.append('K/Y')
                for v, p in zip(self._apex, self._apex_digits):
                    words.append(' ')
                    words.append(pretty_float(v, p))
        elif np.all(self._get_axis() == np.array([0.0, 0.0, 1.0])):
            if self._get_apex()[0] == 0.0 and self._get_apex()[1] == 0.0:
                words.append('KZ')
                words.append(' ')
                v = self._apex[2]
                p = self._apex_digits[2]
                words.append(pretty_float(v, p))
            else:
                words.append('K/Z')
                for v, p in zip(self._apex, self._apex_digits):
                    words.append(' ')
                    words.append(pretty_float(v, p))
        else:
            nx, ny, nz = self._axis
            a = 1 + self._t2
            m = np.array([[1-a*nx**2, -a*nx*ny, -a*nx*nz],
                          [-a*nx*ny, 1-a*ny**2, -a*ny*nz],
                          [-a*nx*nz, -a*ny*nz, 1-a*nz**2]])
            v = np.zeros(3)
            k = 0
            m, v, k = Transformation(translation=self._apex).apply2gq(m, v, k)
            return GQuadratic(m, v, k, **self.options).mcnp_repr()
        words.append(' ')
        v = self._t2
        p = self._t2_digits
        words.append(pretty_float(v, p))
        if self._sheet != 0:
            words.append(' ')
            words.append('{0:d}'.format(self._sheet))
        return words


class GQuadratic(Surface, _GQuadratic):
    """Generic quadratic surface class.

    Parameters
    ----------
    m : array_like[float]
        Matrix of coefficients of quadratic terms. m.shape=(3,3)
    v : array_like[float]
        Vector of coefficients of linear terms. v.shape=(3,)
    k : float
        Free term.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to the surface being
                             created. Transformation instance.
    """
    def __init__(self, m, v, k, **options):
        if 'transform' in options.keys():
            tr = options.pop('transform')
            m, v, k = tr.apply2gq(m, v, k)
        else:
            m = np.array(m)
            v = np.array(v)
            k = k
        L = np.linalg.eigvalsh(m)
        factor = 1 / np.max(np.abs(L))
        self._m_digits = significant_array(m, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._v_digits = significant_array(v, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._k_digits = significant_digits(k, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)

        Surface.__init__(self, **options)
        _GQuadratic.__init__(self, m, v, k, factor)

    def __getstate__(self):
        return self._m, self._v, self._k, self._factor, Surface.__getstate__(self)

    def __setstate__(self, state):
        m, v, k, factor, options = state
        _GQuadratic.__init__(self, m, v, k, factor)
        Surface.__setstate__(self, options)

    def copy(self):
        instance = GQuadratic.__new__(GQuadratic, self._m, self._v, self._k, self._factor)
        instance._m_digits = self._m_digits
        instance._v_digits = self._v_digits
        instance._k_digits = self._k_digits
        Surface.__init__(instance, **self.options)
        _GQuadratic.__init__(instance, self._m, self._v, self._k, self._factor)
        return instance

    def __hash__(self):
        result = hash(self._get_k())
        for v in self._get_v():
            result ^= hash(v)
        for x in self._get_m().ravel():
            result ^= hash(x)
        return result

    def __eq__(self, other):
        if not isinstance(other, GQuadratic):
            return False
        else:
            for x, y in zip(self._get_v(), other._get_v()):
                if x != y:
                    return False
            for x, y in zip(self._get_m().ravel(), other._get_m().ravel()):
                if x != y:
                    return False
            return self._get_k() == other._get_k()

    def _get_m(self):
        return round_array(self._m, self._m_digits)

    def _get_v(self):
        return round_array(self._v, self._v_digits)

    def _get_k(self):
        return round_scalar(self._k, self._k_digits)

    def transform(self, tr):
        return GQuadratic(self._m, self._v, self._k, transform=tr,
                          **self.options)

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        words.append('GQ')
        m = self._get_m()
        a, b, c = np.diag(m)
        d = m[0, 1] + m[1, 0]
        e = m[1, 2] + m[2, 1]
        f = m[0, 2] + m[2, 0]
        g, h, j = self._get_v()
        k = self._get_k()
        for v in [a, b, c, d, e, f, g, h, j, k]:
            words.append(' ')
            p = significant_digits(v, constants.FLOAT_TOLERANCE, constants.FLOAT_TOLERANCE)
            words.append(pretty_float(v, p))
        return print_card(words)


class Torus(Surface, _Torus):
    """Tori surface class.

    Parameters
    ----------
    center : array_like[float]
        The center of torus.
    axis : array_like[float]
        The axis of torus.
    R : float
        Major radius.
    a : float
        Radius parallel to torus axis.
    b : float
        Radius perpendicular to torus axis.
    options : dict
        Dictionary of surface's options. Possible values:
            transform = tr - transformation to be applied to the torus being
                             created. Transformation instance.
    """
    def __init__(self, center, axis, R, a, b, **options):
        if 'transform' in options.keys():
            tr = options.pop('transform')
            center = tr.apply2point(center)
            axis = tr.apply2vector(axis)
        else:
            center = np.array(center)
            axis = np.array(axis)
        axis = axis / np.linalg.norm(axis)
        maxdir = np.argmax(np.abs(axis))
        if axis[maxdir] < 0:
            axis *= -1
        self._axis_digits = significant_array(axis, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._center_digits = significant_array(center, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE)
        self._R_digits = significant_digits(R, constants.FLOAT_TOLERANCE)
        self._a_digits = significant_digits(a, constants.FLOAT_TOLERANCE)
        self._b_digits = significant_digits(b, constants.FLOAT_TOLERANCE)

        Surface.__init__(self, **options)
        _Torus.__init__(self, center, axis, R, a, b)

    def __getstate__(self):
        return self._center, self._axis, self._R, self._a, self._b, Surface.__getstate__(self)

    def __setstate__(self, state):
        center, axis, R, a, b, options = state
        _Torus.__init__(self, center, axis, R, a, b)
        Surface.__setstate__(self, options)

    def copy(self):
        instance = Torus.__new__(Torus, self._center, self._axis, self._R, self._a, self._b)
        instance._axis_digits = self._axis_digits
        instance._center_digits = self._center_digits
        instance._R_digits = self._R_digits
        instance._a_digits = self._a_digits
        instance._b_digits = self._b_digits
        Surface.__init__(instance, **self.options)
        _Torus.__init__(instance, self._center, self._axis, self._R, self._a, self._b)
        return instance

    def __hash__(self):
        result = hash(self._get_R()) ^ hash(self._get_a()) ^ hash(self._get_b())
        for c in self._get_center():
            result ^= hash(c)
        for a in self._get_axis():
            result ^= hash(a)
        return result

    def __eq__(self, other):
        if not isinstance(other, Torus):
            return False
        else:
            for x, y in zip(self._get_center(), other._get_center()):
                if x != y:
                    return False
            for x, y in zip(self._get_axis(), other._get_axis()):
                if x != y:
                    return False
            return self._get_R() == other._get_R() and self._get_a() == other._get_a() and self._get_b() == other._get_b()

    def _get_axis(self):
        return round_array(self._axis, self._axis_digits)

    def _get_center(self):
        return round_array(self._center, self._center_digits)

    def _get_R(self):
        return round_scalar(self._R, self._R_digits)

    def _get_a(self):
        return round_scalar(self._a, self._a_digits)

    def _get_b(self):
        return round_scalar(self._b, self._b_digits)

    def transform(self, tr):
        return Torus(self._center, self._axis, self._R, self._a, self._b,
                     transform=tr, **self.options)

    def mcnp_words(self):
        words = Surface.mcnp_words(self)
        if np.all(self._get_axis() == np.array([1.0, 0.0, 0.0])):
            words.append('TX')
        elif np.all(self._get_axis() == np.array([0.0, 1.0, 0.0])):
            words.append('TY')
        elif np.all(self._get_axis() == np.array([0.0, 0.0, 1.0])):
            words.append('TZ')
        x, y, z = self._get_center()
        values = [x, y, z, self._get_R(), self._get_a(), self._get_b()]
        digits = [*self._center_digits, self._R_digits, self._a_digits, self._b_digits]
        for v, p in zip(values, digits):
            words.append(' ')
            words.append(pretty_float(v, p))
        return print_card(words)
