add_library(end2end-ov
    backend.cc
    context.cc
)

target_link_libraries(end2end-ov PRIVATE
    end2end-base
    basic
    models
    kernel-ov
    frontend
    openvino::runtime
)