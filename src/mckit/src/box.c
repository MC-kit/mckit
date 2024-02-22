#include "box.h"
#include <mkl.h>
#include <nlopt.h>

// Turn on caching of test_box results.
char enable_box_cache = 0;

/* Each row is delta to be added to center point to obtain specific corner.
 * They must be multiplied by corresponding box's dimensions.
 */
static double perm[NCOR][NDIM] = {{-1, -1, -1}, {-1, -1, 1}, {-1, 1, -1}, {-1, 1, 1},
                                  {1, -1, -1},  {1, -1, 1},  {1, 1, -1},  {1, 1, 1}};

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
        cblas_dcopy(NDIM, box->center, 1, box->corners + i * NDIM, 1);
        cblas_daxpy(NDIM, 0.5 * perm[i][0] * box->dims[0], box->ex, 1, box->corners + i * NDIM, 1);
        cblas_daxpy(NDIM, 0.5 * perm[i][1] * box->dims[1], box->ey, 1, box->corners + i * NDIM, 1);
        cblas_daxpy(NDIM, 0.5 * perm[i][2] * box->dims[2], box->ez, 1, box->corners + i * NDIM, 1);
    }

    // Finding lower and upper bounds
    cblas_dcopy(NDIM, box->corners, 1, box->lb, 1);
    cblas_dcopy(NDIM, box->corners, 1, box->ub, 1);
    for (int i = 1; i < NCOR; ++i)
    {
        for (int j = 0; j < NDIM; ++j)
        {
            if (box->corners[i * NDIM + j] < box->lb[j])
                box->lb[j] = box->corners[i * NDIM + j];
            if (box->corners[i * NDIM + j] > box->ub[j])
                box->ub[j] = box->corners[i * NDIM + j];
        }
    }

    box->rng = NULL;
    box->subdiv = 1; // Means that it is the most outer box for now.

    return BOX_SUCCESS;
}

void box_dispose(Box *box)
{
    if (box != NULL && box->rng != NULL)
        vslDeleteStream(&box->rng);
}

void box_copy(Box *dst, const Box *src)
{
    box_init(dst, src->center, src->ex, src->ey, src->ez, src->dims[0], src->dims[1], src->dims[2]);
    dst->subdiv = src->subdiv;
}

int box_generate_random_points(Box *box, size_t npts, double *points)
{
    // If rng is not allocated yet, try to allocate. It will be used at future calls.
    if (box->rng == NULL)
        vslNewStream(&box->rng, VSL_BRNG_MT19937, 777);
    if (box->rng == NULL)
        return BOX_FAILURE;
    int i, status;
    double d[NDIM];

    // TODO: Try to implement generation of all points during one single call to rng.
    for (i = 0; i < npts; ++i)
    {
        status = vdRngUniform(VSL_RNG_METHOD_UNIFORM_STD, box->rng, NDIM, d, -0.5, 0.5);
        if (status != VSL_STATUS_OK)
            return BOX_FAILURE;

        cblas_dcopy(NDIM, box->center, 1, points + i * NDIM, 1);
        cblas_daxpy(NDIM, d[0] * box->dims[0], box->ex, 1, points + i * NDIM, 1);
        cblas_daxpy(NDIM, d[1] * box->dims[1], box->ey, 1, points + i * NDIM, 1);
        cblas_daxpy(NDIM, d[2] * box->dims[2], box->ez, 1, points + i * NDIM, 1);
    }
    return BOX_SUCCESS;
}

void box_test_points(const Box *box, size_t npts, const double *points, int *result)
{
    double delta[NDIM];
    double x, y, z;
    int i;

    for (i = 0; i < npts; ++i)
    {
        cblas_dcopy(NDIM, points + i * NDIM, 1, delta, 1);
        cblas_daxpy(NDIM, -1, box->center, 1, delta, 1);
        x = cblas_ddot(NDIM, delta, 1, box->ex, 1) / box->dims[0];
        y = cblas_ddot(NDIM, delta, 1, box->ey, 1) / box->dims[1];
        z = cblas_ddot(NDIM, delta, 1, box->ez, 1) / box->dims[2];
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
        dir = (int)cblas_idamax(NDIM, box->dims, 1);

    double center1[NDIM], center2[NDIM], dims1[NDIM], dims2[NDIM];
    const double *basis[NDIM] = {box->ex, box->ey, box->ez};

    // find new dimensions
    cblas_dcopy(NDIM, box->dims, 1, dims1, 1);
    cblas_dcopy(NDIM, box->dims, 1, dims2, 1);
    dims1[dir] *= ratio;
    dims2[dir] *= 1 - ratio;

    // find new centers.
    cblas_dcopy(NDIM, box->center, 1, center1, 1);
    cblas_dcopy(NDIM, box->center, 1, center2, 1);

    cblas_daxpy(NDIM, -0.5 * dims2[dir], basis[dir], 1, center1, 1);
    cblas_daxpy(NDIM, 0.5 * dims1[dir], basis[dir], 1, center2, 1);

    // subdivision index.
    char hb = high_bit(box->subdiv);
    uint64_t ones = ~0;
    uint64_t mask = (ones) >> (BIT_LEN - 1) << (hb - 1);
    uint64_t start_bit = mask << 1;
    // create new boxes.
    int status;
    status = box_init(box1, center1, box->ex, box->ey, box->ez, dims1[0], dims1[1], dims1[2]);
    if (status == BOX_FAILURE)
        return BOX_FAILURE;

    status = box_init(box2, center2, box->ex, box->ey, box->ez, dims2[0], dims2[1], dims2[2]);
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

void box_ieqcons(unsigned int m, double *result, unsigned int n, const double *x, double *grad, void *f_data)
{
    Box *box = (Box *)f_data;

    const double *basis[NDIM] = {box->ex, box->ey, box->ez};
    double point[NDIM];
    int i, j, mult;

    for (i = 0; i < 6; ++i)
    {
        cblas_dcopy(NDIM, box->center, 1, point, 1);
        mult = 2 * (i % 2) - 1;
        j = i % 3;
        cblas_daxpy(NDIM, mult * box->dims[j], basis[j], 1, point, 1);
        result[i] = mult * (cblas_ddot(NDIM, basis[j], 1, x, 1) - cblas_ddot(NDIM, basis[j], 1, point, 1));

        if (grad != NULL)
        {
            cblas_dcopy(NDIM, basis[j], 1, grad + i * NDIM, 1);
            cblas_dscal(NDIM, mult, grad + i * NDIM, 1);
        }
    }
}

double min_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    Box *data = (Box *)f_data;
    if (grad != NULL)
    {
        cblas_dcopy(NDIM, x, 1, grad, 1);
        cblas_daxpy(NDIM, -1, data->center, 1, grad, 1);
        cblas_dscal(NDIM, 2, grad, 1);
    }
    double delta[NDIM];
    cblas_dcopy(NDIM, x, 1, delta, 1);
    cblas_daxpy(NDIM, -1, data->center, 1, delta, 1);
    return cblas_ddot(NDIM, delta, 1, delta, 1);
}

// Checks if the box intersects with another one.
int box_check_intersection(const Box *box1, const Box *box2)
{
    double x[NDIM], opt_val;
    nlopt_result opt_result;
    int result;

    nlopt_opt opt;
    opt = nlopt_create(NLOPT_LD_SLSQP, 3);
    nlopt_set_lower_bounds(opt, box1->lb);
    nlopt_set_upper_bounds(opt, box1->ub);

    nlopt_set_min_objective(opt, min_func, box2);

    nlopt_add_inequality_mconstraint(opt, 6, box_ieqcons, (void *)box1, NULL);
    nlopt_set_stopval(opt, 0);
    nlopt_set_maxeval(opt, 1000); // TODO: consider passing this parameter.

    cblas_dcopy(NDIM, box1->center, 1, x, 1);
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
