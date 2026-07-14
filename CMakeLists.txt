cmake_minimum_required(VERSION 3.19)

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

  find_package(Git QUIET)

  # if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git") execute_process(
  # COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
  # WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} RESULT_VARIABLE
  # GIT_SUBMOD_RESULT) if(NOT GIT_SUBMOD_RESULT EQUAL "0") message( FATAL_ERROR
  # "git submodule update --init --recursive failed with ${GIT_SUBMOD_RESULT},
  # please checkout submodules" ) endif() endif() if(NOT EXISTS
  # "${PROJECT_SOURCE_DIR}/extern/nlopt/CMakeLists.txt") message( FATAL_ERROR
  # "The submodules were not downloaded! GIT_SUBMODULE was turned off or failed.
  # Please update submodules and try again." ) endif()

  # Set C++ standard
  set(CMAKE_CXX_STANDARD 20)
  # Use Inter Procedural Optimization, if possible
  include(CheckIPOSupported)
  check_ipo_supported(RESULT ipo_supported)
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ${ipo_supported})
  cmake_print_variables(ipo_supported)
endif()

# list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake) list(APPEND
# CMAKE_PREFIX_PATH ${PROJECT_SOURCE_DIR}/cmake)

if(WIN32)
  set(Python_FIND_VIRTUALENV FIRST)
endif()

find_package(
  Python COMPONENTS Interpreter Development.Module NumPy
                    ${SKBUILD_SABI_COMPONENT} USE_SABI ${SKBUILD_SABI_VERSION})

# set(Python_SOABI ${SKBUILD_SOABI})

execute_process(COMMAND ${Python_EXECUTABLE} "--version"
                RESULT_VARIABLE _PYTHON_VERSION)
cmake_print_variables(Python_EXECUTABLE _PYTHON_VERSION SKBUILD_SOABI
                      Python_SOABI)

cmake_path(GET Python_EXECUTABLE PARENT_PATH MCKIT_ENV_BIN_DIR)
message(STATUS "bin dir: ${MCKIT_ENV_BIN_DIR}")
cmake_path(GET MCKIT_ENV_BIN_DIR PARENT_PATH MCKIT_PIXI_ENV_ROOT)
if(NOT DEFINED MCKIT_PIXI_ENV_ROOT)
  # Резервный вариант: относительный путь, если запускается локально
  set(MCKIT_PIXI_ENV_ROOT "${CMAKE_SOURCE_DIR}/.pixi/envs/default")
endif()
message(STATUS "pixi env: ${MCKIT_PIXI_ENV_ROOT}")

# Устанавливаем пути в зависимости от ОС
if(WIN32)
  # На Windows пакеты conda/pixi лежат в поддиректории Library
  set(MKL_ROOT_DIR "${MCKIT_PIXI_ENV_ROOT}/Library")
  set(MKL_INCLUDE_SEARCH_PATH "${MCKIT_PIXI_ENV_ROOT}/Library/include")
  # Добавляем Library в префикс поиска
  list(APPEND CMAKE_PREFIX_PATH "${MCKIT_PIXI_ENV_ROOT}/Library/lib")
else()
  # На Linux пути стандартные (корень окружения)
  set(MKL_ROOT_DIR "${MCKIT_PIXI_ENV_ROOT}")
  set(MKL_INCLUDE_SEARCH_PATH "${MCKIT_PIXI_ENV_ROOT}/include")
  list(APPEND CMAKE_PREFIX_PATH "${MCKIT_PIXI_ENV_ROOT}")
endif()

# Явно указываем переменные, которые ищет MKLConfig.cmake
set(MKL_INCLUDE_DIR
    "${MKL_INCLUDE_SEARCH_PATH}"
    CACHE PATH "Path to MKL headers")
set(ENV{MKLROOT} "${MKL_ROOT_DIR}")
set(ENV{MKL_INCLUDE_DIR} "${MKL_INCLUDE_SEARCH_PATH}")

# Опционально: выводим пути для отладки
message(STATUS "MKL Root: ${MKL_ROOT_DIR}")
message(STATUS "MKL Include: ${MKL_INCLUDE_DIR}")
message(STATUS "CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")

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

if(NOT Win32)
  # Fix MKL packaging bug: the issue is that libmkl_intel_thread.so lacks a
  # DT_NEEDED entry for libatomic.so.1.
  find_program(PATCHELF_EXECUTABLE patchelf)
  if(PATCHELF_EXECUTABLE)
    set(MKL_LIB_PATH "${MCKIT_PIXI_ENV_ROOT}/lib/libmkl_intel_thread.so.3")
    execute_process(COMMAND ${PATCHELF_EXECUTABLE} --add-needed libatomic.so.1
                            ${MKL_LIB_PATH} RESULT_VARIABLE PATCH_RESULT)
    if(NOT PATCH_RESULT EQUAL 0)
      message(WARNING "Failed to patch MKL library, but continuing...")
    else()
      message(STATUS "MKL library is patched...")
    endif()
  else()
    message(
      WARNING
        "patchelf not found. MKL atomic fix will not be applied automatically.")
  endif()
endif()

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
# install(TARGETS nlopt DESTINATION ${SKBUILD_PROJECT_NAME})
install(TARGETS geometry DESTINATION ${SKBUILD_PROJECT_NAME})
# copy libraries to the source tree for editable installation install(TARGETS
# nlopt DESTINATION $ENV{MCKIT_SRC}/src/mckit) install(TARGETS geometry
# DESTINATION $ENV{MCKIT_SRC}/src/mckit) install(TARGETS geometry DESTINATION
# ${CMAKE_SOURCE_DIR}/src/mckit)

include(FeatureSummary)

if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
  feature_summary(WHAT ENABLED_FEATURES DISABLED_FEATURES PACKAGES_FOUND)
  feature_summary(FILENAME ${CMAKE_CURRENT_BINARY_DIR}/features.log WHAT ALL)
endif()
