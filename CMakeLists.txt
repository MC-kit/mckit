cmake_minimum_required(VERSION 3.19)

include(CMakePrintHelpers)

# to make CMake happy, if not running under skbuild
if(NOT DEFINED SKBUILD_PROJECT_NAME)
  set(SKBUILD_PROJECT_NAME mckit)
  set(SKBUILD_PROJECT_VERSION 0.8.5) # TODO: add this version update to just
                                     # bump action
endif()

cmake_print_variables(SKBUILD_PROJECT_NAME SKBUILD_PROJECT_VERSION SKBUIL_STATE)
project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  DESCRIPTION "mckit geometry extension"
  LANGUAGES C CXX)

if(SKBUILD)
  message(STATUS "The project is built using scikit-build")
endif()

# Only do these if this is the main project, and not if it is included through
# add_subdirectory
if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)

  # Set CMAKE_BUILD_TYPE to Release by default. Must be done before calling
  # project()
  set(default_build_type "Release")
  if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    message(
      STATUS
        "Setting build type to '${default_build_type}' as none was specified.")
    set(CMAKE_BUILD_TYPE
        "${default_build_type}"
        CACHE STRING "Choose the type of build." FORCE)
    # Set the possible values of build type for cmake-gui
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release"
                                                 "MinSizeRel" "RelWithDebInfo")
  endif()

  if(CMAKE_BINARY_DIR STREQUAL CMAKE_SOURCE_DIR)
    message(
      FATAL_ERROR
        "Building in-source is not supported! Create a build dir and remove ${CMAKE_SOURCE_DIR}/CMakeCache.txt"
    )
  endif()

  # find_package(Git QUIET)
  #
  # if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git") execute_process(
  # COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
  # WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} RESULT_VARIABLE
  # GIT_SUBMOD_RESULT) if(NOT GIT_SUBMOD_RESULT EQUAL "0") message( FATAL_ERROR
  # "git submodule update --init --recursive failed with ${GIT_SUBMOD_RESULT},
  # please checkout submodules" ) endif() endif() if(NOT EXISTS
  # "${PROJECT_SOURCE_DIR}/extern/nlopt/CMakeLists.txt") message( FATAL_ERROR
  # "The submodules were not downloaded! GIT_SUBMODULE was turned off or failed.
  # Please update submodules and try again." ) endif()
endif()

# list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake) list(APPEND
# CMAKE_PREFIX_PATH ${PROJECT_SOURCE_DIR}/cmake)

if(WIN32)
  set(Python_FIND_VIRTUALENV FIRST)
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)

# if(NOT DEFINED PythonEnv_ROOT) execute_process( COMMAND ${Python_EXECUTABLE}
# -c "import sys; print(sys.prefix)" WORKING_DIRECTORY
# ${CMAKE_CURRENT_SOURCE_DIR} RESULT_VARIABLE Python_ROOT_FOUND OUTPUT_VARIABLE
# PythonEnv_ROOT OUTPUT_STRIP_TRAILING_WHITESPACE) if(NOT Python_ROOT_FOUND
# STREQUAL "0") message(FATAL_ERROR "Cannot find python environment") endif()
# endif()

if(NOT DEFINED ENV{MCKIT_SRC})
  set(ENV{MCKIT_SRC} ${CMAKE_SOURCE_DIR})
endif()

list(APPEND CMAKE_PREFIX_PATH $ENV{MCKIT_SRC}/.pixi/envs/default/lib/cmake)

cmake_print_variables(CMAKE_MODULE_PATH, CMAKE_PREFIX_PATH)

# add_subdirectory(extern)

# if(NOT WIN32) message("Creating symlinks in environment ${PythonEnv_ROOT}")
# execute_process( COMMAND ${Python_EXECUTABLE} create_mkl_symlinks.py
# WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} OUTPUT_VARIABLE
# CREATED_MKL_SYMLINKS OUTPUT_STRIP_TRAILING_WHITESPACE) endif()

# if(WIN32) set(MKL_DIR ${PythonEnv_ROOT}/Library) else() set(MKL_DIR
# ${PythonEnv_ROOT}) endif()

find_package(MKL REQUIRED)
find_package(NLopt REQUIRED)

set(geometry_dir ${CMAKE_CURRENT_SOURCE_DIR}/src/mckit/src/)

set(geometry_sources
    ${geometry_dir}box.c ${geometry_dir}geometrymodule.c
    ${geometry_dir}rbtree.c ${geometry_dir}shape.c ${geometry_dir}surface.c)

python_add_library(geometry MODULE ${geometry_sources} WITH_SOABI)
target_include_directories(
  geometry PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src/mckit/src MKL::MKL
                  ${Python_NumPy_INCLUDE_DIRS})
target_link_libraries(geometry PUBLIC NLopt::nlopt MKL::MKL)
if(WIN32)
  target_link_libraries(geometry PUBLIC Python::Module)
else()
  target_link_libraries(geometry PUBLIC pthread m dl)
endif()

# install(TARGETS nlopt DESTINATION ${SKBUILD_PROJECT_NAME})
install(TARGETS geometry DESTINATION ${SKBUILD_PROJECT_NAME})

# copy libraries to the source tree for editable installation install(TARGETS
# nlopt DESTINATION $ENV{MCKIT_SRC}/src/mckit)
# install(TARGETS geometry DESTINATION $ENV{MCKIT_SRC}/src/mckit)
install(TARGETS geometry DESTINATION ${CMAKE_SOURCE_DIR}/src/mckit)

include(FeatureSummary)

if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
  feature_summary(WHAT ENABLED_FEATURES DISABLED_FEATURES PACKAGES_FOUND)
  feature_summary(FILENAME ${CMAKE_CURRENT_BINARY_DIR}/features.log WHAT ALL)
endif()
