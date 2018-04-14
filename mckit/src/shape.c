//
// Created by Roma on 14.04.2018.
//

#include "shape.h"

#define is_final(opc) (opc == COMPLEMENT || opc == IDENTITY)
#define is_void(opc)  (opc == EMPTY || opc == UNIVERSE)
#define is_composite(opc) (opc == UNION || opc == INTERSECTION)
#define invert_opc(opc) ((opc + 3) % 6)

#define geom_complement(arg) (-1 * (arg))

char geom_intersection(char * args, size_t n, size_t inc);
char geom_union(char * args, size_t n, size_t inc);

// Initializes shape struct
int shape_init(
        Shape * shape,          // Pointer to struct to be initialized
        char opc,               // Operation code
        size_t alen,            // Length of arguments
        const void * args       // Argument array.
)
{
    shape->opc = opc;
    shape->alen = alen;
    if (is_void(opc)) {
        shape->args = 0;
    } else if (is_final(opc)) {
        shape->args = args;
    } else {
        shape->args = malloc(alen * sizeof(Shape *));
        if (shape->args == NULL) return SHAPE_FAILURE;
        size_t i;
        for (i = 0; i < alen; ++i) shape->args[i] = args[i];
    }
    return SHAPE_SUCCESS;
}

void shape_dealloc(Shape * shape)
{
    if (shape->args != NULL) free(shape->args);
    if (shape->stats != NULL) rbtree_free(shape->stats);
}

// Tests box location with respect to the shape.
// Returns BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
//
int shape_test_box(
        Shape * shape,          // Shape to test.
        const Box * box,        // Box to test.
        char collect            // Collect statistics about results.
)
{
    if (shape->last_box != 0) {
        int bc = box_is_in(box, shape->last_box);
        // if it is the box already tested (bc == 0) then returns cached result;
        // if it is inner box - then returns cached result only if it is not 0. For inner box result may be different.
        if (bc == 0 || bc > 0 && shape->last_box_result != BOX_CAN_INTERSECT_SHAPE)
            return shape->last_box_result;
    }

    int result;
    if (is_final(shape->opc)) {
        result = surface_test_box(shape->args, box);
        if (shape->opc == COMPLEMENT) result = geom_complement(result);
    } else if (shape->opc == UNIVERSE) {
        result = BOX_INSIDE_SHAPE;
    } else if (shape->opc == EMPTY) {
        result = BOX_OUTSIDE_SHAPE;
    } else {
        char sub[shape->alen];
        for (i = 0; i < shape->alen; ++i) {
            sub[i] = shape_test_box(shape->args[i], box, collect);
        }

        if (shape->opc == INTERSECTION) {
            result = geom_intersection(sub, shape->alen, 1);
        } else {
            result = geom_union(sub, shape->alen, 1);
        }

        /* TODO: Review statistics collection
        if (collect && result != 0) {
            StatUnit * stat = (StatUnit *) malloc(sizeof(StatUnit));
            stat->arr = sub;
            stat->len = n;
            double * vol = map_get(node->stats, stat);
            if (vol == NULL) {
                vol = (double *) malloc(sizeof(double));
                *vol = box->volume;
                map_add(node->stats, stat, vol);
            } else {
                *vol += box->volume;
                free(sub);
                free(stat);
            }
        } else free(sub); */
    }
    // Cash test result;
    shape->last_box = box->subdiv;
    shape->last_box_result = result;
    return result;
}

// Tests box location with respect to the shape. It tries to find out
// if the box really intersects the shape with desired accuracy.
// Returns BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
int shape_ultimate_test_box(
        Shape * shape,          // Pointer to shape
        const Box * box,        // box
        double min_vol          // minimal volume until which splitting process goes.
)
{
    int result = shape_test_box(shape, box, 0);
    if (result == BOX_CAN_INTERSECT_SHAPE && box->volume > min_vol) {
        Box box1, box2;
        box_split(box, &box1, &box2, BOX_SPLIT_AUTODIR, 0.5);
        int result1 = shape_ultimate_test_box(shape, box1, min_vol);
        int result2 = shape_ultimate_test_box(shape, box2, min_vol);
        if (result1 != BOX_CAN_INTERSECT_SHAPE && result2 != BOX_CAN_INTERSECT_SHAPE)
            return result1;     // No matter what value (result1 or result2) is returned because they
                                // will be equal.
    }
    return result;
}

// Tests whether points belong to this shape.
// Returns status - SHAPE_SUCCESS | SHAPE_NO_MEMORY
//
int shape_test_points(
        const Shape * shape,    // test shape
        size_t npts,            // the number of points
        const double * points,  // array of points - NDIM * npts
        int * result            // Result - +1 if point belongs to shape, -1
                                // otherwise. It must have length npts.
)
{
    int i;
    if (is_final(shape->opc)) {
        surface_test_points(shape->args, npts, points, result);
        if (shape->opc == COMPLEMENT)
            for (i = 0; i < npts; ++i) result[i] = geom_complement(result[i]);
    } else if (is_void(shape->opc)) {
        char fill = (shape->opc == UNIVERSE) ? 1 : -1;
        for (i = 0; i < npts; ++i) result[i] = fill;
    } else {
        char (*op)(char * arg, size_t n, size_t inc);
        op = (shape->opc == INTERSECTION) ? geom_intersection : geom_union;

        size_t n = shape->len;
        int * sub = malloc(n * npts * sizeof(int));
        if (sub == NULL) return SHAPE_NO_MEMORY;

        for (i = 0; i < n; ++i) {
            shape_test_points(shape->args[i], npts, points, sub + i * npts);
        }
        for (i = 0; i < npts; ++i) result[i] = (*op)(sub, n * npts, npts);
        free(sub);
    }
    return NODE_SUCCESS;
}

// Gets bounding box, that bounds the shape.
int shape_bounding_box(
        const Shape * shape,    // Shape to de bound
        Box * box,              // INOUT: Start box. It is modified to obtain bounding box.
        double tol              // Absolute tolerance. When change of box dimensions become smaller than tol
                                // the process of box reduction finishes.
)
{
    double lower, upper, ratio;
    int dim, tl, min_vol = tol * tol * tol;
    Box box1, box2;
    for (dim = 0; dim < NDIM; ++dim) {
        lower = 0;
        while (box->dims[dim] - lower > tol) {
            ratio = 0.5 * (lower + box->dims[dim]) / box->dims[dim];
            box_split(box, &box1, &box2, dim, ratio);
            tl = shape_ultimate_test_box(shape, &box2, min_vol);
            if (tl == -1) box_copy(box, &box1);
            else lower = box1.dims[dim];
        }
        upper = 0;
        while (box->dims[dim] - upper > tol) {
            ratio = 0.5 * (box->dims[dim] - upper) / box->dims[dim];
            box_split(box, &box1, &box2, dim, ratio);
            tl = shape_ultimate_test_box(shape, &box1, min_vol);
            if (tl == -1) box_copy(box, &box2);
            else upper = box2.dims[dim];
        }
    }
    return NODE_SUCCESS;
}

// Gets volume of the shape
double shape_volume(
        const Shape * shape,    // Shape
        const Box * box,        // Box from which the process of volume finding starts
        double min_vol          // Minimum volume - when volume of the box become smaller than min_vol the process
        // of box splitting finishes.
)
{
    int result = shape_test_box(shape, box, 0);
    if (result == BOX_INSIDE_SHAPE) return box->volume;   // Box totally belongs to the shape
    if (result == BOX_OUTSIDE_SHAPE) return 0;             // Box don't belong to the shape
    if (box->volume > min_vol) {            // Shape intersects the box
        Box box1, box2;
        box_split(box, box1, box2, BOX_SPLIT_AUTODIR, 0.5);
        double vol1 = shape_volume(shape, box1, min_vol);
        double vol2 = shape_volume(shape, box2, min_vol);
        return vol1 + vol2;
    } else {                        // Minimum volume has been reached, but shape still intersects box
        return 0.5 * box->volume;   // This is statistical decision. On average a half of the box belongs to the shape.
    }
}

// Operation functions

char geom_intersection(char * args, size_t n, size_t inc) {
    size_t i;
    char result = +1;
    for (i = 0; i < n; i += inc) {
        if (*(args + i) == 0) result = 0;
        else if (*(args + i) == -1) {
            result = -1;
            break;
        }
    }
    return result;
}

char geom_union(char * args, size_t n, size_t inc) {
    size_t i;
    char result = -1;
    for (i = 0; i < n; i += inc) {
        if (*(args + i) == 0) result = 0;
        else if (*(args + i) == +1) {
            result = +1;
            break;
        }
    }
    return result;
}
