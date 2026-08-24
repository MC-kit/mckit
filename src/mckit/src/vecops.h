//
// Inline replacements for the MKL cblas functions formerly used by the
// geometry module.
//
// All former call sites operate on short (NDIM = 3) unit-stride vectors,
// for which plain inline loops are faster than dispatching into a BLAS
// library. This removes the MKL dependency from the module entirely.
// The functions accept std::span arguments, so both std::array vectors
// and windows into raw buffers can be passed.
//

#ifndef MCKIT_VECOPS_H
#define MCKIT_VECOPS_H

#include <cmath>
#include <cstddef>
#include <span>

/// Copies the vector src to dst. Replaces cblas_dcopy.
inline void vec_copy(std::span<const double> src, std::span<double> dst)
{
    for (size_t i = 0; i < dst.size(); ++i)
        dst[i] = src[i];
}

/// Adds alpha * x to y. Replaces cblas_daxpy.
inline void vec_axpy(double alpha, std::span<const double> x, std::span<double> y)
{
    for (size_t i = 0; i < y.size(); ++i)
        y[i] += alpha * x[i];
}

/// Returns the dot product of x and y. Replaces cblas_ddot.
inline double vec_dot(std::span<const double> x, std::span<const double> y)
{
    double result = 0;
    for (size_t i = 0; i < x.size(); ++i)
        result += x[i] * y[i];
    return result;
}

/// Multiplies x by alpha. Replaces cblas_dscal.
inline void vec_scale(double alpha, std::span<double> x)
{
    for (size_t i = 0; i < x.size(); ++i)
        x[i] *= alpha;
}

/// Returns the index of the element with the maximal absolute value,
/// the first one on ties. Replaces cblas_idamax.
inline size_t vec_argmax_abs(std::span<const double> x)
{
    size_t index = 0;
    double max_abs = std::fabs(x[0]);
    for (size_t i = 1; i < x.size(); ++i)
    {
        const double abs_xi = std::fabs(x[i]);
        if (abs_xi > max_abs)
        {
            max_abs = abs_xi;
            index = i;
        }
    }
    return index;
}

/// Adds alpha * m * x to y, where m is a row-major n x n matrix
/// with n equal to the size of y. Replaces cblas_dgemv
/// with CblasRowMajor and CblasNoTrans.
inline void mat_vec_add(double alpha, std::span<const double> m, std::span<const double> x,
                        std::span<double> y)
{
    const size_t n = y.size();
    for (size_t i = 0; i < n; ++i)
    {
        double sum = 0;
        for (size_t j = 0; j < n; ++j)
            sum += m[i * n + j] * x[j];
        y[i] += alpha * sum;
    }
}

#endif
