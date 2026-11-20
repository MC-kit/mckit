//
// Created by Roma on 14.04.2018.
//

#ifndef MCKIT_SHAPE_H
#define MCKIT_SHAPE_H

#include <cstdint>
#include <memory>
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

/// Converts a one-letter operation code to the Operation enum value.
///
/// @return Operation value or -1 for an unknown code.
int opc_from_char(char opc);

/// Converts an Operation enum value to its one-letter code.
const char *opc_name(int opc);

/// Base class of the shape hierarchy.
///
/// Shapes are immutable: the factory below creates the proper subclass for the
/// requested operation. Child shapes and surfaces are not owned by the shape;
/// the Python wrappers keep them alive.
struct Shape
{
    Shape(const Shape &) = delete;
    Shape &operator=(const Shape &) = delete;

    virtual ~Shape() = default;

    int opc() const
    {
        return opc_;
    }

    /// The number of arguments.
    virtual size_t alen() const
    {
        return 0;
    }

    /// The child shape at the given position or nullptr.
    virtual const Shape *child(size_t /*index*/) const
    {
        return nullptr;
    }

    /// The surface of a final shape or nullptr.
    virtual Surface *surface() const
    {
        return nullptr;
    }

    /// Tests box location with respect to the shape.
    ///
    /// @return BOX_INSIDE_SHAPE | BOX_CAN_INTERSECT_SHAPE | BOX_OUTSIDE_SHAPE
    int test_box(const Box &box, char collect = 0, int *zero_surfaces = nullptr);

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

    /// Collects pointers to surfaces, which were tested at the given subdivision.
    ///
    /// This is an internal algorithm hook of the composite shape, hence it must
    /// be reachable through a `Shape *` (see C++ protected access rules).
    virtual int set_zero_surface_pointers(int n, Surface **zs, uint64_t subdiv) const
    {
        return n;
    }

  protected:
    explicit Shape(int opc) : opc_(opc)
    {
    }

    /// Tests the box without shape-level caching.
    virtual int do_test_box(const Box &box, char collect, int *zero_surfaces) = 0;

    /// Tests points without shape-level dispatch.
    virtual void do_test_points(size_t npts, const double *points, char *result) const = 0;

    /// Resets the cache of the child objects only.
    virtual void do_reset_cache() = 0;

    /// Resets the statistics of the child objects only.
    virtual void do_reset_stat()
    {
    }

    /// Statistics storage or nullptr when the shape does not collect it.
    virtual const StatsMap *stats() const
    {
        return nullptr;
    }

    int opc_;                 ///< Code of operation applied to arguments (see enum Operation)
    uint64_t last_box_ = 0;   ///< Subdivision code of last tested box
    int last_box_result_ = 0; ///< Result of last test_box call.
};

/// An identity or complement shape over a single surface.
struct FinalShape final : Shape
{
    FinalShape(int opc, Surface *surface);

    size_t alen() const override
    {
        return 1;
    }

    Surface *surface() const override
    {
        return surf;
    }

  protected:
    int do_test_box(const Box &box, char collect, int *zero_surfaces) override;
    void do_test_points(size_t npts, const double *points, char *result) const override;
    void do_reset_cache() override;
    int set_zero_surface_pointers(int n, Surface **zs, uint64_t subdiv) const override;

  public:
    Surface *surf;
};

/// An empty or universe shape.
struct VoidShape final : Shape
{
    explicit VoidShape(int opc);

  protected:
    int do_test_box(const Box &box, char collect, int *zero_surfaces) override;
    void do_test_points(size_t npts, const double *points, char *result) const override;
    void do_reset_cache() override
    {
    }
};

/// A union or intersection of child shapes.
struct CompositeShape final : Shape
{
    CompositeShape(int opc, std::span<Shape *const> args);

    size_t alen() const override
    {
        return args.size();
    }

    const Shape *child(size_t index) const override
    {
        return args[index];
    }

  protected:
    int do_test_box(const Box &box, char collect, int *zero_surfaces) override;
    void do_test_points(size_t npts, const double *points, char *result) const override;
    void do_reset_cache() override;
    void do_reset_stat() override;
    int set_zero_surface_pointers(int n, Surface **zs, uint64_t subdiv) const override;
    const StatsMap *stats() const override
    {
        return &stat_entries;
    }

  public:
    std::vector<Shape *> args;
    StatsMap stat_entries;
};

/// Factory: creates the proper Shape subclass for the requested operation.
///
/// The operation and argument combination is validated here, so callers get a
/// ValueError for invalid combinations regardless of the entry point.
std::unique_ptr<Shape> make_shape(int opc, Surface *surface);
std::unique_ptr<Shape> make_shape(int opc, std::span<Shape *const> args);
std::unique_ptr<Shape> make_shape(int opc);

#endif // MCKIT_SHAPE_H
