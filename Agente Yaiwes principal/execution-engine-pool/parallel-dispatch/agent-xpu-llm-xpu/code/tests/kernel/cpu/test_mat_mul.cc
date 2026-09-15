#include "fp16/include/half/half.hpp"
#include "kernel/kernel.h"
#include <gtest/gtest.h>

using namespace hllm;

static auto cpu_kernel = get_kernel(hllm::DeviceType::CPU);

void mat_mul_2d_ref_0_1(const float *X1, const float *X2, float *Xout,
                        const int N, const int D, const int M) {
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < M; j++) {
      float sum = 0;
      for (int k = 0; k < D; k++) {
        sum += X1[i * D + k] * X2[j * D + k];
      }
      Xout[i * M + j] = sum;
    }
  }
}

void mat_mul_2d_ref_0_0(const float *X1, const float *X2, float *Xout,
                        const int N, const int D, const int M) {
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < M; j++) {
      float sum = 0;
      for (int k = 0; k < D; k++) {
        sum += X1[i * D + k] * X2[k * M + j];
      }
      Xout[i * M + j] = sum;
    }
  }
}

TEST(MatMulTestCPU, MatMul2D_0_1) {
  int N = 139;
  int D = 140;
  int M = 141;
  float *X1 = new float[N * D];
  float *X2 = new float[M * D];
  float *Xout_ref = new float[N * M];
  for (int i = 0; i < N * D; i++) {
    X1[i] = (float)rand() / RAND_MAX;
  }
  for (int i = 0; i < M * D; i++) {
    X2[i] = (float)rand() / RAND_MAX;
  }
  mat_mul_2d_ref_0_1(X1, X2, Xout_ref, N, D, M);

  // Test float32
  Tensor X1_tensor = create_tensor(Dtype::float32, {(size_t)N, (size_t)D});
  Tensor X2_tensor = create_tensor(Dtype::float32, {(size_t)M, (size_t)D});
  X1_tensor.copy_data(X1);
  X2_tensor.copy_data(X2);
  Tensor Xout_tensor =
      create_tensor(Dtype::float32, {(size_t)N, (size_t)M}, hllm::ALLOC);
  cpu_kernel->mat_mul(X1_tensor, X2_tensor, Xout_tensor, 32, false, true);

  for (int i = 0; i < N * M; i++) {
    EXPECT_LE(abs(*(float *)Xout_tensor.at(i / M, i % M) - Xout_ref[i]) /
                  (1 + abs(*(float *)Xout_tensor.at(i / M, i % M)) +
                   abs(Xout_ref[i])),
              1e-4);
  }

  // Test float16
  Tensor X1_tensor_fp16 =
      create_tensor(Dtype::float16, {(size_t)N, (size_t)D}, hllm::ALLOC);
  Tensor X2_tensor_fp16 =
      create_tensor(Dtype::float16, {(size_t)M, (size_t)D}, hllm::ALLOC);
  for (int i = 0; i < N * D; i++) {
    half_float::half val = X1[i];
    *((half_float::half *)X1_tensor_fp16.get_data() + i) = val;
  }
  for (int i = 0; i < M * D; i++) {
    half_float::half val = X2[i];
    *((half_float::half *)X2_tensor_fp16.get_data() + i) = val;
  }
  Tensor Xout_tensor_fp16 =
      create_tensor(Dtype::float16, {(size_t)N, (size_t)M}, hllm::ALLOC);
  cpu_kernel->mat_mul(X1_tensor_fp16, X2_tensor_fp16, Xout_tensor_fp16, 32,
                      false, true);
  for (int i = 0; i < N * M; i++) {
    EXPECT_LE(abs(*(half_float::half *)Xout_tensor_fp16.at(i / M, i % M) -
                  Xout_ref[i]) /
                  (1 +
                   abs(*(half_float::half *)Xout_tensor_fp16.at(i / M, i % M)) +
                   abs(Xout_ref[i])),
              1e-3);
  }

  delete[] X1;
  delete[] X2;
  delete[] Xout_ref;
}

TEST(MatMulTestCPU, MatMul2D_0_0) {
  int N = 139;
  int D = 140;
  int M = 141;
  float *X1 = new float[N * D];
  float *X2 = new float[M * D];
  float *Xout_ref = new float[N * M];
  for (int i = 0; i < N * D; i++) {
    X1[i] = (float)rand() / RAND_MAX;
  }
  for (int i = 0; i < M * D; i++) {
    X2[i] = (float)rand() / RAND_MAX;
  }
  mat_mul_2d_ref_0_0(X1, X2, Xout_ref, N, D, M);

  // Test float32
  Tensor X1_tensor_fp32 = create_tensor(Dtype::float32, {(size_t)N, (size_t)D});
  Tensor X2_tensor_fp32 = create_tensor(Dtype::float32, {(size_t)D, (size_t)M});
  X1_tensor_fp32.copy_data(X1);
  X2_tensor_fp32.copy_data(X2);
  Tensor Xout_tensor =
      create_tensor(Dtype::float32, {(size_t)N, (size_t)M}, hllm::ALLOC);
  cpu_kernel->mat_mul(X1_tensor_fp32, X2_tensor_fp32, Xout_tensor, 32, false,
                      false);
  for (int i = 0; i < N * M; i++) {
    EXPECT_LE(abs(*(float *)Xout_tensor.at(i / M, i % M) - Xout_ref[i]) /
                  (1 + abs(*(float *)Xout_tensor.at(i / M, i % M)) +
                   abs(Xout_ref[i])),
              1e-4);
  }

  // Test float16
  Tensor X1_tensor_fp16 =
      create_tensor(Dtype::float16, {(size_t)N, (size_t)D}, hllm::ALLOC);
  Tensor X2_tensor_fp16 =
      create_tensor(Dtype::float16, {(size_t)D, (size_t)M}, hllm::ALLOC);
  for (int i = 0; i < N * D; i++) {
    half_float::half val = X1[i];
    *((half_float::half *)X1_tensor_fp16.get_data() + i) = val;
  }
  for (int i = 0; i < M * D; i++) {
    half_float::half val = X2[i];
    *((half_float::half *)X2_tensor_fp16.get_data() + i) = val;
  }
  Tensor Xout_tensor_fp16 =
      create_tensor(Dtype::float16, {(size_t)N, (size_t)M}, hllm::ALLOC);
  cpu_kernel->mat_mul(X1_tensor_fp16, X2_tensor_fp16, Xout_tensor_fp16, 32,
                      false, false);
  for (int i = 0; i < N * M; i++) {
    EXPECT_LE(abs(*(half_float::half *)Xout_tensor_fp16.at(i / M, i % M) -
                  Xout_ref[i]) /
                  (1 +
                   abs(*(half_float::half *)Xout_tensor_fp16.at(i / M, i % M)) +
                   abs(Xout_ref[i])),
              1e-3);
  }
  delete[] X1;
  delete[] X2;
  delete[] Xout_ref;
}