#include "kernel-cpu.h"

#include <cmath>
#include <cstdint>
#include <omp.h>

namespace hllm {
template <typename T> static void rmsnorm(T* input, T* weight, T* out, int size) {
    // calculate sum of squares
    T ss = static_cast<T>(0.0);
#pragma omp parallel for reduction(+ : ss)
    for (int i = 0; i < size; i++) {
        ss += input[i] * input[i];
    }
    ss /= size;
    ss += static_cast<T>(1e-5);
    ss = static_cast<T>(1.0) / static_cast<T>(std::sqrt(ss));
// normalize and scale
#pragma omp parallel for
    for (int i = 0; i < size; i++) {
        out[i] = weight[i] * (ss * input[i]);
    }
}

void cpu::rmsnorm(__Tensor& t) {
    __Tensor& input = *t.src()[0].get();
    __Tensor& weight = *t.src()[1].get();
    assert("Input tensor must be 1D or 2D" && (input.dims() == 1 || input.dims() == 2));
    assert(("Weight tensor must be 1D" && weight.dims() == 1));
    int size = input.dims() == 1 ? input.shape_of(0) : input.shape_of(1);
    assert(("Weight tensor must have the same size as input last dim" &&
            (int)weight.shape_of(0) == size));
    assert(("Output tensor must have the same shape as input" && input.has_same_shape(t)));
    auto dtype = input.dtype();
    assert(("Weight and input should have the same data type" && weight.dtype() == dtype));
    assert("Only support contiguous tensors for now" && input.is_contiguous() &&
           weight.is_contiguous() && t.is_contiguous());

    if (dtype == Dtype::float32) {
        if (input.dims() == 1) {
            hllm::rmsnorm<float>((float*)(input.at(0)), (float*)(weight.at(0)), (float*)(t.at(0)),
                                 size);
        } else if (input.dims() == 2) {
            auto input_data = (float*)(input.at(0));
            auto weight_data = (float*)(weight.at(0));
            auto out_data = (float*)(t.at(0));

#pragma omp parallel for
            for (int i = 0; i < (int)input.shape_of(0); i++) {
                hllm::rmsnorm<float>(input_data + i * size, weight_data, out_data + i * size, size);
            }
        }
    } else if (dtype == Dtype::int8) {
        if (input.dims() == 1) {
            hllm::rmsnorm<int8_t>((int8_t*)(input.at(0)), (int8_t*)(weight.at(0)),
                                  (int8_t*)(t.at(0)), size);
        } else if (input.dims() == 2) {
            auto input_data = (int8_t*)(input.at(0));
            auto weight_data = (int8_t*)(weight.at(0));
            auto out_data = (int8_t*)(t.at(0));

#pragma omp parallel for
            for (int i = 0; i < (int)input.shape_of(0); i++) {
                hllm::rmsnorm<int8_t>(input_data + i * size, weight_data, out_data + i * size,
                                      size);
            }
        }
    } else if (dtype == Dtype::float16) {
        if (input.dims() == 1) {
            hllm::rmsnorm<std::float16_t>((std::float16_t*)(input.at(0)),
                                          (std::float16_t*)(weight.at(0)),
                                          (std::float16_t*)(t.at(0)), size);
        } else if (input.dims() == 2) {
            auto input_data = (std::float16_t*)(input.at(0));
            auto weight_data = (std::float16_t*)(weight.at(0));
            auto out_data = (std::float16_t*)(t.at(0));
#pragma omp parallel for
            for (int i = 0; i < (int)input.shape_of(0); i++) {
                hllm::rmsnorm<std::float16_t>(input_data + i * size, weight_data,
                                              out_data + i * size, size);
            }
        }
    } else {
        assert(("Unsupported data type for RMSNorm" && false));
    }
}

} // namespace hllm