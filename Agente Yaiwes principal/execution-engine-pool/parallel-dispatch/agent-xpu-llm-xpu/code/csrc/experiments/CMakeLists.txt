if(BUILD_INTEL)
    # Auto-discover all entrypoint executables named run-*.cc (except run-cpu.cc)
    file(GLOB ENTRYPOINT_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/exp-*.cc")
    foreach(src ${ENTRYPOINT_SOURCES})
        get_filename_component(exec_name "${src}" NAME_WE) # e.g. run-ov
        add_executable(${exec_name} ${exec_name}.cc util-exp.cc)
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