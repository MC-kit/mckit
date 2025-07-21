#ifndef __SURFACE_H
#define __SURFACE_H

#include "box.h"
#include "common.h"
#include <stddef.h>
#include <stdint.h>

#define SURFACE_SUCCESS 0
#define SURFACE_FAILURE -1

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
    char type;           ///< surface type
    uint64_t last_box;   ///< subdivision code of last tested box
    int last_box_result; ///< last test_box result
};

struct Plane
{
    Surface base;
    double norm[NDIM];
    double offset;
};

struct Sphere
{
    Surface base;
    double center[NDIM];
    double radius;
};

struct Cylinder
{
    Surface base;
    double point[NDIM];
    double axis[NDIM];
    double radius;
};

struct Cone
{
    Surface base;
    double apex[NDIM];
    double axis[NDIM];
    double ta;
    int sheet;
};

struct Torus
{
    Surface base;
    double center[NDIM];
    double axis[NDIM];
    double radius;
    double a;
    double b;
    char degenerate;
    double specpts[NDIM * 2]; ///< Special points, if present.
};

struct GQuadratic
{
    Surface base;
    double m[NDIM * NDIM];
    double v[NDIM];
    double k;
    double factor;
};

struct RCC
{
    Surface base;
    Cylinder *cyl;
    Plane *top;
    Plane *bot;
};

struct BOX
{
    Surface base;
    Plane *planes[BOX_PLANE_NUM];
};

// Methods //

int plane_init(Plane *surf, const double *norm, double offset);

int sphere_init(Sphere *surf, const double *center, double radius);

int cylinder_init(Cylinder *surf, const double *point, const double *axis, double radius);

int cone_init(Cone *surf, const double *apex, const double *axis, double ta, int sheet);

int torus_init(Torus *surf, const double *center, const double *axis, double radius, double a, double b);

int gq_init(GQuadratic *surf, const double *m, const double *v, double k, double factor);

int RCC_init(RCC *surf, Cylinder *cyl, Plane *top, Plane *bot);

int BOX_init(BOX *surf, Plane **planes);

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
