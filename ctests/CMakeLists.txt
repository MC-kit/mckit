message(STATUS Building MCKIT CTEST suite)
include(CTest)
# Example of GTest loading (https://cmake.org/cmake/help/latest/module/FetchContent.html)
# FetchContent_Declare(
#   googletest
#   GIT_REPOSITORY https://github.com/google/googletest.git
#   GIT_TAG        703bd9caab50b139428cea1aaff9974ebee5742e # release-1.10.0 # dvp: obsolete
#   FIND_PACKAGE_ARGS NAMES GTest
# )
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG
    v3.16.0
    FIND_PACKAGE_ARGS
)
FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(Catch)

add_executable(test_box test_box.cpp)
target_link_libraries(test_box PRIVATE geometry_objs Catch2::Catch2WithMain)
# add_test(NAME test_box COMMAND test_box)
include(Format)
Format(test_box .)

if (MCKIT_BUILD_COVERAGE)
    include(Coverage)
    AddCoverage(test_box)
endif()
catch_discover_tests(test_box)

if (MCKIT_BUILD_MEMCHECK)
    # include(Valgrind)
    # AddValgrind(test_box)

    # use this wrapper around Valgrind if online
    include(Memcheck)
    AddMemcheck(test_box)

endif()