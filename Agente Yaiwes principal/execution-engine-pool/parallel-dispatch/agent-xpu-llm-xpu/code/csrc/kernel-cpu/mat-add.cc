#include "kernel-cpu.h"

#include <cstdint>

namespace hllm {
template <typename T> static void mat_add(T* x, T* y, T* out, size_t size) {
#pragma omp parallel for
    for (size_t i = 0; i < size; i++) {
        out[i] = x[i] + y[i];
    }
}

void cpu::mat_add(__Tensor& t) {
    __Tensor& x = *t.src()[0].get();
    __Tensor& y = *t.src()[1].get();

    // Check if the tensors have the same shape
    assert(("Tensors must have the same shape for mat_add" && x.has_same_shape(y)));
    assert("Only support contiguous tensors for now" && x.is_contiguous() && x.is_contiguous() &&
           t.is_contiguous());
    if (t.dtype() == Dtype::float32) {
        hllm::mat_add((float*)x.at(0), (float*)y.at(0), (float*)t.at(0), t.size());
    } else if (t.dtype() == Dtype::int8) {
        hllm::mat_add((int8_t*)x.at(0), (int8_t*)y.at(0), (int8_t*)t.at(0), t.size());
    } else if (t.dtype() == Dtype::float16) {
        hllm::mat_add((std::float16_t*)x.at(0), (std::float16_t*)y.at(0), (std::float16_t*)t.at(0),
                      t.size());
    } else {
        assert(("Unsupported data type for mat_add" && false));
    }
}
} // namespace hllm