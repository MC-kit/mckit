message(STATUS Building MCKIT CTEST suite)
include(CTest)
include(FetchContent)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG
    v3.16.0
)
FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(Catch)

add_executable(test_box test_box.cpp)
target_link_libraries(test_box PRIVATE geometry_objs Catch2::Catch2WithMain)
# add_test(NAME test_box COMMAND test_box)

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