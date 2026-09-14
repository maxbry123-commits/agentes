#include "kernel-cpu.h"

#include <cmath>

namespace hllm {
template <typename T> static void silu(T* w1x, T* w3x, T* out, int size) {
    for (int i = 0; i < size; i++) {
        T val = w1x[i];
        // silu(x) = x * sigmoid(x)
        val *= T(1.0f / (1.0f + expf(-val)));
        // element-wise multiply with w3(x)
        val *= w3x[i];
        out[i] = val;
    }
}

// SwiGLU activation function
// SwiGLU(x) = w1(x) * sigmoid(w1(x)) * w3(x), where * is element-wise
// multiplication for 2D tensors, silu is applied along the last dimension
void cpu::silu(__Tensor& t) {
    __Tensor& w1x = *t.src()[0].get();
    __Tensor& w3x = *t.src()[1].get();
    assert(("Silu input and output tensors should have the same shape" && w1x.has_same_shape(w3x) &&
            w1x.has_same_shape(t)));
    auto dtype = w1x.dtype();
    assert(
        ("all tensors should have the same dtype" && dtype == w3x.dtype() && dtype == t.dtype()));
    auto size = w1x.size();
    assert("Only support contiguous tensors for now" && w1x.is_contiguous() &&
           w3x.is_contiguous() && t.is_contiguous());
    if (dtype == Dtype::float32) {
        hllm::silu<float>((float*)w1x.at(0), (float*)w3x.at(0), (float*)t.at(0), size);
    } else if (dtype == Dtype::int8) {
        hllm::silu<int8_t>((int8_t*)w1x.at(0), (int8_t*)w3x.at(0), (int8_t*)t.at(0), size);
    } else if (dtype == Dtype::float16) {
        hllm::silu<std::float16_t>((std::float16_t*)w1x.at(0), (std::float16_t*)w3x.at(0),
                                   (std::float16_t*)t.at(0), size);
    } else {
        assert(("Unsupported data type for silu" && false));
    }
}
} // namespace hllm