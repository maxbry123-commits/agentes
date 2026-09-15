#include "kernel-cpu.h"

#include <cstdint>

template <typename T> static void mat_scale(T* x, T* out, int size, float scale) {
#pragma omp parallel for
    for (int i = 0; i < size; i++) {
        out[i] = x[i] * scale;
    }
}

namespace hllm {

void cpu::mat_scale(__Tensor& t) {
    using opset_ns::mat_scale_options;
    auto& options = t.options<mat_scale_options>();
    __Tensor& x = *t.src()[0].get();
    assert("Unsupported datatype" && (t.dtype() == Dtype::float32 || t.dtype() == Dtype::float16));
    assert("Must be contiguous" && t.is_contiguous());

    int size = t.size();
    if (t.dtype() == Dtype::float32) {
        ::mat_scale((float*)x.at(0), (float*)t.at(0), size, options.scale);
    } else if (t.dtype() == Dtype::float16) {
        ::mat_scale((std::float16_t*)x.at(0), (std::float16_t*)t.at(0), size, options.scale);
    }
}
} // namespace hllm