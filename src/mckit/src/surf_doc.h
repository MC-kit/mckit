#define SURF_TEST_POINTS_DOC                                                                                           \
    "Checks the sense of point(s) p."                                                                                  \
    ""                                                                                                                 \
    "Parameters"                                                                                                       \
    "----------"                                                                                                       \
    "p : array_like[float]"                                                                                            \
    "    Coordinates of point(s) to be checked. If it is the only one point,"                                          \
    "    then p.shape=(3,). If it is an array of points, then"                                                         \
    "    p.shape=(num_points, 3)."                                                                                     \
    ""                                                                                                                 \
    "Returns"                                                                                                          \
    "-------"                                                                                                          \
    "sense : numpy.ndarray[int]"                                                                                       \
    "    If the point has positive sense, then +1 value is returned."                                                  \
    "    If point lies on the surface 0 is returned."                                                                  \
    "    If point has negative sense -1 is returned."

#define SURF_TEST_BOX_DOC                                                                                              \
    "Checks whether this surface crosses the box."                                                                     \
    ""                                                                                                                 \
    "Box defines a rectangular cuboid. This method checks if this surface"                                             \
    "crosses the box, i.e. there is two points belonging to this box which"                                            \
    "have different sense with respect to this surface."                                                               \
    ""                                                                                                                 \
    "Parameters"                                                                                                       \
    "----------"                                                                                                       \
    "box : Box"                                                                                                        \
    "    Describes the box."                                                                                           \
    ""                                                                                                                 \
    "Returns"                                                                                                          \
    "-------"                                                                                                          \
    "result : int"                                                                                                     \
    "    Test result. It equals one of the following values:"                                                          \
    "    +1 if every point inside the box has positive sense."                                                         \
    "    0 if there are both points with positive and negative sense inside"                                           \
    "    the box"                                                                                                      \
    "    -1 if every point inside the box has negative sense."
