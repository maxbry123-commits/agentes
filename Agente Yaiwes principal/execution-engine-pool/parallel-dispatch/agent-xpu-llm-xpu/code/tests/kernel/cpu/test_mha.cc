#include "fp16/include/half/half.hpp"
#include "kernel/kernel.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <gtest/gtest.h>
#include <numeric>

auto cpu_kernel = hllm::get_kernel(hllm::DeviceType::CPU);

constexpr int n_heads = 7;
constexpr int prompt_len = 8;
constexpr int head_size = 9;

float Q[n_heads][prompt_len][head_size];
float K[n_heads][prompt_len][head_size];
float V[n_heads][prompt_len][head_size];
float Scores[n_heads][prompt_len][prompt_len];
float Out[n_heads][prompt_len][head_size];
constexpr int size = sizeof(Q) / sizeof(float);

using namespace hllm;

void ScaledDotProductAttentionRef() {
  for (int head = 0; head < n_heads; head++) {
    for (int i = 0; i < prompt_len; i++)
      for (int j = 0; j < prompt_len; j++)
        for (int k = 0; k < head_size; k++) {
          Scores[head][i][j] += Q[head][i][k] * K[head][j][k];
        }
    for (int i = 0; i < prompt_len; i++)
      for (int j = 0; j < prompt_len; j++) {
        Scores[head][i][j] /= sqrt(head_size);
        Scores[head][i][j] += j > i ? -INFINITY : 0;
      }
    for (int i = 0; i < prompt_len; i++) {
      float max_val =
          *std::max_element(Scores[head][i], Scores[head][i] + prompt_len);
      for (int j = 0; j < prompt_len; j++) {
        Scores[head][i][j] = exp(Scores[head][i][j] - max_val);
      }
      float sum =
          std::accumulate(Scores[head][i], Scores[head][i] + prompt_len, 0.0f);
      for (int j = 0; j < prompt_len; j++) {
        Scores[head][i][j] /= sum;
      }
    }
    for (int i = 0; i < prompt_len; i++)
      for (int j = 0; j < head_size; j++) {
        for (int k = 0; k < prompt_len; k++) {
          Out[head][i][j] += Scores[head][i][k] * V[head][k][j];
        }
      }
  }
}

TEST(ScaledDotProductAttentionTestCPU, ScaledDotProductAttention_fp32) {
  for (int i = 0; i < size; i++) {
    *((float *)Q + i) = rand() / (float)RAND_MAX;
    *((float *)K + i) = rand() / (float)RAND_MAX;
    *((float *)V + i) = rand() / (float)RAND_MAX;
  }
  memset(Out, 0, sizeof(Out));
  memset(Scores, 0, sizeof(Scores));
  ScaledDotProductAttentionRef();
  Tensor Q_t = create_tensor(Dtype::float32, {n_heads, prompt_len, head_size});
  Tensor K_t = create_tensor(Dtype::float32, {n_heads, prompt_len, head_size});
  Tensor V_t = create_tensor(Dtype::float32, {n_heads, prompt_len, head_size});
  Tensor Out_t =
      create_tensor(Dtype::float32, {n_heads, prompt_len, head_size}, ALLOC);
  Q_t.copy_data(Q);
  K_t.copy_data(K);
  V_t.copy_data(V);
  cpu_kernel->scaled_dot_product_attention(Q_t, K_t, V_t, Out_t);
  for (int i = 0; i < size; i++) {
    EXPECT_LE(
        fabs(((float *)Out)[i] - *((float *)Out_t.at(0) + i)) /
            (1 + fabs(((float *)Out)[i]) + fabs(*((float *)Out_t.at(0) + i))),
        1e-5);
  }
}

TEST(ScaledDotProductAttentionTestCPU, ScaledDotProductAttention_fp16) {
  for (int i = 0; i < size; i++) {
    *((float *)Q + i) = rand() / (float)RAND_MAX;
    *((float *)K + i) = rand() / (float)RAND_MAX;
    *((float *)V + i) = rand() / (float)RAND_MAX;
  }
  memset(Out, 0, sizeof(Out));
  memset(Scores, 0, sizeof(Scores));
  ScaledDotProductAttentionRef();
  Tensor Q_t =
      create_tensor(Dtype::float16, {n_heads, prompt_len, head_size}, ALLOC);
  Tensor K_t =
      create_tensor(Dtype::float16, {n_heads, prompt_len, head_size}, ALLOC);
  Tensor V_t =
      create_tensor(Dtype::float16, {n_heads, prompt_len, head_size}, ALLOC);
  Tensor Out_t =
      create_tensor(Dtype::float16, {n_heads, prompt_len, head_size}, ALLOC);
  for (int i = 0; i < size; i++) {
    *((half_float::half *)Q_t.at(0) + i) = *((float *)Q + i);
    *((half_float::half *)K_t.at(0) + i) = *((float *)K + i);
    *((half_float::half *)V_t.at(0) + i) = *((float *)V + i);
  }
  cpu_kernel->scaled_dot_product_attention(Q_t, K_t, V_t, Out_t);
  for (int i = 0; i < size; i++) {
    EXPECT_LE(fabs(((float *)Out)[i] - *((half_float::half *)Out_t.at(0) + i)) /
                  (0.1e-5 + fabs(((float *)Out)[i]) +
                   fabs(*((half_float::half *)Out_t.at(0) + i))),
              1e-3);
  }
}
