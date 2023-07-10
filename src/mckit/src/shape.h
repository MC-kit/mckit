//
// Created by Roma on 14.04.2018.
//

#ifndef MCKIT_SHAPE_H
#define MCKIT_SHAPE_H

#include <stddef.h>

#include "box.h"
#include "rbtree.h"
#include "surface.h"

#define BOX_INSIDE_SHAPE        +1
#define BOX_CAN_INTERSECT_SHAPE  0
#define BOX_OUTSIDE_SHAPE       -1
#define COLLECT_STAT    1

#define SHAPE_SUCCESS    0
#define SHAPE_FAILURE   -1
#define SHAPE_NO_MEMORY -2
#define SHAPE_WRONG_ARGLENGTH -3

#define invert_opc(opc) ((opc + 3) % 6)


typedef struct Shape Shape;

enum Operation {INTERSECTION=0, COMPLEMENT, EMPTY, UNION, IDENTITY, UNIVERSE};


/// Describes a shape.
///
/// Contains operation code, number of children, pointer to a Surface or child Shapes
struct Shape {
    char opc;               ///< Code of operation applied to arguments (see enum Operation)
    size_t alen;            ///< Length of arguments
    union {
        Surface * surface;
        Shape ** shapes;
    } args;                 ///< Pointer to arguments. It can be either Shape or Surface structures
};


typedef struct ShapeCache ShapeCache;

struct ShapeCache {
    const Shape* shape;
    union {
        SurfaceCache surface_cache;
        ShapeCache ** shape_caches;
    } args;                 ///< Pointer to  either ShapeCache array or SurfaceCache object
    uint64_t last_box;      ///< Subdivision code of last tested box
    int last_box_result;    ///< Result of last test_box call.
    RBTree* stats;          ///< Statistics about argument results.
};

/**
  Initializes Shape struct.

  \param shape Pointer to struct to be initialized
  \param opc   Operation code
  \param alen  Length of arguments
  \param args  A surface or an array of Shapes

  \return SHAPE_NO_MEMORY on memory allocation failure, SHAPE_SUCCESS otherwise
 */
int shape_init(
    Shape * shape,
    char opc,
    size_t alen,
    const void * args
);

void shape_dealloc(Shape * shape);

/// Init ShapeCache for a given Shape.
///
/// \param cache Pointer to cache object to be initialized
/// \param shape Pointer to original shape
/// \return SHAPE_SUCCESS | SHAPE_NO_MEMORY
int shape_cache_init(
    ShapeCache* cache,
    const Shape * shape
);

void shape_cache_dealloc(ShapeCache* shape);

/// Tests box location with respect to the shape.
///
/// \return BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
int shape_test_box(
    ShapeCache * cache,          ///< Shape cache to test.
    const Box * box,        ///< Box to test.
    char collect,           ///< Collect statistics about results.
    size_t * zero_surfaces     ///< The number of surfaces that was tested to be zero.
);

/// Tests box location with respect to a Shape.
///
/// It tries to find out if the box really intersects the shape with desired accuracy.
///
/// \param cache [inout] Pointer to cache with a shape
/// \param box   [in] box
/// \param min_vol [in] minimal volume until which splitting process goes.
/// \param collect [in] Whether to collect statistics about results.
/// \return BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
int shape_ultimate_test_box(
    ShapeCache * cache,
    const Box * box,
    double min_vol,
    char collect
);

/// Tests whether points belong to this shape.
///
/// @return status - SHAPE_SUCCESS | SHAPE_NO_MEMORY
int shape_test_points(
    const Shape * shape,    ///< test shape
    size_t npts,            ///< the number of points
    const double * points,  ///< array of points - NDIM * npts
    char * result           ///< Result - +1 if point belongs to shape, -1
                                ///< otherwise. It must have length npts.
);

/// Gets bounding box, that bounds the shape.
///
/// \param cache  [in] cache for a Shape to de bound
/// \param box    [inout] Start box. It is modified to obtain bounding box.
/// \param tol    [in] Absolute tolerance. When change of box dimensions become smaller than tol
///                    the process of box reduction finishes.
//);
/// \return
int shape_bounding_box(
    ShapeCache * cache,
    Box * box,
    double tol
);


/// Compute volume of a shape.
///
/// \param cache a cache for a Shape to compute volume for
/// \param box Box from which the process of volume finding starts
/// \param min_vol Minimum volume - when volume of the box become smaller than min_vol the process
///                of box splitting finishes.
/// \return computed volume
double shape_volume(
    ShapeCache * cache,
    const Box * box,
    double min_vol
);

/// Gets shape's contour.
///
/// \return the number of points in the contour.
size_t shape_contour(
    ShapeCache * cache,    ///< cache for a Shape
    const Box * box,        ///< Box, where contour is needed.
    double min_vol,         ///< Size of volume to be considered as point
    double * buffer         ///< Buffer, where points are put.
);

/// Resets collected statistics or initializes statistics storage.
///
/// \param  cache a Shape cache to reset statistics members: stats and last_box.
void shape_reset_stat(ShapeCache * cache);

/// Resets cache of shape and all objects involved.
void shape_reset_cache(ShapeCache * shape);

/// Collects statistics about shapes.
///
/// \param cache [inout] cache for a Shape
/// \param box  [in] Global box, where statistics is collected
/// \param min_vol [in] minimal volume, when splitting process stops.
void shape_collect_statistics(
    ShapeCache * cache,
    const Box * box,
    double min_vol
);

/// Gets statistics table.
///
/// \param cache Shape cache
/// \param nrows number of rows
/// \param ncols number of columns
///
/// \return
char * shape_get_stat_table(
    const ShapeCache * cache,
    size_t * nrows,
    size_t * ncols
);

#endif //MCKIT_SHAPE_H
