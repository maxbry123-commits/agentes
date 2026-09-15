if(BUILD_INTEL)
    # Auto-discover all entrypoint executables named run-*.cc (except run-cpu.cc)
    file(GLOB ENTRYPOINT_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/run-*.cc")
    foreach(src ${ENTRYPOINT_SOURCES})
        get_filename_component(exec_name "${src}" NAME_WE) # e.g. run-ov
        if(exec_name STREQUAL "run-cpu")
            continue()
        endif()
        add_executable(${exec_name} ${exec_name}.cc)
        target_link_libraries(${exec_name} PRIVATE
            end2end-ov
            utils
            openvino::runtime
        )
        set_target_properties(${exec_name} PROPERTIES
            RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
        )
    endforeach()
endif()

if(BUILD_CPU)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/run-cpu.cc")
        add_executable(run-cpu run-cpu.cc)
        # target_link_libraries(run-cpu PRIVATE
        #     end2end-base
        #     end2end-cpu
        # )
    endif()
endif()