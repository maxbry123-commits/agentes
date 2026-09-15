cmake_minimum_required(VERSION 3.14)
project(intel_profile LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)

find_package(OpenVINO REQUIRED)

link_libraries(openvino::runtime)

add_executable(mm_cont contention/both_mm.cc util.cc)
add_executable(mm_cont_fused contention/both_mm_fused.cc util.cc)
add_executable(mm_cont_dist contention/both_mm_dist.cc util.cc)
add_executable(mm_cont_colocate contention/both_mm_colocate.cc util.cc)
add_executable(attn_decode_batch op_profile/attn_decode_batch.cc util.cc)