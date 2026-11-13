#include "kernel/kernel.h"
#include <gtest/gtest.h>

using namespace hllm;
auto static cpu_kernel = get_kernel(hllm::DeviceType::CPU);

constexpr size_t dims[] = {8, 9, 10, 11};
constexpr size_t size = dims[0] * dims[1] * dims[2] * dims[3];
float mat[size];
float mat_ref[size];

void transpose_ref_1_3() {
  for (int i = 0; i < (int)dims[0]; ++i) {
    for (int j = 0; j < (int)dims[3]; ++j) {
      for (int k = 0; k < (int)dims[2]; ++k) {
        for (int l = 0; l < (int)dims[1]; ++l) {
          mat_ref[i * dims[1] * dims[2] * dims[3] + j * dims[1] * dims[2] +
                  k * dims[1] + l] =
              mat[i * dims[3] * dims[2] * dims[1] + l * dims[3] * dims[2] +
                  k * dims[3] + j];
        }
      }
    }
  }
}

TEST(TransposeTestCPU, Transpose) {
  for (int i = 0; i < (int)size; i++) {
    mat[i] = i;
  }
  transpose_ref_1_3();
  auto t = create_tensor(Dtype::float32, {dims[0], dims[1], dims[2], dims[3]});
  t.copy_data(mat);
  cpu_kernel->transpose(t, 1, 3);
  t = t.contiguous();
  for (int i = 0; i < (int)size; i++) {
    EXPECT_EQ(mat_ref[i], *((float *)t.at(0) + i));
  }
}