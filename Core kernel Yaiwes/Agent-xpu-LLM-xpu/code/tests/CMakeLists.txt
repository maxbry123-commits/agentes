include_directories(${CMAKE_SOURCE_DIR}/src)
include(GoogleTest)

macro(add_gtest TARGET)
  add_executable(${TARGET} ${TARGET}.cc)
  target_link_libraries(${TARGET} PRIVATE ${ARGN} GTest::gtest_main)
  gtest_discover_tests(${TARGET})
endmacro()

add_gtest(test-sampler module)
add_gtest(test-tokenizer module)
add_gtest(test-tensor basic)
add_gtest(test-load-model model)
add_gtest(test-logger util)

add_subdirectory(kernel)
add_subdirectory(end2end)
