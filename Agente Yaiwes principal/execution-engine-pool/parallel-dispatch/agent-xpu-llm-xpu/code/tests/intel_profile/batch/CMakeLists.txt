cmake_minimum_required(VERSION 3.14)
project(intel_profile LANGUAGES CXX)

# Set C++ standard (C++20)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)

find_package(OpenMP REQUIRED)
find_package(OpenVINO REQUIRED)

find_library(MATH_LIB m)

link_libraries(OpenMP::OpenMP_CXX openvino::runtime ${MATH_LIB})
add_executable(batch batch.cpp)
add_executable(batch_dyn batch_dyn.cpp)
add_executable(batch_prefill_decode batch_prefill_decode.cpp)