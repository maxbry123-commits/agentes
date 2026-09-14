add_library(models
    llama.cc
    models.cc
)

target_link_libraries(models PRIVATE
    basic
)