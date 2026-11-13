cmake_minimum_required(VERSION 3.10.0)
project(main VERSION 0.1.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
find_package(OpenVINO REQUIRED)

add_executable(pure_attn pure_attn.cpp)

target_link_libraries(pure_attn PRIVATE
    openvino::runtime
)

add_executable(real_attn real_attn.cpp)

target_link_libraries(real_attn PRIVATE
    openvino::runtime
)