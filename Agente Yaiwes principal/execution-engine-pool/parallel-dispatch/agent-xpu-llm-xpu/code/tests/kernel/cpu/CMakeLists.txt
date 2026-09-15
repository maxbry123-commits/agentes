macro(add_test_target TEST_TARGET)
  add_executable(${TEST_TARGET} ${TEST_TARGET}.cc)
  target_link_libraries(${TEST_TARGET} PRIVATE ${KERNEL_LIBS}
  basic GTest::gtest_main ${ARGN})
  gtest_discover_tests(${TEST_TARGET})
endmacro()

add_test_target(test-rope model util)
add_test_target(test-mat-mul)
add_test_target(test-transpose)
add_test_target(test-scaled_dot_product_attention)