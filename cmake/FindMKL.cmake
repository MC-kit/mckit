# ##############################################################################
#
# Simplified version of
# https://github.com/PyMesh/PyMesh/blob/main/cmake/FindMKL.cmake
#
# \file      cmake/FindMKL.cmake \author    J. Bakosi \copyright 2012-2015,
# Jozsef Bakosi, 2016, Los Alamos National Security, LLC. \brief     Find the
# Math Kernel Library from Intel \date      Thu 26 Jan 2017 02:05:50 PM MST
#
# ##############################################################################

# Find the Math Kernel Library from Intel
#
# MKL_FOUND - System has MKL MKL_INCLUDE_DIRS - MKL include files directories
# MKL_LIBRARIES - The MKL libraries
#
# The environment variable MKL_DIR is used to find the library. Everything else
# is ignored. If MKL is found "-DMKL_ILP64" is added to CMAKE_C_FLAGS and
# CMAKE_CXX_FLAGS.
#
# Example usage:
#
# find_package(MKL) if(MKL_FOUND) target_link_libraries(TARGET ${MKL_LIBRARIES})
# endif()

# If already in cache, be silent
if(MKL_INCLUDE_DIRS AND MKL_LIBRARIES)
  set(MKL_FIND_QUIETLY TRUE)
endif()

find_path(
  MKL_INCLUDE_DIR
  NAMES mkl.h
  HINTS ${MKL_DIR}/include)

find_library(
  MKL_RT_LIBRARY
  NAMES mkl_rt
  PATHS ${MKL_DIR}/lib ${MKL_DIR}/bin REQUIRED)

set(MKL_INCLUDE_DIRS ${MKL_INCLUDE_DIR})
set(MKL_LIBRARIES ${MKL_RT_LIBRARY})

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(MKL REQUIRED_VARS MKL_LIBRARIES
                                                    MKL_INCLUDE_DIRS)

mark_as_advanced(MKL_INCLUDE_DIRS MKL_LIBRARIES)
