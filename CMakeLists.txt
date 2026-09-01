cmake_minimum_required(VERSION 3.28.0)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/module/")

include(CMakePrintHelpers)

# to make CMake happy, if not running under skbuild
if(NOT DEFINED SKBUILD_PROJECT_NAME AND DEFINED ENV{PIXI_PROJECT_VERSION})
  set(SKBUILD_PROJECT_NAME mckit)
  set(SKBUILD_PROJECT_VERSION $ENV{PIXI_PROJECT_VERSION})
endif()

cmake_print_variables(SKBUILD_PROJECT_NAME SKBUILD_PROJECT_VERSION SKBUIL_STATE)

project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  DESCRIPTION "mckit geometry extension"
  LANGUAGES C CXX
)

if(SKBUILD)
  message(STATUS "The project is built using scikit-build")
endif()

# Only do these if this is the main project, and not if it is included through
# add_subdirectory
if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)

  include(SetBuildType)
  include(NoInSourceBuild)
  include(UpdateGitSubModules)

  # Libc++ has no support compiler extensions for modules.
  set(CMAKE_CXX_EXTENSIONS OFF)
  # Set C++ standard
  set(CMAKE_CXX_STANDARD 20)
  # Use Inter Procedural Optimization, if possible
  include(CheckIPOSupported)
  check_ipo_supported(RESULT ipo_supported)
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ${ipo_supported})
  cmake_print_variables(ipo_supported)
endif()

option(MCKIT_BUILD_TEST "Build and run MCKIT CTEST suite" TRUE)
option(MCKIT_BUILD_COVERAGE "Check coverage of MCKIT CTEST suite" TRUE)
option(MCKIT_BUILD_MEMCHECK "Check memory leaks with valgrind" TRUE)
if (NOT MCKIT_BUILD_TEST)
  set(MCKIT_BUILD_COVERAGE FALSE)
  set(MCKIT_BUILD_MEMCHECK FALSE)
endif()

if(WIN32)
  set(Python_FIND_VIRTUALENV FIRST)
endif()

find_package(Python COMPONENTS Interpreter Development.Module NumPy)


add_subdirectory(extern)

add_library( geometry_objs STATIC
  src/mckit/_geometry/box.cpp
  src/mckit/_geometry/shape.cpp
  src/mckit/_geometry/surface.cpp
  src/mckit/_geometry/stats.h
  src/mckit/_geometry/rand.h
  src/mckit/_geometry/vecops.h
)
target_include_directories( geometry_objs
  PUBLIC 
    ${CMAKE_CURRENT_SOURCE_DIR}/src/mckit/_geometry 
    ${Python_NumPy_INCLUDE_DIRS}
)
set_target_properties(geometry_objs PROPERTIES
  POSITION_INDEPENDENT_CODE 1
)
if (MCKIT_BUILD_COVERAGE AND CMAKE_BUILD_TYPE STREQUAL Debug)
  target_compile_options(geometry_objs PRIVATE --coverage)
  target_link_options(geometry_objs PUBLIC --coverage)
  add_custom_command(TARGET geometry_objs PRE_BUILD COMMAND
    find ${CMAKE_BINARY_DIR} -type f -name '*.gcda' -exec rm {} +
  )
endif()
target_link_Libraries(geometry_objs PUBLIC nlopt)
include(Format)
Format(geometry_objs src/mckit/_geometry)
#  TODO @dvp: fix clang-tidy warnings allowingx` more checks
#      in .clang-tidy config,
#      when ctest testing coverage reaches at least 80% 
# include(ClangTidy)
# AddClangTidy(geometry_objs) 


python_add_library( geometry MODULE
  src/mckit/_geometry/geometrymodule.cpp
  WITH_SOABI
)
# target_include_directories( geometry
#   PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/_geometry/mckit/_geometry ${Python_NumPy_INCLUDE_DIRS}
# )
target_link_libraries(geometry PUBLIC geometry_objs)
if(WIN32)
  target_link_libraries(geometry PUBLIC Python::Module)
else()
  target_link_libraries(geometry PUBLIC pthread m dl)
endif()
# Обработка специфичных флагов для abi3t (free-threaded)
if(Py_TARGET_ABI3T)
  target_compile_definitions(geometry PRIVATE Py_TARGET_ABI3T=0x030f0000)
endif()

# fix rpath
# https://scikit-build-core.readthedocs.io/en/latest/guide/dynamic_link.html
if(APPLE)
  set(origin_token "@loader_path")
else()
  set(origin_token "$ORIGIN")
endif()
set_property(TARGET geometry PROPERTY INSTALL_RPATH "${origin_token}/../../..")
install(TARGETS geometry DESTINATION ${SKBUILD_PROJECT_NAME})

include(FetchContent)
set(FETCHCONTENT_BASE_DIR "${CMAKE_SOURCE_DIR}/_deps")
include(fetchcontent-offline)
FetchContent_DisconnectedIfOffline() 

if(MCKIT_BUILD_TEST)
  add_subdirectory(ctests)
endif()
  

include(FeatureSummary)

if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
  feature_summary(WHAT ENABLED_FEATURES DISABLED_FEATURES PACKAGES_FOUND)
  feature_summary(FILENAME ${CMAKE_CURRENT_BINARY_DIR}/features.log WHAT ALL)
endif()
