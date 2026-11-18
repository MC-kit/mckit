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

/// surface common data
struct Surface
{
    explicit Surface(char type) : type(type), last_box(0), last_box_result(0)
    {
    }

    char type;           ///< surface type
    uint64_t last_box;   ///< subdivision code of last tested box
    int last_box_result; ///< last test_box result
};

struct Plane
{
    Plane(std::span<const double, NDIM> norm, double offset);

    Surface base;
    std::array<double, NDIM> norm;
    double offset;
};

struct Sphere
{
    Sphere(std::span<const double, NDIM> center, double radius);

    Surface base;
    std::array<double, NDIM> center;
    double radius;
};

struct Cylinder
{
    Cylinder(std::span<const double, NDIM> point, std::span<const double, NDIM> axis, double radius);

    Surface base;
    std::array<double, NDIM> point;
    std::array<double, NDIM> axis;
    double radius;
};

struct Cone
{
    Cone(std::span<const double, NDIM> apex, std::span<const double, NDIM> axis, double ta, int sheet);

    Surface base;
    std::array<double, NDIM> apex;
    std::array<double, NDIM> axis;
    double ta;
    int sheet;
};

struct Torus
{
    Torus(std::span<const double, NDIM> center, std::span<const double, NDIM> axis, double radius, double a, double b);

    Surface base;
    std::array<double, NDIM> center;
    std::array<double, NDIM> axis;
    double radius;
    double a;
    double b;
    char degenerate;
    std::array<std::array<double, NDIM>, 2> specpts; ///< Special points, if present.
};

struct GQuadratic
{
    GQuadratic(std::span<const double, NDIM * NDIM> m, std::span<const double, NDIM> v, double k, double factor);

    Surface base;
    std::array<double, NDIM * NDIM> m;
    std::array<double, NDIM> v;
    double k;
    double factor;
};

struct RCC
{
    RCC(Cylinder *cyl, Plane *top, Plane *bot);

    Surface base;
    Cylinder *cyl;
    Plane *top;
    Plane *bot;
};

struct BOX
{
    explicit BOX(std::span<Plane *, BOX_PLANE_NUM> planes);

    Surface base;
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
