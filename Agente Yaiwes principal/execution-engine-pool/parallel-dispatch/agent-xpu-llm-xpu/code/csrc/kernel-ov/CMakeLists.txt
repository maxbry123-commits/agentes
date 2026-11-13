add_library(kernel-ov
    llama-attn.cc
    llama-final-output.cc
    llama-layer.cc
    llama-post-attn.cc
    llama-pre-attn.cc
)

target_link_libraries(kernel-ov PRIVATE
    basic
    openvino::runtime
)