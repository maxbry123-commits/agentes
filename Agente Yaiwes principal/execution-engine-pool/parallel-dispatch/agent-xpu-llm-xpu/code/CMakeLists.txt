cmake_minimum_required(VERSION 3.14)
project(LLM.xpu LANGUAGES CXX)

# Set C++ standard (C++17)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Clangd format support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if (WIN32)
    add_compile_options(/W4 /FS)
    # Windows-specific settings
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /bigobj")
    # Use static runtime for better compatibility
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
else()
    add_compile_options(-Wall -Wextra)
endif()

###
# option list
###
option(BUILD_CPU "Build on x86 CPU platforms" OFF)
option(BUILD_INTEL "Build on Intel Core Ultra platforms w/ NPU/iGPU support" ON)
option(BUILD_AMD "Build on AMD Ryzen AI platforms w/ XDNA NPU support" OFF)
option(BUIld_CUDA "Build on NVIDIA platforms w/ CUDA GPU support" OFF)

option(BUILD_TESTS "Build tests" OFF)
option(BUILD_EXAMPLES "Build examples" OFF)

option(ENABLE_MSAN "Enable Memory Sanitizer" OFF) # This conflicts with openvino, 
                                                  # see https://github.com/google/sanitizers/issues/611

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "Building in debug mode.")
    # Define a preprocessor macro for debug mode
    add_compile_definitions(DEBUG_MODE=1)
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    message(STATUS "Build in release mode.")
    add_compile_options(
        -O3         # Optimization level 3
        -march=native  # Enable all instruction subsets supported by the local machine
        # -flto=4       # Enable link-time optimization
        -funroll-loops  # Unroll loops
        -ffast-math  # Enable fast math optimizations
    )
endif()

if (BUILD_CPU)
    message(SEND_ERROR "CPU inference is still under development.")
endif()

if (BUILD_INTEL)
    add_definitions(-DBUILD_INTEL)

    find_package(OpenVINO QUIET)
    if (OpenVINO_FOUND)
        message(STATUS "Found OpenVINO. NPU/GPU support on Intel platforms will be enabled.")
        
        # Windows-specific OpenVINO configuration
        if (WIN32)
            # Ensure proper linking on Windows
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
            # Add Windows-specific OpenVINO paths if needed
            if (DEFINED ENV{INTEL_OPENVINO_DIR})
                set(OpenVINO_DIR "$ENV{INTEL_OPENVINO_DIR}/cmake")
            endif()
        endif()
      
    else()
        message(SEND_ERROR "Cannot locate OpenVINO. To enable NPU/GPU support on Intel platforms,\
        check if OpenVINO toolkit is properly installed or OpenVINO environment vars are set.")
    endif()

endif()

if(BUILD_AMD)
    message(SEND_ERROR "AMD inference is still under development.")
endif()

if(BUILD_CUDA)
    message(SEND_ERROR "CUDA inference is still under development.")
endif()

if (ENABLE_MSAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

if (BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/03597a01ee50ed33e9dfd640b249b4be3799d395.zip
    )
    # For Windows: Prevent overriding the parent project's compiler/linker settings
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
    
    enable_testing()
    add_subdirectory(tests)
endif()

include_directories(PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/csrc)
add_subdirectory(csrc)

