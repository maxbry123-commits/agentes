#pragma once

#include "basic/tensor.h"

#include <optional>
#include <stdfloat>

namespace hllm {
namespace kernel_cpu {
void mat_add(__Tensor& t);
void mat_mul(__Tensor& t);
void mat_scale(__Tensor& t);
void mat_vec_mul(__Tensor& t);
void rmsnorm(__Tensor& t);
void rope(__Tensor& t);
void mha(__Tensor& t);
void silu(__Tensor& t);
void softmax(__Tensor& t);

// quantization
void mat_mul_w8a32(__Tensor& t);
void mat_vec_mul_w8a32(__Tensor& t);

/**
 * @brief Set the cpu kernel for the Tensor
 */
void set_kernel(Tensor& t);
}; // namespace kernel_cpu
} // namespace hllm