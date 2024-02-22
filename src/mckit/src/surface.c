#include "surface.h"
#include "mkl.h"
#include "nlopt.h"
#include <math.h>
#include <stdlib.h>

// dvp:
// Don't use "standard" macro "max": it can cause not obvious effects.
// To avoid this, libraries usually undefine it, we'd better follow this
// practice.
#ifdef max
#undef max
#endif

#define surface_INIT(surf)                                                                                             \
    (surf)->last_box = 0;                                                                                              \
    (surf)->last_box_result = 0;

static double _max(double a, double b)
{
    return (a < b) ? b : a;
}

/*
 *  In all surf_func functions the first argument is space dimension. This
 * argument introduced for the purposes of compatibility with NLOPT library.
 */

/// Calculates deviation of point x from the plane.
double plane_func(unsigned int n,  // Space dimension (must be NDIM)
                  const double *x, // Point to be checked
                  double *grad,    // Gradient - calculated if not NULL
                  void *f_data     // Surface data - parameters of the function.
)
{
    Plane *data = (Plane *)f_data;
    if (grad != NULL)
    {
        cblas_dcopy(NDIM, data->norm, 1, grad, 1);
    }
    return cblas_ddot(NDIM, x, 1, data->norm, 1) + data->offset;
}

/// Calculates deviation of point x from the sphere.
double sphere_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    Sphere *data = (Sphere *)f_data;
    if (grad != NULL)
    {
        cblas_dcopy(NDIM, x, 1, grad, 1);
        cblas_daxpy(NDIM, -1, data->center, 1, grad, 1);
        cblas_dscal(NDIM, 2, grad, 1);
    }
    double delta[NDIM];
    cblas_dcopy(NDIM, x, 1, delta, 1);
    cblas_daxpy(NDIM, -1, data->center, 1, delta, 1);
    return cblas_ddot(NDIM, delta, 1, delta, 1) - pow(data->radius, 2);
}

double cylinder_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    Cylinder *data = (Cylinder *)f_data;
    double a[NDIM];
    cblas_dcopy(NDIM, x, 1, a, 1);
    cblas_daxpy(NDIM, -1, data->point, 1, a, 1);
    double an = cblas_ddot(NDIM, a, 1, data->axis, 1);
    if (grad != NULL)
    {
        cblas_dcopy(NDIM, a, 1, grad, 1);
        cblas_daxpy(NDIM, -an, data->axis, 1, grad, 1);
        cblas_dscal(NDIM, 2, grad, 1);
    }
    return cblas_ddot(NDIM, a, 1, a, 1) - pow(an, 2) - pow(data->radius, 2);
}

double RCC_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    RCC *data = (RCC *)f_data;
    double gcyl[NDIM];
    double gtop[NDIM];
    double gbot[NDIM];
    for (int i = 0; i < NDIM; ++i)
    {
        gcyl[i] = 0;
        gtop[i] = 0;
        gbot[i] = 0;
    }
    double cyl_obj = cylinder_func(n, x, gcyl, data->cyl);
    double top_obj = plane_func(n, x, gtop, data->top);
    double bot_obj = plane_func(n, x, gbot, data->bot);

    double tot_wgt = fabs(top_obj + bot_obj);
    double top_wgt = fabs(top_obj) / tot_wgt;
    double bot_wgt = fabs(bot_obj) / tot_wgt;

    double h = fabs(data->top->offset + data->bot->offset);
    if (grad != NULL)
    {
        cblas_daxpy(NDIM, top_wgt, gtop, 1, grad, 1);
        cblas_daxpy(NDIM, bot_wgt, gbot, 1, grad, 1);
        cblas_daxpy(NDIM, 1, gcyl, 1, grad, 1);
    }
    return _max(cyl_obj, _max(top_obj, bot_obj));
}

double BOX_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    BOX *data = (BOX *)f_data;
    double gp[NDIM * BOX_PLANE_NUM];
    double result[BOX_PLANE_NUM];
    for (int i = 0; i < NDIM * BOX_PLANE_NUM; ++i)
        gp[i] = 0;

    int index = 0;
    for (int i = 0; i < BOX_PLANE_NUM; ++i)
    {
        result[i] = plane_func(n, x, gp + i * NDIM, data->planes[i]);
        if (result[i] > result[index])
            index = i;
    }

    if (grad != NULL)
    {
        cblas_dcopy(NDIM, gp + index * NDIM, 1, grad, 1);
    }

    return result[index];
}

double cone_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    Cone *data = (Cone *)f_data;
    double a[NDIM];
    cblas_dcopy(NDIM, x, 1, a, 1);
    cblas_daxpy(NDIM, -1, data->apex, 1, a, 1);
    double an = cblas_ddot(NDIM, a, 1, data->axis, 1);
    if (data->sheet != 0 && data->sheet * an < 0)
        an = 0;
    if (grad != NULL)
    {
        cblas_dcopy(NDIM, a, 1, grad, 1);
        cblas_daxpy(NDIM, -an * (1 + data->ta), data->axis, 1, grad, 1);
        cblas_dscal(NDIM, 2, grad, 1);
    }
    return cblas_ddot(NDIM, a, 1, a, 1) - pow(an, 2) * (1 + data->ta);
}

double gq_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    GQuadratic *data = (GQuadratic *)f_data;
    if (grad != NULL)
    {
        cblas_dcopy(NDIM, data->v, 1, grad, 1);
        cblas_dgemv(CblasRowMajor, CblasNoTrans, NDIM, NDIM, 2, data->m, NDIM, x, 1, 1, grad, 1);
        cblas_dscal(NDIM, data->factor, grad, 1);
    }
    double y[NDIM];
    cblas_dcopy(NDIM, data->v, 1, y, 1);
    cblas_dgemv(CblasRowMajor, CblasNoTrans, NDIM, NDIM, 1, data->m, NDIM, x, 1, 1, y, 1);
    return (cblas_ddot(NDIM, y, 1, x, 1) + data->k) * data->factor;
}

double clip_negative_values(double value)
{
    return (value > 0.0) ? value : 0.0;
}

double torus_func(unsigned int n, const double *x, double *grad, void *f_data)
{
    Torus *data = (Torus *)f_data;
    double p[NDIM];
    cblas_dcopy(NDIM, x, 1, p, 1);
    cblas_daxpy(NDIM, -1, data->center, 1, p, 1);
    double pn = cblas_ddot(NDIM, p, 1, data->axis, 1);
    double pp = cblas_ddot(NDIM, p, 1, p, 1);
    double sq = sqrt(clip_negative_values(pp - pow(pn, 2)));
    if (grad != NULL)
    {
        double add = 0;
        if (sq > 1.e-100)
            add = data->radius / sq;
        cblas_dcopy(NDIM, p, 1, grad, 1);
        cblas_daxpy(NDIM, -pn, data->axis, 1, grad, 1);
        cblas_dscal(NDIM, (1 - add) / pow(data->b, 2), grad, 1);
        cblas_daxpy(NDIM, pn / pow(data->a, 2), data->axis, 1, grad, 1);
        cblas_dscal(NDIM, 2, grad, 1);
    }
    return pow(pn / data->a, 2) + pow((sq - data->radius) / data->b, 2) - 1;
}

// Interface to all surface functions. Decides, which function to apply.
double surface_func(unsigned int n,  // Space dimension (NDIM)
                    const double *x, // Point to be checked
                    double *grad,    // Gradient - calculated if not NULL (array of size NDIM)
                    void *f_data     // Surface data
)
{
    Surface *surf = (Surface *)f_data;
    double fval;
    switch (surf->type)
    {
    case PLANE:
        fval = plane_func(n, x, grad, f_data);
        break;
    case SPHERE:
        fval = sphere_func(n, x, grad, f_data);
        break;
    case CYLINDER:
        fval = cylinder_func(n, x, grad, f_data);
        break;
    case CONE:
        fval = cone_func(n, x, grad, f_data);
        break;
    case TORUS:
        fval = torus_func(n, x, grad, f_data);
        break;
    case GQUADRATIC:
        fval = gq_func(n, x, grad, f_data);
        break;
    case MRCC:
        fval = RCC_func(n, x, grad, f_data);
        break;
    case MBOX:
        fval = BOX_func(n, x, grad, f_data);
        break;
    default:
        fval = 0;
        break;
    }
    return fval;
}

int plane_init(Plane *surf, const double *norm, double offset)
{
    int i;
    surface_INIT((Surface *)surf) surf->base.type = PLANE;
    surf->offset = offset;
    for (i = 0; i < NDIM; ++i)
    {
        surf->norm[i] = norm[i];
    }
    return SURFACE_SUCCESS;
}

int sphere_init(Sphere *surf, const double *center, double radius)
{
    if (radius <= 0)
        return SURFACE_FAILURE;
    int i;
    surface_INIT((Surface *)surf);
    surf->base.type = SPHERE;
    surf->radius = radius;
    for (i = 0; i < NDIM; ++i)
    {
        surf->center[i] = center[i];
    }
    return SURFACE_SUCCESS;
}

int cylinder_init(Cylinder *surf, const double *point, const double *axis, double radius)
{
    if (radius <= 0)
        return SURFACE_FAILURE;
    int i;
    surface_INIT((Surface *)surf);
    surf->base.type = CYLINDER;
    surf->radius = radius;
    for (i = 0; i < NDIM; ++i)
    {
        surf->point[i] = point[i];
        surf->axis[i] = axis[i];
    }
    return SURFACE_SUCCESS;
}

int RCC_init(RCC *surf, Cylinder *cyl, Plane *top, Plane *bot)
{
    surface_INIT((Surface *)surf);
    surf->base.type = MRCC;
    surf->cyl = cyl;
    surf->top = top;
    surf->bot = bot;
    return SURFACE_SUCCESS;
}

int BOX_init(BOX *surf, Plane **planes)
{
    surface_INIT((Surface *)surf);
    surf->base.type = MBOX;
    for (int i = 0; i < BOX_PLANE_NUM; ++i)
    {
        surf->planes[i] = planes[i];
    }
    return SURFACE_SUCCESS;
}

int cone_init(Cone *surf, const double *apex, const double *axis, double ta, int sheet)
{
    if (ta <= 0)
        return SURFACE_FAILURE;
    int i;
    surface_INIT((Surface *)surf);
    surf->base.type = CONE;
    surf->ta = ta;
    surf->sheet = sheet;
    for (i = 0; i < NDIM; ++i)
    {
        surf->apex[i] = apex[i];
        surf->axis[i] = axis[i];
    }
    return SURFACE_SUCCESS;
}

int torus_init(Torus *surf, const double *center, const double *axis, double radius, double a, double b)
{
    if (a <= 0 || b <= 0)
        return SURFACE_FAILURE;
    int i;
    surface_INIT((Surface *)surf);
    surf->base.type = TORUS;
    surf->radius = radius;
    surf->a = a;
    surf->b = b;
    for (i = 0; i < NDIM; ++i)
    {
        surf->center[i] = center[i];
        surf->axis[i] = axis[i];
    }
    if (surf->b > surf->radius)
    {
        surf->degenerate = 1;
        double offset = a * sqrt(1 - pow(radius / b, 2));
        cblas_dcopy(NDIM, center, 1, surf->specpts, 1);
        cblas_dcopy(NDIM, center, 1, surf->specpts + NDIM, 1);
        cblas_daxpy(NDIM, offset, axis, 1, surf->specpts, 1);
        cblas_daxpy(NDIM, -offset, axis, 1, surf->specpts + NDIM, 1);
    }
    else
        surf->degenerate = 0;
    return SURFACE_SUCCESS;
}

int gq_init(GQuadratic *surf, const double *m, const double *v, double k, double factor)
{
    int i, j;
    surface_INIT((Surface *)surf);
    surf->base.type = GQUADRATIC;
    surf->k = k;
    surf->factor = factor;
    for (i = 0; i < NDIM; ++i)
    {
        surf->v[i] = v[i];
        for (j = 0; j < NDIM; ++j)
            surf->m[i * NDIM + j] = m[i * NDIM + j];
    }
    return SURFACE_SUCCESS;
}

void surface_test_points(const Surface *surf, size_t npts, const double *points, char *result)
{
    int i;
    double fval;
    for (i = 0; i < npts; ++i)
    {
        fval = surface_func(NDIM, points + NDIM * i, NULL, (void *)surf);
        result[i] = (int)copysign(1, fval);
    }
}

int surface_test_box(Surface *surf, const Box *box)
{
    if (surf->last_box != 0)
    {
        int bc = box_is_in(box, surf->last_box);
        // if it is the box already tested (bc == 0) then returns cached result;
        // if it is inner box - then returns cached result only if it is not 0.
        // For inner box result may be different.
        if (bc == 0 || bc > 0 && surf->last_box_result != 0)
            return surf->last_box_result;
    }

    // First, test corner points of the box. If they have different senses,
    // then surface definitely intersects the box.
    char corner_tests[NCOR];
    surface_test_points(surf, NCOR, box->corners, corner_tests);
    int mins = 1, maxs = -1, i;

    for (i = 0; i < NCOR; ++i)
    {
        if (corner_tests[i] < mins)
            mins = corner_tests[i];
        if (corner_tests[i] > maxs)
            maxs = corner_tests[i];
    }
    // sign == 0 only if both -1 and +1 present in corner_tests.
    int sign = mins + maxs;
    if (sign == 2)
        sign = 1;
    else if (sign == -2)
        sign = -1;

    // The test performed above is sufficient for the plane.
    // But for other surfaces further tests must be done if sign != 0.
    if (sign != 0 && surf->type != PLANE)
    {
        // Additional tests for degenerate torus.
        if (surf->type == TORUS && ((Torus *)surf)->degenerate)
        {
            int test_res[2];
            box_test_points(box, 2, ((Torus *)surf)->specpts, test_res);
            if (test_res[0] == 1 || test_res[1] == 1)
                return 0;
        }

        // General test. The purpose is to clarify if there is a point inside
        // the box with positive sense if all corner results are negative; or a
        // point with nefative sense exists inside the box if all corner results
        // are negative. SLSQP optimization method is used.
        double x[NDIM], opt_val;
        double xtol[NDIM];
        nlopt_result opt_result;

        nlopt_opt opt;
        opt = nlopt_create(NLOPT_LD_SLSQP, 3);
        nlopt_set_lower_bounds(opt, box->lb);
        nlopt_set_upper_bounds(opt, box->ub);

        if (sign > 0)
            nlopt_set_min_objective(opt, surface_func, surf);
        else
            nlopt_set_max_objective(opt, surface_func, surf);

        for (i = 0; i < NDIM; ++i)
            xtol[i] = box->dims[i] / 1000;

        nlopt_add_inequality_mconstraint(opt, 6, box_ieqcons, (void *)box, NULL);
        nlopt_set_stopval(opt, 0);
        nlopt_set_maxeval(opt, 1000); // TODO: consider passing this parameter.
        // nlopt_set_xtol_abs(opt, xtol);

        // Because the problem is nonlinear, the points, where gradient is 0
        // exist. To avoid such trap we start optimization from several points -
        // box's corners.
        for (i = 0; i < NCOR; ++i)
        {
            cblas_dcopy(NDIM, box->corners + i * NDIM, 1, x, 1);
            opt_result = nlopt_optimize(opt, x, &opt_val);
            if (sign * opt_val < 0)
            {             // If sign and found opt_val have
                          // different signs - the surface
                sign = 0; // definitely intersects the box. If we have not found
                          // such solution
                break;    // - for sure not intersects.
            }
        }
        nlopt_destroy(opt);
    }
    // Cache test result;
    if (!(box->subdiv & HIGHEST_BIT))
    {
        surf->last_box = box->subdiv;
        surf->last_box_result = sign;
    }

    return sign;
}
