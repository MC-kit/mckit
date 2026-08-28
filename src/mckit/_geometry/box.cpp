#include "box.h"
#include <nlopt.h>

#include "rand.h"
#include "vecops.h"

/* Each row is delta to be added to center point to obtain specific corner.
 * They must be multiplied by corresponding box's dimensions.
 */
static constexpr std::array<std::array<double, NDIM>, NCOR> perm = {{{-1, -1, -1}, {-1, -1, 1}, {-1, 1, -1}, {-1, 1, 1},
                                                                     {1, -1, -1},  {1, -1, 1},  {1, 1, -1},  {1, 1, 1}}};

// Finds the highest set bit.
static inline char high_bit(uint64_t value)
{
    char result = 0;
    while (value != 0)
    {
        value >>= 1;
        ++result;
    }
    return result;
}

int box_init(Box *box, const double *center, const double *ex, const double *ey, const double *ez, double xdim,
             double ydim, double zdim)
{
    if (!box || !center || !ex || !ey || !ez)
    {
        return BOX_FAILURE;
    }

    int i;
    for (i = 0; i < NDIM; ++i)
        box->center[i] = center[i];

    box->dims[0] = xdim;
    box->dims[1] = ydim;
    box->dims[2] = zdim;

    box->volume = xdim * ydim * zdim;

    // basis vectors.
    for (i = 0; i < NDIM; ++i)
    {
        box->ex[i] = ex[i];
        box->ey[i] = ey[i];
        box->ez[i] = ez[i];
    }

    // Finding coordinates of box's corners
    for (i = 0; i < NCOR; ++i)
    {
        // @dvp: analysis of the algorithm
        // daxpy( N, alpha, x, strideX, y, strideY )
        // y += a*x
        // Let's define
        // w - half widths vector
        // A = [[ex], [ey], [ez]] - matrix with columns ex, ey, ez (rotation)
        // .  - dot multiplication
        // .* - element wise multiplication
        // then
        // corner[i] =  A . (perm[i] .* w) + center
        std::span corner_row = box->corners[i];
        vec_copy(box->center, corner_row);
        vec_axpy(0.5 * perm[i][0] * box->dims[0], box->ex, corner_row);
        vec_axpy(0.5 * perm[i][1] * box->dims[1], box->ey, corner_row);
        vec_axpy(0.5 * perm[i][2] * box->dims[2], box->ez, corner_row);
    }

    // Finding lower and upper bounds
    vec_copy(box->corners[0], box->lb);
    vec_copy(box->corners[0], box->ub);
    for (int i = 1; i < NCOR; ++i)
    {
        for (int j = 0; j < NDIM; ++j)
        {
            if (box->corners[i][j] < box->lb[j])
                box->lb[j] = box->corners[i][j];
            if (box->corners[i][j] > box->ub[j])
                box->ub[j] = box->corners[i][j];
        }
    }

    box->subdiv = 1; // Means that it is the most outer box for now.

    return BOX_SUCCESS;
}

void box_copy(Box *dst, const Box *src)
{
    box_init(dst, src->center.data(), src->ex.data(), src->ey.data(), src->ez.data(), src->dims[0], src->dims[1],
             src->dims[2]);
    dst->subdiv = src->subdiv;
}

void box_generate_random_points(const Box *box, size_t npts, double *points)
{
    Xoshiro256ss &rng = thread_local_rng();
    double d[NDIM];

    for (size_t i = 0; i < npts; ++i)
    {
        for (int j = 0; j < NDIM; ++j)
            d[j] = rng.next_double() - 0.5;

        std::span point_row(points + i * NDIM, NDIM);
        vec_copy(box->center, point_row);
        vec_axpy(d[0] * box->dims[0], box->ex, point_row);
        vec_axpy(d[1] * box->dims[1], box->ey, point_row);
        vec_axpy(d[2] * box->dims[2], box->ez, point_row);
    }
}

void box_test_points(const Box *box, size_t npts, const double *points, int *result)
{
    double delta[NDIM];
    double x, y, z;
    int i;

    for (i = 0; i < npts; ++i)
    {
        vec_copy(std::span(points + i * NDIM, NDIM), delta);
        vec_axpy(-1, box->center, delta);
        x = vec_dot(delta, box->ex) / box->dims[0];
        y = vec_dot(delta, box->ey) / box->dims[1];
        z = vec_dot(delta, box->ez) / box->dims[2];
        if (x > -0.5 && x < 0.5 && y > -0.5 && y < 0.5 && z > -0.5 && z < 0.5)
        {
            result[i] = 1;
        }
        else
        {
            result[i] = 0;
        }
    }
}

int box_split(const Box *box, Box *box1, Box *box2, int dir, double ratio)
{
    // Find splitting direction
    if (dir == BOX_SPLIT_AUTODIR)
        dir = (int)vec_argmax_abs(box->dims);

    double center1[NDIM], center2[NDIM], dims1[NDIM], dims2[NDIM];
    const std::span<const double> basis[NDIM] = {box->ex, box->ey, box->ez};

    // find new dimensions
    vec_copy(box->dims, dims1);
    vec_copy(box->dims, dims2);
    dims1[dir] *= ratio;
    dims2[dir] *= 1 - ratio;

    // find new centers.
    vec_copy(box->center, center1);
    vec_copy(box->center, center2);

    vec_axpy(-0.5 * dims2[dir], basis[dir], center1);
    vec_axpy(0.5 * dims1[dir], basis[dir], center2);

    // subdivision index.
    char hb = high_bit(box->subdiv);
    uint64_t ones = ~0;
    uint64_t mask = (ones) >> (BIT_LEN - 1) << (hb - 1);
    uint64_t start_bit = mask << 1;
    // create new boxes.
    int status;
    status = box_init(box1, center1, box->ex.data(), box->ey.data(), box->ez.data(), dims1[0], dims1[1], dims1[2]);
    if (status == BOX_FAILURE)
        return BOX_FAILURE;

    status = box_init(box2, center2, box->ex.data(), box->ey.data(), box->ez.data(), dims2[0], dims2[1], dims2[2]);
    if (status == BOX_FAILURE)
        return BOX_FAILURE;

    if (box->subdiv & HIGHEST_BIT)
    {
        box1->subdiv = box->subdiv;
        box2->subdiv = box->subdiv;
    }
    else
    {
        box1->subdiv = box->subdiv & (~mask) | start_bit;
        box2->subdiv = box->subdiv | start_bit;
    }

    return BOX_SUCCESS;
}

extern "C" void box_ieqcons(unsigned int m, double *result, unsigned int n, const double *x, double *grad, void *f_data)
{
    Box *box = (Box *)f_data;

    const std::span<const double> basis[NDIM] = {box->ex, box->ey, box->ez};
    double point[NDIM];
    int i, j, mult;

    for (i = 0; i < 6; ++i)
    {
        vec_copy(box->center, point);
        mult = 2 * (i % 2) - 1;
        j = i % 3;
        vec_axpy(mult * box->dims[j], basis[j], point);
        result[i] = mult * (vec_dot(basis[j], std::span(x, NDIM)) - vec_dot(basis[j], point));

        if (grad != nullptr)
        {
            std::span grad_row(grad + i * NDIM, NDIM);
            vec_copy(basis[j], grad_row);
            vec_scale(mult, grad_row);
        }
    }
}

static double min_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    Box *data = (Box *)f_data;
    const std::span x_span(x, NDIM);
    if (grad != nullptr)
    {
        std::span grad_span(grad, NDIM);
        vec_copy(x_span, grad_span);
        vec_axpy(-1, data->center, grad_span);
        vec_scale(2, grad_span);
    }
    double delta[NDIM];
    vec_copy(x_span, delta);
    vec_axpy(-1, data->center, delta);
    return vec_dot(delta, delta);
}

// Checks if the box intersects with another one.
int box_check_intersection(const Box *box1, const Box *box2)
{
    double x[NDIM], opt_val;
    nlopt_result opt_result;
    int result;

    nlopt_opt opt;
    opt = nlopt_create(NLOPT_LD_SLSQP, 3);
    nlopt_set_lower_bounds(opt, box1->lb.data());
    nlopt_set_upper_bounds(opt, box1->ub.data());

    nlopt_set_min_objective(opt, min_func, (void *)box2);

    nlopt_add_inequality_mconstraint(opt, 6, box_ieqcons, (void *)box1, nullptr);
    nlopt_set_stopval(opt, 0);
    nlopt_set_maxeval(opt, 1000); // TODO @rrn: consider passing this parameter.

    vec_copy(box1->center, x);
    opt_result = nlopt_optimize(opt, x, &opt_val);
    box_test_points(box2, 1, x, &result);
    nlopt_destroy(opt);
    return result;
}

int box_is_in(const Box *in_box, uint64_t out_subdiv)
{
    uint64_t out = out_subdiv;
    uint64_t in = in_box->subdiv;

    if (out == in)
        return 0;

    uint64_t mask = ~0;
    char out_stop = high_bit(out);

    mask >>= BIT_LEN + 1 - out_stop;

    if ((in & (~mask)) == 0)
        return -1; // inner box actually is bigger one.

    if (((out ^ in) & mask) == 0)
        return +1;

    return -1;
}
