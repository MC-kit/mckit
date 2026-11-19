//
// Created by Roma on 14.04.2018.
//

#ifndef MCKIT_SHAPE_H
#define MCKIT_SHAPE_H

#include <span>
#include <stddef.h>
#include <vector>

#include "box.h"
#include "stats.h"
#include "surface.h"

constexpr int BOX_INSIDE_SHAPE = +1;
constexpr int BOX_CAN_INTERSECT_SHAPE = 0;
constexpr int BOX_OUTSIDE_SHAPE = -1;

constexpr int invert_opc(int opc)
{
    return (opc + 3) % 6;
}

enum Operation
{
    INTERSECTION = 0,
    COMPLEMENT,
    EMPTY,
    UNION,
    IDENTITY,
    UNIVERSE
};

/// Describes a shape.
///
/// Contains operation code, number of children, pointer to a Surface or child
/// Shapes
struct Shape
{
    /// Creates a final shape (complement or identity) over the given surface.
    Shape(char opc, Surface *surface);

    /// Creates a void shape (empty or universe) without arguments.
    explicit Shape(char opc);

    /// Creates a composite shape (union or intersection) over the given shapes.
    Shape(char opc, std::span<Shape *> shapes);

    ~Shape();

    /// Tests box location with respect to the shape.
    ///
    /// @return BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
    int test_box(const Box &box, char collect, int *zero_surfaces);

    /// Tests box location with respect to a Shape.
    ///
    /// It tries to find out if the box really intersects the shape with desired
    /// accuracy.
    ///
    /// @return BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
    int ultimate_test_box(const Box &box, double min_vol, char collect);

    /// Tests whether points belong to this shape.
    void test_points(size_t npts, const double *points, char *result) const;

    /// Gets bounding box, that bounds the shape.
    ///
    /// @param box INOUT: Start box. It is modified to obtain bounding box.
    /// @param tol Absolute tolerance. When change of box dimensions become
    ///            smaller than tol the process of box reduction finishes.
    void bounding_box(Box &box, double tol);

    /// Gets volume of the shape.
    ///
    /// @param box Box from which the process of volume finding starts.
    /// @param min_vol Minimum volume - when volume of the box become smaller
    ///                than min_vol the process of box splitting finishes.
    double volume(const Box &box, double min_vol);

    /// Gets shape's contour.
    ///
    /// @param box Box, where contour is needed.
    /// @param min_vol Size of volume to be considered as point.
    /// @param buffer Buffer, where points are put.
    size_t contour(const Box &box, double min_vol, double *buffer);

    /// Resets collected statistics.
    void reset_stat();

    /// Resets cache of shape and all objects involved.
    void reset_cache();

    /// Collects statistics about shapes.
    ///
    /// @param box Global box, where statistics is collected.
    /// @param min_vol minimal volume, when splitting process stops.
    void collect_statistics(const Box &box, double min_vol);

    /// Gets statistics table as a row-major char matrix
    /// with `nrows` rows and `ncols` columns.
    std::vector<char> get_stat_table(size_t &nrows, size_t &ncols) const;

    char opc;    ///< Code of operation applied to arguments (see enum Operation)
    size_t alen; ///< Length of arguments
    union {
        Surface *surface;
        Shape **shapes;
    } args;              ///< Pointer to arguments. It can be either Shape or Surface
                         ///< structures
    uint64_t last_box;   ///< Subdivision code of last tested box
    int last_box_result; ///< Result of last test_box call.
    StatsMap *stats;     ///< Statistics about argument results.

  private:
    /// Collects pointers to surfaces, which were tested at the given subdivision.
    int set_zero_surface_pointers(int n, Surface **zs, uint64_t subdiv) const;
};

#endif // MCKIT_SHAPE_H
