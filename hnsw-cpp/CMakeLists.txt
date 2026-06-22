cmake_minimum_required(VERSION 3.18)
project(hnsw_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(HNSWCPP_USE_HNSWLIB "Build with hnswlib backend" ON)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
  include(FetchContent)
  FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.12.0
  )
  FetchContent_MakeAvailable(pybind11)
endif()

if(HNSWCPP_USE_HNSWLIB)
  include(FetchContent)
  FetchContent_Declare(
    hnswlib
    GIT_REPOSITORY https://github.com/nmslib/hnswlib.git
    GIT_TAG v0.8.0
  )
  FetchContent_GetProperties(hnswlib)
  if(NOT hnswlib_POPULATED)
    FetchContent_Populate(hnswlib)
  endif()
  add_library(hnswlib INTERFACE)
  target_include_directories(hnswlib INTERFACE ${hnswlib_SOURCE_DIR})
  set(HNSWLIB_AVAILABLE 1)
endif()

pybind11_add_module(hnsw_cpp src/hnsw_index.cpp src/bindings.cpp)

target_include_directories(hnsw_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(HNSWLIB_AVAILABLE)
  target_compile_definitions(hnsw_cpp PRIVATE HNSWLIB_AVAILABLE)
  target_link_libraries(hnsw_cpp PRIVATE hnswlib)
endif()

install(TARGETS hnsw_cpp DESTINATION .)
