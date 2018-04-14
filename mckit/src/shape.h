//
// Created by Roma on 14.04.2018.
//

#ifndef MCKIT_SHAPE_H
#define MCKIT_SHAPE_H

#include <stddef.h>

#include "box.h"
#include "rbtree.h"

#define BOX_INSIDE_SHAPE        +1
#define BOX_CAN_INTERSECT_SHAPE  0
#define BOX_OUTSIDE_SHAPE       -1
#define COLLECT_STAT    1

#define SHAPE_SUCCESS    0
#define SHAPE_FAILURE   -1
#define SHAPE_NO_MEMORY -2
#define SHAPE_WRONG_ARGLENGTH -3


typedef struct Shape Shape;

enum Operation {INTERSECTION=0, COMPLEMENT, EMPTY, UNION, IDENTITY, UNIVERSE};

// Describes a shape.
struct Shape {
    char opc;               // Code of operation applied to arguments (see enum Operation)
    size_t alen;            // Length of arguments
    void * args;            // Pointer to arguments. It can be either Shape or Surface structures
    uint64_t last_box;      // Subdivision code of last tested box
    int last_box_result;    // Result of last test_box call.
    RBTree * stats;         // Statistics about argument results.
};

// Initializes shape struct
int shape_init(
        Shape * shape,          // Pointer to struct to be initialized
        char opc,               // Operation code
        size_t alen,            // Length of arguments
        const void * args       // Argument array.
);

void shape_dealloc(Shape * shape);

// Tests box location with respect to the shape.
// Returns BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
//
int shape_test_box(
        Shape * shape,          // Shape to test.
        const Box * box,        // Box to test.
        char collect            // Collect statistics about results.
);

// Tests box location with respect to the shape. It tries to find out
// if the box really intersects the shape with desired accuracy.
// Returns BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
int shape_ultimate_test_box(
        Shape * shape,          // Pointer to shape
        const Box * box,        // box
        double min_vol,         // minimal volume until which splitting process goes.
        char collect            // Whether to collect statistics about results.
);

// Tests whether points belong to this shape.
// Retruns status - SHAPE_SUCCESS | SHAPE_NO_MEMORY
//
int shape_test_points(
        const Shape * shape,    // test shape
        size_t npts,            // the number of points
        const double * points,  // array of points - NDIM * npts
        int * result            // Result - +1 if point belongs to shape, -1
                                // otherwise. It must have length npts.
);

// Gets bounding box, that bounds the shape.
int shape_bounding_box(
        const Shape * shape,    // Shape to de bound
        Box * box,              // INOUT: Start box. It is modified to obtain bounding box.
        double tol              // Absolute tolerance. When change of box dimensions become smaller than tol
                                // the process of box reduction finishes.
);

// Gets volume of the shape
double shape_volume(
        const Shape * shape,    // Shape
        const Box * box,        // Box from which the process of volume finding starts
        double min_vol          // Minimum volume - when volume of the box become smaller than min_vol the process
                                // of box splitting finishes.
);

// Resets collected statistics or initializes statistics storage
void shape_reset_stat(Shape * shape);

// Collects statistics about shapes.
int collect_statistics(
        size_t n,               // The number of shapes
        Shape * shapes,         // Array of shapes
        const Box * box,        // Global box, where statistics is collected
        double min_vol          // minimal volume, when splitting process stops.
);

#endif //MCKIT_SHAPE_H
