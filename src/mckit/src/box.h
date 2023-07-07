#ifndef __BOX_H
#define __BOX_H

#include <stdint.h>
#include "common.h"

#define BOX_SUCCESS  0
#define BOX_FAILURE -1

#define BOX_SPLIT_X 0
#define BOX_SPLIT_Y 1
#define BOX_SPLIT_Z 2
#define BOX_SPLIT_AUTODIR -1

#define BIT_LEN 64
#define HIGHEST_BIT (1ull << (BIT_LEN - 1))

#include "mkl_vsl.h"


typedef struct Box Box;

struct Box {
    double center[NDIM];    // center of the box
    double ex[NDIM];        //
    double ey[NDIM];        // basis vectors. Shows directions of box's edges
    double ez[NDIM];        //
    double dims[NDIM];      // Dimensions of the box.
    double lb[NDIM];        // lower bounds
    double ub[NDIM];        // upper bounds
    double corners[NCOR * NDIM];  // corners
    double volume;
    uint64_t subdiv;        // Box location. The most outer (parent) box
    VSLStreamStatePtr rng;  // Random generator. Allocated when it is needed.
};

extern char enable_box_cache;

// Initializes box structure.
int box_init(
    Box * box,              // Pointer to box structure being initialized
    const double * center,  // Center of the box
    const double * ex,      //
    const double * ey,      // Directions of box's edges
    const double * ez,      //
    double xdim,            //
    double ydim,            // Dimensions of the box
    double zdim             //
);

// Deallocates memory created for box's random generator if necessary.
void box_dispose(Box * box);

// Copies content of src box to the dst box.
void box_copy(Box * dst, const Box * src);

// Generates random points inside the box.
int box_generate_random_points(
    Box * box,          // Box
    size_t npts,        // IN: the number of points to be generated
    double * points     // OUT: generated points
);

// Checks if points lie inside the box.
void box_test_points(
    const Box * box,        // Box
    size_t npts,            // the number of points
    const double * points,  // Points to be checked
    int * result            // array of results: 1 point lies inside the box; 0 - otherwise.
);

// Splits box into two parts.
int box_split(
    const Box * box,    // Box to be split
    Box * box1,         // First part box - with smaller coordinates.
    Box * box2,         // Second part box - with greater coordinates.
    int dir,            // Direction along which the box must be split. BOX_SPLIT_X, BOX_SPLIT_Y, BOX_SPLIT_Z,
                        // BOX_SPLIT_AUTODIR - split along dimension with maximal length.
    double ratio        // Ratio of splitting along splitting direction. 0 < ratio < 1.
);

// Boundary conditions for surface test_box methods.
void box_ieqcons(
    unsigned int m,     // The number of constraints - must be 6.
    double * result,    //
    unsigned int n,     // The number of dimensions - must be NDIM.
    const double * x,   // Point to be tested
    double * grad,      // Gradient of constraint function - only if not NULL.
    void * f_data       // Box structure
);

// Checks if the box intersects with another one.
int box_check_intersection(
    const Box * box1,
    const Box * box2
);

/**
 * Compare two boxes.
 *
 * subdiv denotes subdivision. It is 64 bit integer value. The elder bit marks the number of subdivision generations.
 * 0 means first half of the box, 1 - second half.
 *
 *
 * @param in_box
 * @param out_subdiv the code of subdivisions of outer box. The box struct itself is not used because
 *                   box itself may not exist when check is needed (because of cache purposes).
 *
 * @return     +1 if in_box lies actually inside the out_box;
 *              0 if in_box equals out_box;
 *             -1 if in_box lies outside of the out_box;
 *
 */
int box_is_in(const Box * in_box, uint64_t out_subdiv);

#endif
