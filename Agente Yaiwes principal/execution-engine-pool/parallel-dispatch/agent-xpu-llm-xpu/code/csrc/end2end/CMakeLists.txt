add_library(end2end-base
    infer-job.cc
)

target_link_libraries(end2end-base PRIVATE
    basic
)

if(BUILD_INTEL)
    add_subdirectory(ov)
endif()

if(BUILD_CPU)
    add_subdirectory(cpu)
endif()