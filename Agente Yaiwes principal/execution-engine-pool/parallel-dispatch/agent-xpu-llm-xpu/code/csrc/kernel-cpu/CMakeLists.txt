add_library(kernel-cpu
    kernel-cpu.cc
    gemm.cc
    gemm-w8a32.cc
    gemv.cc
    gemv-w8a32.cc
    mat-add.cc
    mat-scale.cc
    mha.cc
    rmsnorm.cc
    rope.cc
    silu.cc
    softmax.cc
)

target_link_libraries(kernel-cpu PRIVATE basic OpenMP::OpenMP_CXX)
if (WIN32)
    target_compile_options(kernel-cpu PRIVATE $<$<CXX_COMPILER_ID:MSVC>:/openmp:llvm>)
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(kernel-cpu PRIVATE -march=native)
elseif(MSVC)
    target_compile_options(kernel-cpu PRIVATE /arch:AVX /arch:AVX2 /arch:AVX512)
endif()