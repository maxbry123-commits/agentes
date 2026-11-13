cmake_minimum_required(VERSION 3.14)
project(intel_profile LANGUAGES CXX)

# Set C++ standard (C++20)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)

find_package(OpenVINO REQUIRED)

link_libraries(openvino::runtime)

# add_executable(mm mm.cc)
add_executable(attn util.cc attn.cc)
add_executable(pre_attn pre_attn.cc util.cc)
add_executable(post_attn post_attn.cc util.cc)