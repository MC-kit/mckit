//
// Created by Roma on 14.04.2018.
//

#include "shape.h"
#include "surface.h"
#include <algorithm>
#include <memory>
#include <vector>

namespace
{
bool is_final(char opc)
{
    return opc == COMPLEMENT || opc == IDENTITY;
}

bool is_void(char opc)
{
    return opc == EMPTY || opc == UNIVERSE;
}

bool is_composite(char opc)
{
    return opc == UNION || opc == INTERSECTION;
}

/// Applies the AND operation to strided result codes.
char geom_intersection(const char *args, size_t n, size_t inc)
{
    char result = +1;
    for (size_t i = 0; i < n; i += inc)
    {
        if (args[i] == 0)
            result = 0;
        else if (args[i] == -1)
            return -1;
    }
    return result;
}

/// Applies the OR operation to strided result codes.
char geom_union(const char *args, size_t n, size_t inc)
{
    char result = -1;
    for (size_t i = 0; i < n; i += inc)
    {
        if (args[i] == 0)
            result = 0;
        else if (args[i] == +1)
            return +1;
    }
    return result;
}
} // namespace

/**
  Creates a final shape over a surface.

  @param opc   Operation code (complement or identity)
  @param surface Surface to apply the operation to
 */
Shape::Shape(char opc, Surface *surface)
    : opc(opc), alen(1), args{}, last_box(0), last_box_result(0), stats(new StatsMap())
{
    args.surface = surface;
}

/**
  Creates a void shape.

  @param opc   Operation code (empty or universe)
 */
Shape::Shape(char opc) : opc(opc), alen(0), args{}, last_box(0), last_box_result(0), stats(new StatsMap())
{
    args.surface = nullptr;
}

/**
  Creates a composite shape.

  @param opc    Operation code (union or intersection)
  @param shapes Shapes to combine
 */
Shape::Shape(char opc, std::span<Shape *> shapes)
    : opc(opc), alen(shapes.size()), args{}, last_box(0), last_box_result(0), stats(nullptr)
{
    std::unique_ptr<StatsMap> stats_holder(new StatsMap());
    args.shapes = new Shape *[alen];
    std::copy(shapes.begin(), shapes.end(), args.shapes);
    stats = stats_holder.release();
}

Shape::~Shape()
{
    if (is_composite(opc))
        delete[] args.shapes;
    delete stats;
    stats = nullptr;
}

/**
 * Tests box location with respect to the shape.
 *
 * @param box Box to test.
 * @param collect Collect statistics about results.
 * @param zero_surfaces The number of surfaces that was tested to be zero.
 * @return  BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
 */
int Shape::test_box(const Box &box, char collect, int *zero_surfaces)
{
    if (last_box != 0)
    {
        int bc = box.is_in(last_box);
        // if it is the box already tested (bc == 0) then returns cached result;
        // if it is inner box - then returns cached result only if it is not 0.
        // For inner box result may be different.

        // It is inner box and test result is not 0: -1 or +1 i.e. won't change.
        char use_cache = (bc > 0 && last_box_result != BOX_CAN_INTERSECT_SHAPE);

        // If collect < 0 - it means that we try to test different
        // combinations of the remaining surfaces. In this case caching is not
        // used if we test the same box again.
        use_cache = use_cache || (bc == 0 && collect >= 0);

        if (use_cache)
            return last_box_result;
    }

    int result;

    if (is_final(opc))
    {
        char already = (box.subdiv == args.surface->last_box);

        result = surface_test_box(args.surface, &box);

        if (opc == COMPLEMENT)
            result = -result;

        if (collect > 0 && result == 0 && !already)
            ++(*zero_surfaces);
    }
    else if (opc == UNIVERSE)
    {
        result = BOX_INSIDE_SHAPE;
    }
    else if (opc == EMPTY)
    {
        result = BOX_OUTSIDE_SHAPE;
    }
    else
    {
        std::vector<char> sub(alen);

        for (size_t i = 0; i < alen; ++i)
        {
            sub[i] = args.shapes[i]->test_box(box, collect, zero_surfaces);
        }

        if (opc == INTERSECTION)
        {
            result = geom_intersection(sub.data(), alen, 1);
        }
        else
        {
            result = geom_union(sub.data(), alen, 1);
        }

        // TODO: Review statistics collection
        if (collect != 0 && result != 0)
        {
            // On a duplicate key the first recorded volume is kept -
            // the new entry is discarded, as the former rbtree did.
            stats->entries.emplace(sub, box.volume);
        }
    }
    // Cache test result;
    if (collect >= 0 && !(box.subdiv & HIGHEST_BIT))
    {
        last_box = box.subdiv;
        last_box_result = result;
    }
    return result;
}

int Shape::set_zero_surface_pointers(int n, Surface **zs, uint64_t subdiv) const
{
    if (is_final(opc))
    {
        if (args.surface->last_box == subdiv && args.surface->last_box_result == 0)
        {
            bool already = false;
            for (int i = 0; i < n; ++i)
            {
                if (zs[i] == args.surface)
                {
                    already = true;
                    break;
                }
            }
            if (!already)
                zs[n++] = args.surface;
        }
    }
    else if (is_composite(opc))
    {
        for (size_t i = 0; i < alen; ++i)
        {
            n = args.shapes[i]->set_zero_surface_pointers(n, zs, subdiv);
        }
    }
    return n;
}

// Tests box location with respect to the shape. It tries to find out
// if the box really intersects the shape with desired accuracy.
// Returns BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
int Shape::ultimate_test_box(const Box &box, double min_vol, char collect)
{
    int zero_surfaces = 0;
    int result = test_box(box, collect, &zero_surfaces);
    if (collect > 0 && result == BOX_CAN_INTERSECT_SHAPE)
    {
        // If collect is on and result is 0 we have the following possibilities:
        // 1. only one surface has test_box result 0. Then this surface is
        //    essential for the shape. Further volume division is unnecessary.
        // 2. minimal volume is already reached. Then remaining surfaces
        //    somehow describe the shape and they are important.
        // In those cases we test all possible test_box results of the
        // remaining surfaces and collect statistics.
        if (zero_surfaces == 1 || box.volume < min_vol)
        {
            // vary all zero surfaces that remain to be -1 and +1
            std::vector<Surface *> zs(zero_surfaces, nullptr);

            set_zero_surface_pointers(0, zs.data(), box.subdiv);
            int n = 1 << zero_surfaces;
            for (int i = 0; i < n; ++i)
            {
                for (int j = 0; j < zero_surfaces; ++j)
                {
                    zs[j]->last_box_result = ((i >> j) & 1) * 2 - 1;
                }
                test_box(box, -collect, nullptr);
            }
            return result;
        }
    }
    if (result == BOX_CAN_INTERSECT_SHAPE && box.volume > min_vol)
    {
        auto [box1, box2] = box.split(BOX_SPLIT_AUTODIR, 0.5);
        int result1 = ultimate_test_box(box1, min_vol, collect);
        int result2 = ultimate_test_box(box2, min_vol, collect);
        if (result1 != BOX_CAN_INTERSECT_SHAPE && result2 != BOX_CAN_INTERSECT_SHAPE)
            return result1; // No matter what value (result1 or result2) is
                            // returned because they will be equal.
    }
    return result;
}

// Tests whether points belong to this shape.
void Shape::test_points(size_t npts, const double *points, char *result) const
{
    if (is_final(opc))
    {
        surface_test_points(args.surface, npts, points, result);
        if (opc == COMPLEMENT)
            for (size_t i = 0; i < npts; ++i)
                result[i] = -result[i];
    }
    else if (is_void(opc))
    {
        std::fill(result, result + npts, static_cast<char>(opc == UNIVERSE ? 1 : -1));
    }
    else
    {
        const size_t n = alen;
        std::vector<char> sub(n * npts);

        for (size_t i = 0; i < n; ++i)
        {
            args.shapes[i]->test_points(npts, points, sub.data() + i * npts);
        }

        char (*op)(const char *arg, size_t n, size_t inc) = opc == INTERSECTION ? geom_intersection : geom_union;
        for (size_t i = 0; i < npts; ++i)
            result[i] = op(sub.data() + i, n * npts, npts);
    }
}

/**
    Compute a bounding box, that bounds the shape.

    @param box INOUT: Start box. It is modified to obtain bounding box.
    @param tol Absolute tolerance. When change of box dimensions become smaller
                than tol the process of box reduction finishes.
 */
void Shape::bounding_box(Box &box, double tol)
{
    const double min_vol = tol * tol * tol;
    for (int dim = 0; dim < NDIM; ++dim)
    {
        double lower = 0;
        while (box.dims[dim] - lower > tol)
        {
            const double ratio = 0.5 * (lower + box.dims[dim]) / box.dims[dim];
            auto [box1, box2] = box.split(dim, ratio);
            reset_cache();
            const int tl = ultimate_test_box(box2, min_vol, 0);
            if (tl == -1)
                box = box1;
            else
                lower = box1.dims[dim];
        }
        double upper = 0;
        while (box.dims[dim] - upper > tol)
        {
            const double ratio = 0.5 * (box.dims[dim] - upper) / box.dims[dim];
            auto [box1, box2] = box.split(dim, ratio);
            reset_cache();
            const int tl = ultimate_test_box(box1, min_vol, 0);
            if (tl == -1)
                box = box2;
            else
                upper = box2.dims[dim];
        }
    }
    box.subdiv = 1;
}

/**
 Compute volume of a shape.

 @param box Box from which the process of volume finding starts
 @param min_vol Minimum volume - when volume of the box become smaller than
 min_vol the process of box splitting finishes.
 @return computed volume
 */
double Shape::volume(const Box &box, double min_vol)
{
    int result = test_box(box, 0, nullptr);

    if (result == BOX_INSIDE_SHAPE)
        return box.volume; // Box totally belongs to the shape

    if (result == BOX_OUTSIDE_SHAPE)
        return 0; // Box don't belong to the shape

    if (box.volume > min_vol)
    { // Shape intersects the box
        auto [box1, box2] = box.split(BOX_SPLIT_AUTODIR, 0.5);
        return volume(box1, min_vol) + volume(box2, min_vol);
    }
    // Minimum volume has been reached, but shape still intersects box.
    // This is statistical decision: on average a half of the box belongs to the shape.
    return 0.5 * box.volume;
}

/**
 Resets cache of shape and all objects involved: last_box in a surface or
 underlying shapes.
 */
void Shape::reset_cache()
{
    last_box = 0;
    if (is_final(opc))
    {
        args.surface->last_box = 0;
    }
    else if (is_composite(opc))
    {
        for (size_t i = 0; i < alen; ++i)
        {
            args.shapes[i]->reset_cache();
        }
    }
}

/**
 * Resets collected statistics or initializes statistics storage.
 */
void Shape::reset_stat()
{
    if (stats != nullptr)
        stats->entries.clear();
    last_box = 0;
    if (is_composite(opc) && args.shapes != nullptr)
    {
        for (size_t i = 0; i < alen; ++i)
        {
            if (args.shapes[i] != nullptr)
                args.shapes[i]->reset_stat();
        }
    }
}

// Gets shape's contour. Returns the number of points in the contour.
size_t Shape::contour(const Box &box, double min_vol, double *buffer)
{
    int result = test_box(box, 0, nullptr);
    if (result == BOX_INSIDE_SHAPE || result == BOX_OUTSIDE_SHAPE)
        return 0;
    if (box.volume > min_vol)
    {
        auto [box1, box2] = box.split(BOX_SPLIT_AUTODIR, 0.5);
        const size_t n1 = contour(box1, min_vol, buffer);
        const size_t n2 = contour(box2, min_vol, buffer + n1 * NDIM);
        return n1 + n2;
    }
    for (int i = 0; i < NDIM; ++i)
        buffer[i] = box.center[i];
    return 1;
}

// Collects statistics about shape.
void Shape::collect_statistics(const Box &box, double min_vol)
{
    reset_stat();
    ultimate_test_box(box, min_vol, 1);
}

// Gets statistics table
std::vector<char> Shape::get_stat_table(size_t &nrows, size_t &ncols) const
{
    nrows = stats->entries.size();
    ncols = alen;
    std::vector<char> table(nrows * ncols, '\0');
    size_t i = 0;
    for (const auto &entry : stats->entries)
    {
        const std::vector<char> &key = entry.first;
        for (size_t j = 0; j < ncols; ++j)
            table[i * ncols + j] = key[j];
        ++i;
    }
    return table;
}
