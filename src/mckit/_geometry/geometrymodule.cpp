#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <numpy/arrayobject.h>

#include <algorithm>
#include <cstring>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "box.h"
#include "shape.h"
#include "surface.h"

#include "box_doc.h"
#include "surf_doc.h"

namespace nb = nanobind;
using namespace nb::literals;

namespace
{
constexpr int MAX_DIM = 5000;        // Size of global box in cm.
constexpr double MIN_VOLUME = 0.001; // Min volume size.

constexpr std::array<double, NDIM> ORIGIN_DATA{0.0, 0.0, 0.0};
constexpr std::array<double, NDIM> EX_DATA{1.0, 0.0, 0.0};
constexpr std::array<double, NDIM> EY_DATA{0.0, 1.0, 0.0};
constexpr std::array<double, NDIM> EZ_DATA{0.0, 0.0, 1.0};

/// The box used as a default search domain for shape algorithms.
const Box &global_box()
{
    static const Box box(ORIGIN_DATA, EX_DATA, EY_DATA, EZ_DATA, MAX_DIM, MAX_DIM, MAX_DIM);
    return box;
}

nb::object make_array_1d(const double *data, size_t size)
{
    npy_intp dims[] = {static_cast<npy_intp>(size)};
    PyObject *array = PyArray_SimpleNew(1, dims, NPY_DOUBLE);
    if (array == nullptr)
        throw nb::python_error();
    std::copy(data, data + size, static_cast<double *>(PyArray_DATA((PyArrayObject *)array)));
    return nb::steal<nb::object>(array);
}

nb::object make_array_2d(const double *data, size_t rows, size_t cols)
{
    npy_intp dims[] = {static_cast<npy_intp>(rows), static_cast<npy_intp>(cols)};
    PyObject *array = PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (array == nullptr)
        throw nb::python_error();
    std::copy(data, data + rows * cols, static_cast<double *>(PyArray_DATA((PyArrayObject *)array)));
    return nb::steal<nb::object>(array);
}

nb::object make_int_array_1d(const int *data, size_t size)
{
    npy_intp dims[] = {static_cast<npy_intp>(size)};
    PyObject *array = PyArray_SimpleNew(1, dims, NPY_INT);
    if (array == nullptr)
        throw nb::python_error();
    std::copy(data, data + size, static_cast<int *>(PyArray_DATA((PyArrayObject *)array)));
    return nb::steal<nb::object>(array);
}

nb::object make_char_array_1d(const char *data, size_t size)
{
    npy_intp dims[] = {static_cast<npy_intp>(size)};
    PyObject *array = PyArray_SimpleNew(1, dims, NPY_BYTE);
    if (array == nullptr)
        throw nb::python_error();
    std::copy(data, data + size, static_cast<char *>(PyArray_DATA((PyArrayObject *)array)));
    return nb::steal<nb::object>(array);
}

nb::object make_char_array_2d(const std::vector<char> &data, size_t rows, size_t cols)
{
    npy_intp dims[] = {static_cast<npy_intp>(rows), static_cast<npy_intp>(cols)};
    PyObject *array = PyArray_SimpleNew(2, dims, NPY_BYTE);
    if (array == nullptr)
        throw nb::python_error();
    if (!data.empty())
        std::memcpy(PyArray_DATA((PyArrayObject *)array), data.data(), data.size());
    return nb::steal<nb::object>(array);
}

/// Converts an array-like object to a 3-element vector.
std::array<double, NDIM> as_dbl_vec(nb::handle obj)
{
    PyObject *array = PyArray_FROM_OTF(obj.ptr(), NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (array == nullptr)
        throw nb::python_error();
    nb::object holder = nb::steal<nb::object>(array);
    if (PyArray_SIZE((PyArrayObject *)array) != NDIM)
        throw std::invalid_argument("Vector of length 3 is expected");
    const double *data = static_cast<const double *>(PyArray_DATA((PyArrayObject *)array));
    return {data[0], data[1], data[2]};
}

/// An owned array-like of points with shape (n, 3) or a single point.
struct PointsView
{
    explicit PointsView(nb::handle obj)
    {
        PyObject *array = PyArray_FROM_OTF(obj.ptr(), NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
        if (array == nullptr)
            throw nb::python_error();
        holder = nb::steal<nb::object>(array);
        const int ndim = PyArray_NDIM((PyArrayObject *)array);
        if (ndim == 0 || ndim > 2)
            throw std::invalid_argument("Vector or matrix are expected");
        if (PyArray_DIM((PyArrayObject *)array, ndim - 1) != NDIM)
            throw std::invalid_argument("Shape (n, 3) is expected");
        const npy_intp size = PyArray_SIZE((PyArrayObject *)array);
        npts = size > NDIM ? static_cast<size_t>(PyArray_DIM((PyArrayObject *)array, 0)) : 1;
        data = static_cast<const double *>(PyArray_DATA((PyArrayObject *)array));
    }

    nb::object holder;
    const double *data = nullptr;
    size_t npts = 0;
};

/// Python-visible shape: owns the C++ shape tree and the cleaned argument
/// tuple. The tuple keeps the child wrappers (and surface wrappers) alive,
/// while the C++ shape only holds raw pointers to them.
struct PyShape
{
    nb::tuple args;
    std::unique_ptr<Shape> impl;
};

const Box &as_box(nb::handle obj)
{
    if (!nb::isinstance<Box>(obj))
        throw std::invalid_argument("Box instance is expected");
    return *nb::cast<const Box *>(obj);
}
} // namespace

NB_MODULE(geometry, m)
{
    if (_import_array() < 0)
        throw nb::python_error();

    m.doc() = "Geometry native objects.";

    nb::class_<Box>(m, "Box", BOX_DOC)
        .def(
            "__init__",
            [](Box *self, nb::object center, double xdim, double ydim, double zdim, nb::object ex, nb::object ey,
               nb::object ez) {
                const auto c = as_dbl_vec(center);
                const auto e1 = ex.is_none() ? EX_DATA : as_dbl_vec(ex);
                const auto e2 = ey.is_none() ? EY_DATA : as_dbl_vec(ey);
                const auto e3 = ez.is_none() ? EZ_DATA : as_dbl_vec(ez);
                new (self) Box(c, e1, e2, e3, xdim, ydim, zdim);
            },
            "center"_a, "xdim"_a, "ydim"_a, "zdim"_a, "ex"_a = nb::none(), "ey"_a = nb::none(), "ez"_a = nb::none())
        .def(
            "copy", [](const Box &box) { return box; }, BOX_COPY_DOC)
        .def(
            "generate_random_points",
            [](const Box &box, nb::handle npts) {
                if (!PyLong_CheckExact(npts.ptr()))
                    throw std::invalid_argument("Integer value is expected");
                const long n = PyLong_AsLong(npts.ptr());
                if (n < 0)
                    throw std::invalid_argument("Integer value is expected");
                std::vector<double> points(static_cast<size_t>(n) * NDIM);
                box.generate_random_points(static_cast<size_t>(n), points.data());
                return make_array_2d(points.data(), static_cast<size_t>(n), NDIM);
            },
            "npts"_a, BOX_GRP_DOC)
        .def(
            "test_points",
            [](const Box &box, nb::object points) {
                PointsView pts(points);
                std::vector<int> result(pts.npts);
                box.test_points(pts.npts, pts.data, result.data());
                return make_int_array_1d(result.data(), result.size());
            },
            "points"_a, BOX_TEST_POINTS_DOC)
        .def(
            "check_intersection",
            [](const Box &box, nb::handle other) {
                const Box &other_box = as_box(other);
                return box_check_intersection(&box, &other_box) != 0;
            },
            "box"_a, BOX_CHECK_INTERSECTION_DOC)
        .def(
            "split",
            [](const Box &box, const std::string &dir, double ratio) {
                int direct;
                if (dir == "auto")
                    direct = BOX_SPLIT_AUTODIR;
                else if (dir == "x")
                    direct = BOX_SPLIT_X;
                else if (dir == "y")
                    direct = BOX_SPLIT_Y;
                else if (dir == "z")
                    direct = BOX_SPLIT_Z;
                else
                    throw std::invalid_argument("Unknown splitting direction.");
                if (ratio <= 0 || ratio >= 1)
                    throw std::invalid_argument("Split ratio is out of range (0, 1).");
                auto [first, second] = box.split(direct, ratio);
                return nb::make_tuple(std::move(first), std::move(second));
            },
            "dir"_a = "auto", "ratio"_a = 0.5, BOX_SPLIT_DOC)
        .def_prop_ro("corners", [](const Box &box) { return make_array_2d(box.corners[0].data(), NCOR, NDIM); })
        .def_prop_ro("volume", [](const Box &box) { return box.volume; })
        .def_prop_ro("bounds",
                     [](const Box &box) {
                         double bounds[NDIM][2];
                         for (int i = 0; i < NDIM; ++i)
                         {
                             bounds[i][0] = box.lb[i];
                             bounds[i][1] = box.ub[i];
                         }
                         return make_array_2d(&bounds[0][0], NDIM, 2);
                     })
        .def_prop_ro("center", [](const Box &box) { return make_array_1d(box.center.data(), NDIM); })
        .def_prop_ro("dimensions", [](const Box &box) { return make_array_1d(box.dims.data(), NDIM); })
        .def_prop_ro("ex", [](const Box &box) { return make_array_1d(box.ex.data(), NDIM); })
        .def_prop_ro("ey", [](const Box &box) { return make_array_1d(box.ey.data(), NDIM); })
        .def_prop_ro("ez", [](const Box &box) { return make_array_1d(box.ez.data(), NDIM); });

    nb::class_<Surface>(m, "Surface", "Surface base class")
        .def(
            "test_points",
            [](const Surface &surface, nb::object points) {
                PointsView pts(points);
                std::vector<char> result(pts.npts);
                surface_test_points(&surface, pts.npts, pts.data, result.data());
                return make_char_array_1d(result.data(), result.size());
            },
            "points"_a, SURF_TEST_POINTS_DOC)
        .def(
            "test_box",
            [](Surface &surface, nb::handle box) {
                const Box &box_ref = as_box(box);
                surface.last_box = 0;
                return surface_test_box(&surface, &box_ref);
            },
            "box"_a, SURF_TEST_BOX_DOC);

    nb::class_<Plane, Surface>(m, "Plane", "Plane class")
        .def(
            "__init__",
            [](Plane *self, nb::object norm, double offset) {
                const auto n = as_dbl_vec(norm);
                new (self) Plane(n, offset);
            },
            "norm"_a, "offset"_a)
        .def_prop_ro("_v", [](const Plane &plane) { return make_array_1d(plane.norm.data(), NDIM); })
        .def_prop_ro("_k", [](const Plane &plane) { return plane.offset; });

    nb::class_<Sphere, Surface>(m, "Sphere", "Sphere class")
        .def(
            "__init__",
            [](Sphere *self, nb::object center, double radius) {
                const auto c = as_dbl_vec(center);
                new (self) Sphere(c, radius);
            },
            "center"_a, "radius"_a)
        .def_prop_ro("_center", [](const Sphere &sphere) { return make_array_1d(sphere.center.data(), NDIM); })
        .def_prop_ro("_radius", [](const Sphere &sphere) { return sphere.radius; });

    nb::class_<Cylinder, Surface>(m, "Cylinder", "Cylinder class")
        .def(
            "__init__",
            [](Cylinder *self, nb::object point, nb::object axis, double radius) {
                const auto p = as_dbl_vec(point);
                const auto a = as_dbl_vec(axis);
                new (self) Cylinder(p, a, radius);
            },
            "point"_a, "axis"_a, "radius"_a)
        .def_prop_ro("_pt", [](const Cylinder &cylinder) { return make_array_1d(cylinder.point.data(), NDIM); })
        .def_prop_ro("_axis", [](const Cylinder &cylinder) { return make_array_1d(cylinder.axis.data(), NDIM); })
        .def_prop_ro("_radius", [](const Cylinder &cylinder) { return cylinder.radius; });

    nb::class_<Cone, Surface>(m, "Cone", "Cone class")
        .def(
            "__init__",
            [](Cone *self, nb::object apex, nb::object axis, double ta, int sheet) {
                const auto a = as_dbl_vec(apex);
                const auto b = as_dbl_vec(axis);
                new (self) Cone(a, b, ta, sheet);
            },
            "apex"_a, "axis"_a, "ta"_a, "sheet"_a)
        .def_prop_ro("_apex", [](const Cone &cone) { return make_array_1d(cone.apex.data(), NDIM); })
        .def_prop_ro("_axis", [](const Cone &cone) { return make_array_1d(cone.axis.data(), NDIM); })
        .def_prop_ro("_t2", [](const Cone &cone) { return cone.ta; })
        .def_prop_ro("_sheet", [](const Cone &cone) { return cone.sheet; });

    nb::class_<Torus, Surface>(m, "Torus", "Torus class")
        .def(
            "__init__",
            [](Torus *self, nb::object center, nb::object axis, double radius, double a, double b) {
                const auto c = as_dbl_vec(center);
                const auto ax = as_dbl_vec(axis);
                new (self) Torus(c, ax, radius, a, b);
            },
            "center"_a, "axis"_a, "r"_a, "a"_a, "b"_a)
        .def_prop_ro("_center", [](const Torus &torus) { return make_array_1d(torus.center.data(), NDIM); })
        .def_prop_ro("_axis", [](const Torus &torus) { return make_array_1d(torus.axis.data(), NDIM); })
        .def_prop_ro("_R", [](const Torus &torus) { return torus.radius; })
        .def_prop_ro("_a", [](const Torus &torus) { return torus.a; })
        .def_prop_ro("_b", [](const Torus &torus) { return torus.b; });

    nb::class_<GQuadratic, Surface>(m, "GQuadratic", "GQuadratic class")
        .def(
            "__init__",
            [](GQuadratic *self, nb::object m_obj, nb::object v_obj, double k, double factor) {
                PyObject *array = PyArray_FROM_OTF(m_obj.ptr(), NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
                if (array == nullptr)
                    throw nb::python_error();
                nb::object holder = nb::steal<nb::object>(array);
                const int ndim = PyArray_NDIM((PyArrayObject *)array);
                if (ndim == 0 || ndim > 2)
                    throw std::invalid_argument("Vector or matrix are expected");
                if (PyArray_DIM((PyArrayObject *)array, ndim - 1) != NDIM)
                    throw std::invalid_argument("Shape (n, 3) is expected");
                if (PyArray_SIZE((PyArrayObject *)array) < NDIM * NDIM)
                    throw std::invalid_argument("Shape (3, 3) is expected");
                const double *matrix = static_cast<const double *>(PyArray_DATA((PyArrayObject *)array));
                const auto v = as_dbl_vec(v_obj);
                std::array<double, NDIM * NDIM> m{};
                for (size_t i = 0; i < NDIM * NDIM; ++i)
                    m[i] = matrix[i];
                new (self) GQuadratic(m, v, k, factor);
            },
            "m"_a, "v"_a, "k"_a, "factor"_a)
        .def_prop_ro("_m", [](const GQuadratic &gq) { return make_array_2d(gq.m.data(), NDIM, NDIM); })
        .def_prop_ro("_v", [](const GQuadratic &gq) { return make_array_1d(gq.v.data(), NDIM); })
        .def_prop_ro("_k", [](const GQuadratic &gq) { return gq.k; })
        .def_prop_ro("_factor", [](const GQuadratic &gq) { return gq.factor; });

    nb::class_<RCC, Surface>(m, "RCC", "RCC class")
        .def(
            "__init__",
            [](RCC *self, Cylinder *cyl, Plane *top, Plane *bot) {
                if (cyl == nullptr)
                    throw std::invalid_argument("Cylinder instance is expected");
                if (top == nullptr || bot == nullptr)
                    throw std::invalid_argument("Plane instance is expected");
                new (self) RCC(cyl, top, bot);
            },
            "cyl"_a, "top"_a, "bot"_a, nb::keep_alive<1, 2>(), nb::keep_alive<1, 3>(), nb::keep_alive<1, 4>())
        .def_prop_ro("surfaces", [](const RCC &rcc) {
            return nb::make_tuple(nb::find(rcc.cyl), nb::find(rcc.top), nb::find(rcc.bot));
        });

    nb::class_<BOX, Surface>(m, "BOX", "BOX class")
        .def(
            "__init__",
            [](BOX *self, Plane *p0, Plane *p1, Plane *p2, Plane *p3, Plane *p4, Plane *p5) {
                std::array<Plane *, BOX_PLANE_NUM> planes{p0, p1, p2, p3, p4, p5};
                for (Plane *plane : planes)
                {
                    if (plane == nullptr)
                        throw std::invalid_argument("Plane instance is expected");
                }
                new (self) BOX(planes);
            },
            "plane1"_a, "plane2"_a, "plane3"_a, "plane4"_a, "plane5"_a, "plane6"_a, nb::keep_alive<1, 2>(),
            nb::keep_alive<1, 3>(), nb::keep_alive<1, 4>(), nb::keep_alive<1, 5>(), nb::keep_alive<1, 6>(),
            nb::keep_alive<1, 7>())
        .def_prop_ro("surfaces", [](const BOX &box) {
            nb::list result;
            for (Plane *plane : box.planes)
                result.append(nb::find(plane));
            return nb::tuple(result);
        });

    nb::class_<PyShape>(m, "Shape", "Shape class")
        .def(
            "__init__",
            [](PyShape *self, const std::string &opc_str, nb::args raw) {
                if (opc_str.size() != 1)
                    throw std::invalid_argument("Unknown operation");
                const int opc = opc_from_char(opc_str[0]);
                if (opc < 0)
                    throw std::invalid_argument("Unknown operation");

                std::unique_ptr<Shape> impl;
                if (opc == IDENTITY || opc == COMPLEMENT)
                {
                    if (raw.size() != 1)
                        throw std::invalid_argument("Only one operand is expected.");
                    if (!nb::isinstance<Surface>(raw[0]))
                        throw std::invalid_argument("Surface instance is expected...");
                    impl = make_shape(opc, nb::cast<Surface *>(raw[0]));
                }
                else if (opc == EMPTY || opc == UNIVERSE)
                {
                    if (!raw.empty())
                        throw std::invalid_argument("No arguments are expected.");
                    impl = make_shape(opc);
                }
                else
                {
                    if (raw.size() < 2)
                        throw std::invalid_argument("More than one shape object is expected");
                    std::vector<Shape *> children;
                    children.reserve(raw.size());
                    for (nb::handle arg : raw)
                    {
                        if (!nb::isinstance<PyShape>(arg))
                            throw std::invalid_argument("Shape instance is expected.");
                        children.push_back(nb::cast<PyShape *>(arg)->impl.get());
                    }
                    impl = make_shape(opc, children);
                }

                new (self) PyShape{nb::tuple(raw), std::move(impl)};
            },
            "opc"_a, "args"_a)
        .def_prop_ro("opc", [](const PyShape &shape) { return std::string(opc_name(shape.impl->opc())); })
        .def_prop_ro("invert_opc",
                     [](const PyShape &shape) { return std::string(opc_name(invert_opc(shape.impl->opc()))); })
        .def_prop_ro("args", [](const PyShape &shape) { return shape.args; })
        .def(
            "test_points",
            [](const PyShape &shape, nb::object points) {
                PointsView pts(points);
                std::vector<char> result(pts.npts);
                shape.impl->test_points(pts.npts, pts.data, result.data());
                return make_char_array_1d(result.data(), result.size());
            },
            "points"_a, "Tests senses of the points with respect to the surface.")
        .def(
            "test_box",
            [](PyShape &shape, nb::handle box) {
                const Box &box_ref = as_box(box);
                shape.impl->reset_cache();
                return shape.impl->test_box(box_ref, 0, nullptr);
            },
            "box"_a, "Tests where the box is located with respect to the surface.")
        .def(
            "ultimate_test_box",
            [](PyShape &shape, nb::object box, double min_volume, bool collect) {
                const Box &box_ref = box.is_none() ? global_box() : as_box(box);
                shape.impl->reset_cache();
                return shape.impl->ultimate_test_box(box_ref, min_volume, collect ? 1 : 0);
            },
            "box"_a = nb::none(), "min_volume"_a = MIN_VOLUME, "collect"_a = false)
        .def(
            "bounding_box",
            [](PyShape &shape, double tol, nb::object box) {
                const Box &start = box.is_none() ? global_box() : as_box(box);
                Box result(start);
                shape.impl->reset_cache();
                {
                    nb::gil_scoped_release release;
                    shape.impl->bounding_box(result, tol);
                }
                return result;
            },
            "tol"_a = 100.0, "box"_a = nb::none())
        .def(
            "volume",
            [](PyShape &shape, nb::object box, double min_volume) {
                const Box &box_ref = box.is_none() ? global_box() : as_box(box);
                shape.impl->reset_cache();
                double volume;
                {
                    nb::gil_scoped_release release;
                    volume = shape.impl->volume(box_ref, min_volume);
                }
                return volume;
            },
            "box"_a = nb::none(), "min_volume"_a = MIN_VOLUME)
        .def(
            "collect_statistics",
            [](PyShape &shape, nb::handle box, double min_vol) {
                const Box &box_ref = as_box(box);
                shape.impl->reset_cache();
                shape.impl->collect_statistics(box_ref, min_vol);
            },
            "box"_a, "min_vol"_a)
        .def("get_stat_table", [](const PyShape &shape) {
            size_t nrows = 0;
            size_t ncols = 0;
            const std::vector<char> table = shape.impl->get_stat_table(nrows, ncols);
            return make_char_array_2d(table, nrows, ncols);
        });

    m.attr("ORIGIN") = make_array_1d(ORIGIN_DATA.data(), NDIM);
    m.attr("EX") = make_array_1d(EX_DATA.data(), NDIM);
    m.attr("EY") = make_array_1d(EY_DATA.data(), NDIM);
    m.attr("EZ") = make_array_1d(EZ_DATA.data(), NDIM);
    m.attr("GLOBAL_BOX") = nb::cast(global_box());
    m.attr("MIN_VOLUME") = MIN_VOLUME;
}
