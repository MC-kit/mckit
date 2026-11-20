#ifndef MCKIT_SURFACE_H
#define MCKIT_SURFACE_H

#include "box.h"
#include "common.h"
#include <array>
#include <span>
#include <stddef.h>
#include <stdint.h>

#define BOX_PLANE_NUM 6

typedef struct Surface Surface;
typedef struct Plane Plane;
typedef struct Sphere Sphere;
typedef struct Cylinder Cylinder;
typedef struct Cone Cone;
typedef struct Torus Torus;
typedef struct GQuadratic GQuadratic;
typedef struct RCC RCC;
typedef struct BOX BOX;

enum SurfType
{
    PLANE = 1,
    SPHERE,
    CYLINDER,
    CONE,
    TORUS,
    GQUADRATIC,
    MRCC,
    MBOX
};

/// Base class of all surfaces.
///
/// The concrete surface type is still available as `type`, because some
/// algorithms (box tests, caching) need cheap type checks. The geometry
/// function itself is virtual, so algorithms do not need a type switch.
struct Surface
{
    explicit Surface(SurfType type) : type(type)
    {
    }

    Surface(const Surface &) = delete;
    Surface &operator=(const Surface &) = delete;

    virtual ~Surface() = default;

    /// Deviation of the point x from the surface.
    ///
    /// @param n Space dimension (must be NDIM).
    /// @param x Point to be checked.
    /// @param grad Gradient - calculated if not nullptr.
    virtual double func(unsigned int n, const double *x, double *grad) const = 0;

    SurfType type;       ///< surface type
    uint64_t last_box;   ///< subdivision code of last tested box
    int last_box_result; ///< last test_box result
};

struct Plane : Surface
{
    Plane(std::span<const double, NDIM> norm, double offset);

    double func(unsigned int n, const double *x, double *grad) const override;

    std::array<double, NDIM> norm;
    double offset;
};

struct Sphere : Surface
{
    Sphere(std::span<const double, NDIM> center, double radius);

    double func(unsigned int n, const double *x, double *grad) const override;

    std::array<double, NDIM> center;
    double radius;
};

struct Cylinder : Surface
{
    Cylinder(std::span<const double, NDIM> point, std::span<const double, NDIM> axis, double radius);

    double func(unsigned int n, const double *x, double *grad) const override;

    std::array<double, NDIM> point;
    std::array<double, NDIM> axis;
    double radius;
};

struct Cone : Surface
{
    Cone(std::span<const double, NDIM> apex, std::span<const double, NDIM> axis, double ta, int sheet);

    double func(unsigned int n, const double *x, double *grad) const override;

    std::array<double, NDIM> apex;
    std::array<double, NDIM> axis;
    double ta;
    int sheet;
};

struct Torus : Surface
{
    Torus(std::span<const double, NDIM> center, std::span<const double, NDIM> axis, double radius, double a, double b);

    double func(unsigned int n, const double *x, double *grad) const override;

    std::array<double, NDIM> center;
    std::array<double, NDIM> axis;
    double radius;
    double a;
    double b;
    char degenerate;
    std::array<std::array<double, NDIM>, 2> specpts; ///< Special points, if present.
};

struct GQuadratic : Surface
{
    GQuadratic(std::span<const double, NDIM * NDIM> m, std::span<const double, NDIM> v, double k, double factor);

    double func(unsigned int n, const double *x, double *grad) const override;

    std::array<double, NDIM * NDIM> m;
    std::array<double, NDIM> v;
    double k;
    double factor;
};

/// Right circular cylinder macrobody: a cylinder clipped by two planes.
struct RCC : Surface
{
    RCC(Cylinder *cyl, Plane *top, Plane *bot);

    double func(unsigned int n, const double *x, double *grad) const override;

    Cylinder *cyl;
    Plane *top;
    Plane *bot;
};

/// Box macrobody: an intersection of six planes.
struct BOX : Surface
{
    explicit BOX(std::span<Plane *, BOX_PLANE_NUM> planes);

    double func(unsigned int n, const double *x, double *grad) const override;

    Plane *planes[BOX_PLANE_NUM];
};

// Methods //

/**
 * Interface to all surface functions. Decides, which function to apply.
 *
 * The function is passed as a callback to the C NLopt library,
 * so it must have C linkage.
 */
extern "C" double surface_func(unsigned int n,  // Space dimension (NDIM)
                               const double *x, // Point to be checked
                               double *grad,    // Gradient - calculated if not NULL (array of size NDIM)
                               void *f_data     // Surface data
);

/// Tests senses of points with respect to the surface.
void surface_test_points(const Surface *surf,  ///< Surface
                         size_t npts,          ///< The number of points to be tested
                         const double *points, ///< Points to be tested
                         char *result          ///< The result - +1 if point has positive
                                               ///< sense and -1 if negative.
);

/**
 * Tests if the surface intersects the box.
 *
 * @return
 *     0 - surface intersects the box;
 *    +1 - box lies on the positive side of surface;
 *    -1 - box lies on the negative side of surface.
 */
int surface_test_box(Surface *surf, ///< surface to test
                     const Box *box ///< box to test
);

#endif
