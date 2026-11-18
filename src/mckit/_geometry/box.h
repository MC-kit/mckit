#ifndef MCKIT_BOX_H
#define MCKIT_BOX_H

#include <array>
#include <span>
#include <stdint.h>
#include <stdlib.h>
#include <utility>

#include "common.h"

#define BOX_SPLIT_X 0
#define BOX_SPLIT_Y 1
#define BOX_SPLIT_Z 2
#define BOX_SPLIT_AUTODIR (-1)

#define BIT_LEN 64
#define HIGHEST_BIT (1ull << BIT_LEN - 1)

typedef struct Box Box;

struct Box
{
    std::array<double, NDIM> center;                    /// center of the box
    std::array<double, NDIM> ex;                        ///
    std::array<double, NDIM> ey;                        /// basis vectors. Shows directions of box's edges
    std::array<double, NDIM> ez;                        ///
    std::array<double, NDIM> dims;                      /// Dimensions of the box.
    std::array<double, NDIM> lb;                        /// lower bounds
    std::array<double, NDIM> ub;                        /// upper bounds
    std::array<std::array<double, NDIM>, NCOR> corners; /// corners
    double volume;                                      /// volume
    uint64_t subdiv;                                    /// Box location. The most outer (parent) box

    /// Creates a box from its center, basis vectors and edge lengths.
    Box(std::span<const double, NDIM> center, /// Center of the box
        std::span<const double, NDIM> ex,     ///
        std::span<const double, NDIM> ey,     /// Directions of box's edges
        std::span<const double, NDIM> ez,     ///
        double xdim,                          ///
        double ydim,                          /// Dimensions of the box
        double zdim                           ///
    );

    /// Generates random points inside the box.
    void generate_random_points(size_t npts,   ///< IN: the number of points to be generated
                                double *points ///< OUT: generated points
    ) const;

    /// Checks if points lie inside the box.
    ///
    /// @param npts the number of points
    /// @param points Points to be checked
    /// @param result array of results: 1 point lies inside the box; 0 - otherwise.
    void test_points(size_t npts, const double *points, int *result) const;

    /// Splits the box into two parts.
    ///
    /// @param dir Direction along which the box must be split (BOX_SPLIT_X, BOX_SPLIT_Y, BOX_SPLIT_Z,
    ///            BOX_SPLIT_AUTODIR - split along the dimension with maximal length).
    /// @param ratio Ratio of splitting along splitting direction. 0 < ratio < 1.
    std::pair<Box, Box> split(int dir, double ratio) const;

    /// Compares this box position with the one denoted by a subdivision code.
    ///
    /// subdiv denotes subdivision. It is 64 bit integer value. The elder bit marks the number of
    /// subdivision generations. 0 means first half of the box, 1 - second half. Only the code is
    /// used because the outer box itself may not exist when the check is needed (cache purposes).
    ///
    /// @param out_subdiv the code of subdivisions of outer box.
    ///
    /// @return     +1 if this box lies actually inside the out_box;
    ///              0 if this box equals out_box;
    ///             -1 if this box lies outside of the out_box;
    int is_in(uint64_t out_subdiv) const;
};

/**
 * Boundary conditions for surface test_box methods.
 *
 * @param m The number of constraints - must be 6.
 * @param result
 * @param n The number of dimensions - must be NDIM.
 * @param x Point to be tested
 * @param grad Gradient of constraint function - only if not NULL.
 * @param f_data Box structure
 *x
 * The function is passed as a callback to the C NLopt library,
 * so it must have C linkage.
 */
extern "C" void box_ieqcons(unsigned int m, double *result, unsigned int n, const double *x, double *grad,
                            void *f_data);

/**
 * Checks if the box intersects with another one.
 *
 * @param box1
 * @param box2
 * @return
 */
int box_check_intersection(const Box *box1, const Box *box2);

#endif
