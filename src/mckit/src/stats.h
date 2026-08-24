//
// Statistics storage for Shape argument results.
//
// Replaces the former hand-written red-black tree (rbtree.c/rbtree.h).
// Keys are vectors of per-argument test results (+1/0/-1), values are
// volumes of the boxes these results were collected for.
//

#ifndef MCKIT_STATS_H
#define MCKIT_STATS_H

#include <cstddef>
#include <map>
#include <vector>

/// Strict weak ordering for statistics keys.
///
/// Replicates the ordering of the original reversed lexicographic comparator
/// from the removed red-black tree implementation, so that iteration over the
/// storage (and therefore row order of get_stat_table) stays exactly the same.
struct StatKeyLess
{
    bool operator()(const std::vector<char> &a, const std::vector<char> &b) const
    {
        const size_t n = a.size() < b.size() ? a.size() : b.size();
        for (size_t i = 0; i < n; ++i)
        {
            if (a[i] > b[i])
                return true;
            if (a[i] < b[i])
                return false;
        }
        return false;
    }
};

/// Storage of statistics about shape argument results.
///
/// On insertion of a duplicate key the first recorded volume is kept,
/// matching the behavior of the former red-black tree based implementation.
struct StatsMap
{
    std::map<std::vector<char>, double, StatKeyLess> entries;
};

#endif