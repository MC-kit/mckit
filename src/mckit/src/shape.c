//
// Created by Roma on 14.04.2018.
//

#include "shape.h"
#include "surface.h"
#include <stdlib.h>

#define is_final(opc) (opc == COMPLEMENT || opc == IDENTITY)
#define is_void(opc) (opc == EMPTY || opc == UNIVERSE)
#define is_composite(opc) (opc == UNION || opc == INTERSECTION)

#define geom_complement(arg) (-1 * (arg))

char geom_intersection(char *args, size_t n, size_t inc);

char geom_union(char *args, size_t n, size_t inc);

typedef struct StatUnit StatUnit;

struct StatUnit
{
    char *arr;
    size_t len;
    double vol;
};

static int stat_compare(const StatUnit *a, const StatUnit *b)
{
    size_t i, n = a->len;
    for (i = 0; i < n; ++i)
    {
        if (a->arr[i] < b->arr[i])
            return 1;
        else if (a->arr[i] > b->arr[i])
            return -1;
    }
    return 0;
}

/**
  Initializes Shape struct.

  @param shape Pointer to struct to be initialized
  @param opc   Operation code
  @param alen  Length of arguments
  @param args  A surface or an array of Shapes

  @return SHAPE_NO_MEMORY on memory allocation failure, SHAPE_SUCCESS otherwise
 */
int shape_init(Shape *shape, char opc, size_t alen, const void *args)
{
    shape->opc = opc;
    shape->alen = alen;
    shape->stats = rbtree_create(stat_compare);
    shape->last_box = 0;
    shape->last_box_result = 0;
    if (is_final(opc))
    {
        shape->args.surface = (Surface *)args;
    }
    else if (is_void(opc))
    {
        shape->args.surface = NULL;
    }
    else
    {
        shape->args.shapes = (Shape **)malloc(alen * sizeof(Shape *));

        if (shape->args.shapes == NULL)
            return SHAPE_NO_MEMORY;

        size_t i;

        for (i = 0; i < alen; ++i)
            shape->args.shapes[i] = ((Shape **)args)[i];
    }
    return SHAPE_SUCCESS;
}

void shape_dealloc(Shape *shape)
{
    if (is_composite(shape->opc))
        free(shape->args.shapes);
    if (shape->stats != NULL)
    {
        StatUnit *s;
        while ((s = rbtree_pop(shape->stats, NULL)) != NULL)
        {
            free(s->arr);
            free(s);
        }
        rbtree_free(shape->stats);
    }
}

/**
 * Tests box location with respect to the shape.
 *
 * @param shape Shape to test.
 * @param box Box to test.
 * @param collect Collect statistics about results.
 * @param zero_surfaces The number of surfaces that was tested to be zero.
 * @return  BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
 */
int shape_test_box(Shape *shape, const Box *box, char collect, int *zero_surfaces)
{
    if (shape->last_box != 0)
    {
        int bc = box_is_in(box, shape->last_box);
        // if it is the box already tested (bc == 0) then returns cached result;
        // if it is inner box - then returns cached result only if it is not 0.
        // For inner box result may be different.

        // It is inner box and test result is not 0: -1 or +1 i.e. won't change.
        char use_cache = (bc > 0 && shape->last_box_result != BOX_CAN_INTERSECT_SHAPE);

        // If collect < 0 - it means that we try to test different
        // combinations of the remaining surfaces. In this case caching is not
        // used if we test the same box again.
        use_cache = use_cache || (bc == 0 && collect >= 0);

        if (use_cache)
            return shape->last_box_result;
    }

    int result;

    if (is_final(shape->opc))
    {
        char already = (box->subdiv == (shape->args.surface)->last_box);

        result = surface_test_box(shape->args.surface, box);

        if (shape->opc == COMPLEMENT)
            result = geom_complement(result);

        if (collect > 0 && result == 0 && !already)
            ++(*zero_surfaces);
    }
    else if (shape->opc == UNIVERSE)
    {
        result = BOX_INSIDE_SHAPE;
    }
    else if (shape->opc == EMPTY)
    {
        result = BOX_OUTSIDE_SHAPE;
    }
    else
    {
        char *sub = malloc(shape->alen * sizeof(char));

        for (int i = 0; i < shape->alen; ++i)
        {
            sub[i] = shape_test_box((shape->args.shapes)[i], box, collect, zero_surfaces);
        }

        if (shape->opc == INTERSECTION)
        {
            result = geom_intersection(sub, shape->alen, 1);
        }
        else
        {
            result = geom_union(sub, shape->alen, 1);
        }

        // TODO: Review statistics collection
        if (collect != 0 && result != 0)
        {
            StatUnit *stat = (StatUnit *)malloc(sizeof(StatUnit));
            stat->arr = sub;
            stat->len = shape->alen;
            stat->vol = box->volume;

            if (rbtree_add(shape->stats, stat) != RBT_OK)
            {
                free(stat);
                free(sub);
            }
        }
        else
            free(sub);
    }
    // Cache test result;
    if (collect >= 0 && !(box->subdiv & HIGHEST_BIT))
    {
        shape->last_box = box->subdiv;
        shape->last_box_result = result;
    }
    return result;
}

int set_zero_surface_pointers(Shape *shape, int n, Surface **zs, uint64_t subdiv)
{
    if (is_final(shape->opc))
    {
        if (shape->args.surface->last_box == subdiv && shape->args.surface->last_box_result == 0)
        {
            char already = 0;
            for (int i = 0; i < n; ++i)
            {
                if (zs[i] == shape->args.surface)
                {
                    already = 1;
                    break;
                }
            }
            if (!already)
                zs[n++] = shape->args.surface;
        }
    }
    else if (is_composite(shape->opc))
    {
        for (int i = 0; i < shape->alen; ++i)
        {
            n = set_zero_surface_pointers(shape->args.shapes[i], n, zs, subdiv);
        }
    }
    return n;
}

// Tests box location with respect to the shape. It tries to find out
// if the box really intersects the shape with desired accuracy.
// Returns BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
int shape_ultimate_test_box(Shape *shape,   // Pointer to shape
                            const Box *box, // box
                            double min_vol, // minimal volume until which splitting process goes.
                            char collect    // Whether to collect statistics about results.
)
{
    int zero_surfaces = 0;
    int result = shape_test_box(shape, box, collect, &zero_surfaces);
    if (collect > 0 && result == BOX_CAN_INTERSECT_SHAPE)
    {
        // If collect is on and result is 0 we have the following possibilities:
        // 1. only one surface has test_box result 0. Then this surface is
        //    essential for the shape. Further volume division is unnecessary.
        // 2. minimal volume is already reached. Then remaining surfaces
        //    somehow describe the shape and they are important.
        // In those cases we test all possible test_box results of the
        // remaining surfaces and collect statistics.
        if (zero_surfaces == 1 || box->volume < min_vol)
        {
            // vary all zero surfaces that remain to be -1 and +1
            Surface **zs = (Surface **)malloc(zero_surfaces * sizeof(Surface *));
            for (int i = 0; i < zero_surfaces; ++i)
                zs[i] = NULL;

            int k = set_zero_surface_pointers(shape, 0, zs, box->subdiv);
            int n = 1 << zero_surfaces;
            for (int i = 0; i < n; ++i)
            {
                for (int j = 0; j < zero_surfaces; ++j)
                {
                    zs[j]->last_box_result = ((i >> j) & 1) * 2 - 1;
                }
                shape_test_box(shape, box, -collect, NULL);
            }
            free(zs);
            return result;
        }
    }
    if (result == BOX_CAN_INTERSECT_SHAPE && box->volume > min_vol)
    {
        Box box1, box2;
        box_split(box, &box1, &box2, BOX_SPLIT_AUTODIR, 0.5);
        int result1 = shape_ultimate_test_box(shape, &box1, min_vol, collect);
        int result2 = shape_ultimate_test_box(shape, &box2, min_vol, collect);
        if (result1 != BOX_CAN_INTERSECT_SHAPE && result2 != BOX_CAN_INTERSECT_SHAPE)
            return result1; // No matter what value (result1 or result2) is
                            // returned because they will be equal.
    }
    return result;
}

// Tests whether points belong to this shape.
// Returns status - SHAPE_SUCCESS | SHAPE_NO_MEMORY
//
int shape_test_points(const Shape *shape,   // test shape
                      size_t npts,          // the number of points
                      const double *points, // array of points - NDIM * npts
                      char *result          // Result - +1 if point belongs to shape, -1
                                            // otherwise. It must have length npts.
)
{
    int i;
    if (is_final(shape->opc))
    {
        surface_test_points(shape->args.surface, npts, points, result);
        if (shape->opc == COMPLEMENT)
            for (i = 0; i < npts; ++i)
                result[i] = geom_complement(result[i]);
    }
    else if (is_void(shape->opc))
    {
        char fill = (shape->opc == UNIVERSE) ? 1 : -1;
        for (i = 0; i < npts; ++i)
            result[i] = fill;
    }
    else
    {
        char (*op)(char *arg, size_t n, size_t inc);
        op = (shape->opc == INTERSECTION) ? geom_intersection : geom_union;

        size_t n = shape->alen;
        char *sub = malloc(n * npts * sizeof(char));
        if (sub == NULL)
            return SHAPE_NO_MEMORY;

        for (i = 0; i < n; ++i)
        {
            shape_test_points((shape->args.shapes)[i], npts, points, sub + i * npts);
        }
        for (i = 0; i < npts; ++i)
            result[i] = op(sub + i, n * npts, npts);
        free(sub);
    }
    return SHAPE_SUCCESS;
}

/**
    Compute a bounding box, that bounds the shape.

    @param shape    Shape to de bound
    @param box INOUT: Start box. It is modified to obtain bounding box.
    @param tol Absolute tolerance. When change of box dimensions become smaller
                than tol the process of box reduction finishes.

    @return SHAPE_SUCCESS (always)
 */
int shape_bounding_box(const Shape *shape, Box *box, double tol)
{
    double lower, upper, ratio;
    int dim, tl;
    double min_vol = tol * tol * tol;
    Box box1, box2;
    for (dim = 0; dim < NDIM; ++dim)
    {
        lower = 0;
        while (box->dims[dim] - lower > tol)
        {
            ratio = 0.5 * (lower + box->dims[dim]) / box->dims[dim];
            box_split(box, &box1, &box2, dim, ratio);
            shape_reset_cache(shape);
            tl = shape_ultimate_test_box(shape, &box2, min_vol, 0);
            if (tl == -1)
                box_copy(box, &box1);
            else
                lower = box1.dims[dim];
        }
        upper = 0;
        while (box->dims[dim] - upper > tol)
        {
            ratio = 0.5 * (box->dims[dim] - upper) / box->dims[dim];
            box_split(box, &box1, &box2, dim, ratio);
            shape_reset_cache(shape);
            tl = shape_ultimate_test_box(shape, &box1, min_vol, 0);
            if (tl == -1)
                box_copy(box, &box2);
            else
                upper = box2.dims[dim];
        }
    }
    box->subdiv = 1;
    return SHAPE_SUCCESS;
}

/**
 Compute volume of a shape.

 @param shape a Shape to compute volume for
 @param box Box from which the process of volume finding starts
 @param min_vol Minimum volume - when volume of the box become smaller than
 min_vol the process of box splitting finishes.
 @return computed volume
 */
double shape_volume(const Shape *shape, const Box *box, double min_vol)
{
    int result = shape_test_box(shape, box, 0, NULL);

    if (result == BOX_INSIDE_SHAPE)
        return box->volume; // Box totally belongs to the shape

    if (result == BOX_OUTSIDE_SHAPE)
        return 0; // Box don't belong to the shape

    if (box->volume > min_vol)
    { // Shape intersects the box
        Box box1, box2;
        box_split(box, &box1, &box2, BOX_SPLIT_AUTODIR, 0.5);
        double vol1 = shape_volume(shape, &box1, min_vol);
        double vol2 = shape_volume(shape, &box2, min_vol);
        return vol1 + vol2;
    }
    else
    {                             // Minimum volume has been reached, but shape still intersects box
        return 0.5 * box->volume; // This is statistical decision. On average a
                                  // half of the box belongs to the shape.
    }
}

/**
 Resets cache of shape and all objects involved.

 @param shape a Shape to reset cache members in: last_box in a surface or
 underlying shapes
 */
void shape_reset_cache(Shape *shape)
{
    shape->last_box = 0;
    if (is_final(shape->opc))
    {
        shape->args.surface->last_box = 0;
    }
    else if (is_composite(shape->opc))
    {
        for (int i = 0; i < shape->alen; ++i)
        {
            shape_reset_cache((shape->args.shapes)[i]);
        }
    }
}

/**
 * Resets collected statistics or initializes statistics storage.
 *
 * @param shape a Shape to reset statistics members: stats and last_box.
 */
void shape_reset_stat(Shape *shape)
{
    StatUnit *s;
    while ((s = rbtree_pop(shape->stats, NULL)) != NULL)
    {
        free(s->arr);
        free(s);
    }
    shape->last_box = 0;
    if (is_composite(shape->opc) && shape->args.shapes != NULL)
    {
        for (int i = 0; i < shape->alen; ++i)
        {
            if (shape->args.shapes[i] != NULL)
                shape_reset_stat(shape->args.shapes[i]);
        }
    }
}

// Gets shape's contour.Returns the number of points in the contour.
size_t shape_contour(const Shape *shape, // Shape
                     const Box *box,     // Box, where contour is needed.
                     double min_vol,     // Size of volume to be considered as point
                     double *buffer      // Buffer, where points are put.
)
{
    int result = shape_test_box(shape, box, 0, NULL);
    if (result == BOX_INSIDE_SHAPE || result == BOX_OUTSIDE_SHAPE)
        return 0;
    if (box->volume > min_vol)
    {
        Box box1, box2;
        box_split(box, &box1, &box2, BOX_SPLIT_AUTODIR, 0.5);
        int n1 = shape_contour(shape, &box1, min_vol, buffer);
        int n2 = shape_contour(shape, &box2, min_vol, buffer + n1 * NDIM);
        return n1 + n2;
    }
    else
    {
        for (int i = 0; i < NDIM; ++i)
            *(buffer + i) = box->center[i];
        return 1;
    }
}

// Collects statistics about shape.
void shape_collect_statistics(Shape *shape,   // Shape
                              const Box *box, // Global box, where statistics is collected
                              double min_vol  // minimal volume, when splitting process stops.
)
{
    shape_reset_stat(shape);
    shape_ultimate_test_box(shape, box, min_vol, 1);
}

// Gets statistics table
char *shape_get_stat_table(Shape *shape,  // Shape
                           size_t *nrows, // number of rows
                           size_t *ncols  // number of columns
)
{
    *nrows = shape->stats->len;
    *ncols = shape->alen;
    char *table = malloc(*ncols * *nrows * sizeof(char));
    StatUnit **statarr = rbtree_to_array(shape->stats);
    size_t i, j;
    for (i = 0; i < *nrows; ++i)
        for (j = 0; j < *ncols; ++j)
            *(table + i * (*ncols) + j) = statarr[i]->arr[j];
    free(statarr);
    return table;
}

// Operation functions

char geom_intersection(char *args, size_t n, size_t inc)
{
    size_t i;
    char result = +1;
    for (i = 0; i < n; i += inc)
    {
        if (*(args + i) == 0)
            result = 0;
        else if (*(args + i) == -1)
        {
            result = -1;
            break;
        }
    }
    return result;
}

char geom_union(char *args, size_t n, size_t inc)
{
    size_t i;
    char result = -1;
    for (i = 0; i < n; i += inc)
    {
        if (*(args + i) == 0)
            result = 0;
        else if (*(args + i) == +1)
        {
            result = +1;
            break;
        }
    }
    return result;
}
