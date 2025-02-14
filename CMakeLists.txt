cmake_minimum_required(VERSION 3.19...3.27)

include(CMakePrintHelpers)

if(NOT DEFINED SKBUILD_PROJECT_NAME)
  set(SKBUILD_PROJECT_NAME mckit)
  set(SKBUILD_PROJECT_VERSION 0.6.28)
endif()

cmake_print_variables(SKBUILD_PROJECT_NAME SKBUILD_PROJECT_VERSION)

# TODO: setup SKBUILD variables in build.py - retrieve from poetry
project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  DESCRIPTION "mckit geometry extension"
  LANGUAGES C # TODO: upgrade to CXX
)

# https://cliutils.gitlab.io/modern-cmake/chapters/packages/CUDA.html
# include(CheckLanguage) check_language(CUDA) if(CMAKE_CUDA_COMPILER)
# enable_language(CUDA) endif()

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

  find_package(Git QUIET)

  if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git")
    execute_process(
      COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
      RESULT_VARIABLE GIT_SUBMOD_RESULT)
    if(NOT GIT_SUBMOD_RESULT EQUAL "0")
      message(
        FATAL_ERROR
          "git submodule update --init --recursive failed with ${GIT_SUBMOD_RESULT}, please checkout submodules"
      )
    endif()
  endif()
  if(NOT EXISTS "${PROJECT_SOURCE_DIR}/extern/nlopt/CMakeLists.txt")
    message(
      FATAL_ERROR
        "The submodules were not downloaded! GIT_SUBMODULE was turned off or failed. Please update submodules and try again."
    )
  endif()
endif()

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake)
list(APPEND CMAKE_PREFIX_PATH ${PROJECT_SOURCE_DIR}/cmake)

if(WIN32)
  set(Python_FIND_VIRTUALENV FIRST)
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)

cmake_print_variables(Python_EXECUTABLE Python_LIBRARIES Python_LIBRARY_DIRS
                      Python_NumPy_INCLUDE_DIRS Python_STDLIB Python_SITELIB)

# TODO dvp: check if CLI variable provided by sci-build are sufficient instead
# of own search

if(NOT DEFINED PythonEnv_ROOT)

  execute_process(
    COMMAND ${Python_EXECUTABLE} -c "import sys; print(sys.prefix)"
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE Python_ROOT_FOUND
    OUTPUT_VARIABLE PythonEnv_ROOT
    OUTPUT_STRIP_TRAILING_WHITESPACE)
  if(NOT Python_ROOT_FOUND STREQUAL "0")
    message(FATAL_ERROR "Cannot find python environment")
  endif()
endif()
cmake_print_variables(PythonEnv_ROOT)

list(APPEND CMAKE_PREFIX_PATH ${PythonEnv_ROOT})

add_subdirectory(extern)

if(NOT WIN32)
  message("Creating symlinks in environment ${PythonEnv_ROOT}")
  execute_process(
    COMMAND ${Python_EXECUTABLE} create_mkl_symlinks.py
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT_VARIABLE CREATED_MKL_SYMLINKS
    OUTPUT_STRIP_TRAILING_WHITESPACE)
endif()

if(WIN32)
  set(MKL_DIR ${PythonEnv_ROOT}/Library)
else()
  set(MKL_DIR ${PythonEnv_ROOT})
endif()

cmake_print_variables(MKL_DIR)
cmake_print_variables(CMAKE_MODULE_PATH CMAKE_PREFIX_PATH)

find_package(MKL REQUIRED)

set(geometry_dir ${CMAKE_CURRENT_SOURCE_DIR}/src/mckit/src/)

set(geometry_sources
    ${geometry_dir}box.c ${geometry_dir}geometrymodule.c
    ${geometry_dir}rbtree.c ${geometry_dir}shape.c ${geometry_dir}surface.c)

python_add_library(geometry MODULE ${geometry_sources} WITH_SOABI)
target_include_directories(
  geometry PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src/mckit/src ${MKL_INCLUDE_DIR}
                  ${Python_NumPy_INCLUDE_DIRS})
target_link_libraries(geometry PUBLIC nlopt ${MKL_LIBRARIES})
if(WIN32)
  target_link_libraries(geometry PUBLIC Python::Module)
else()
  target_link_libraries(geometry PUBLIC pthread m dl)
endif()

install(TARGETS nlopt LIBRARY DESTINATION src/mckit)
install(TARGETS geometry LIBRARY DESTINATION src/mckit)

include(FeatureSummary)

if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
  feature_summary(WHAT ENABLED_FEATURES DISABLED_FEATURES PACKAGES_FOUND)
  feature_summary(FILENAME ${CMAKE_CURRENT_BINARY_DIR}/features.log WHAT ALL)
endif()
