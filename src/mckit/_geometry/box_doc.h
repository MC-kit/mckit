#define BOX_DOC                                                                                                        \
    "Box object."                                                                                                      \
    ""                                                                                                                 \
    "Parameters"                                                                                                       \
    "----------"                                                                                                       \
    ""                                                                                                                 \
    "center : array_like[float]"                                                                                       \
    "    Center of the box being created."                                                                             \
    "xdim, ydim, zdim : float"                                                                                         \
    "    Dimensions of the box."                                                                                       \
    "ex, ey, ez : array_like[float]"                                                                                   \
    "    Basis vectors that give directions of box's edges. They must be"                                              \
    "    orthogonal. For now it is user's responsibility to ensure the "                                               \
    "    orthogonality."                                                                                               \
    ""                                                                                                                 \
    "Methods"                                                                                                          \
    "-------"                                                                                                          \
    ""                                                                                                                 \
    "generate_random_points(n)"                                                                                        \
    "    Generates n random points inside the box."                                                                    \
    "split(dim, ratio)"                                                                                                \
    "    Splits the box into two ones along dim direction."                                                            \
    "test_points(p)"                                                                                                   \
    "    Tests whether point lies inside the box."                                                                     \
    "copy()"                                                                                                           \
    "    Creates a new copy of the box."                                                                               \
    ""                                                                                                                 \
    "Properties"                                                                                                       \
    "----------"                                                                                                       \
    ""                                                                                                                 \
    "center"                                                                                                           \
    "    Box's center"                                                                                                 \
    "volume"                                                                                                           \
    "    Box's volume"                                                                                                 \
    "corners"                                                                                                          \
    "    Box's corners - coordinates of all corners - 8 points."                                                       \
    "bounds"                                                                                                           \
    "    Box's bounds - pairs of min and max values along every dimension."

#define BOX_GRP_DOC "Generates n random points inside the box."

#define BOX_TEST_POINTS_DOC                                                                                            \
    "Checks if point(s) p lies inside the box."                                                                        \
    ""                                                                                                                 \
    "Parameters"                                                                                                       \
    "----------"                                                                                                       \
    ""                                                                                                                 \
    "p : array_like[float]"                                                                                            \
    "    Coordinates of point(s) to be checked. If it is the only one point,"                                          \
    "    then p.shape=(3,). If it is an array of points, then"                                                         \
    "    p.shape=(num_points, 3)."                                                                                     \
    ""                                                                                                                 \
    "Returns"                                                                                                          \
    "-------"                                                                                                          \
    ""                                                                                                                 \
    "result : numpy.ndarray[int]"                                                                                      \
    "    If the point lies inside the box, then 1 value is returned."                                                  \
    "    If the point lies outside of the box False is returned."

#define BOX_SPLIT_DOC                                                                                                  \
    "Splits the box two smaller ones along dim direction."                                                             \
    ""                                                                                                                 \
    "Parameters"                                                                                                       \
    "----------"                                                                                                       \
    ""                                                                                                                 \
    "dir : str"                                                                                                        \
    "    Dimension along which splitting must take place. \"x\" - ex, \"y\" "                                          \
    "- "                                                                                                               \
    "ey,"                                                                                                              \
    "    z - ez. If not specified or \"auto\", then the box will be split "                                            \
    "along the"                                                                                                        \
    "    longest side."                                                                                                \
    "ratio : float"                                                                                                    \
    "    The ratio of two new boxes volumes difference. If < 0.5 the first"                                            \
    "    box will be smaller."                                                                                         \
    ""                                                                                                                 \
    "Returns"                                                                                                          \
    "-------"                                                                                                          \
    ""                                                                                                                 \
    "box1, box2 : Box"                                                                                                 \
    "    Resulting boxes. box1 contains parent box base point."

#define BOX_COPY_DOC "Makes a copy of the box."

#define BOX_CHECK_INTERSECTION_DOC                                                                                     \
    "Checks if the box intersects with another one."                                                                   \
    ""                                                                                                                 \
    "Parameters"                                                                                                       \
    "----------"                                                                                                       \
    "box : Box"                                                                                                        \
    "    The box intersection must be checked with."                                                                   \
    ""                                                                                                                 \
    "Returns"                                                                                                          \
    "-------"                                                                                                          \
    "result : bool"                                                                                                    \
    "    Test result. True if boxes intersect."
