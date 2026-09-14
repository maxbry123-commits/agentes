add_subdirectory(basic)
add_subdirectory(end2end)
add_subdirectory(frontend)
add_subdirectory(models)
add_subdirectory(utils)
add_subdirectory(experiments)

if(BUILD_CPU)
    add_subdirectory(kernel-cpu)
endif()

if(BUILD_INTEL)
    add_subdirectory(kernel-ov)
endif()

add_subdirectory(entrypoint)