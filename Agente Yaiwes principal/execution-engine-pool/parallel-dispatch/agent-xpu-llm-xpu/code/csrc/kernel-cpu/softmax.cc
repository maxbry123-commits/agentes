#include "kernel-cpu.h"

#include <algorithm>
#include <cmath>

#define SOFTMAX(data, out, x)                                                                      \
    do {                                                                                           \
        if (t.dims() == 1) {                                                                       \
            hllm::softmax(data, out, t.shape_of(0));                                               \
        } else if (t.dims() == 2) {                                                                \
            for (int i = 0; i < (int)t.shape_of(0); i++) {                                         \
                hllm::softmax(data + i * t.shape_of(1), out + i * t.shape_of(1), t.shape_of(1));   \
            }                                                                                      \
        } else if (t.dims() == 3) {                                                                \
            for (int i = 0; i < (int)t.shape_of(0); i++) {                                         \
                for (int j = 0; j < (int)t.shape_of(1); j++) {                                     \
                    hllm::softmax(data + i * t.shape_of(1) * t.shape_of(2) + j * t.shape_of(2),    \
                                  out + i * t.shape_of(1) * t.shape_of(2) + j * t.shape_of(2),     \
                                  t.shape_of(2));                                                  \
                }                                                                                  \
            }                                                                                      \
        }                                                                                          \
    } while (0)

namespace hllm {
// Softmax for a 1D array
template <typename T> static void softmax(T* x, T* out, int size) {
    // find max value (for numerical stability)
    T max_val = x[0];
#pragma omp parallel
    {
        T local_max = max_val;
#pragma omp for
        for (int i = 1; i < size; i++) {
            local_max = std::max(local_max, x[i]);
        }
#pragma omp critical
        { max_val = std::max(max_val, local_max); }
    }
    // exp and sum
    float sum{};
#pragma omp parallel for reduction(+ : sum)
    for (int i = 0; i < size; i++) {
        float val = expf(x[i] - max_val);
        out[i] = T(val);
        sum += val;
    }
// normalize
#pragma omp parallel for
    for (int i = 0; i < size; i++) {
        out[i] /= T(sum);
    }
}

// Softmax for a 1D/2D/3D tensor (inplace),
// the last dimension is the softmax dimension
void cpu::softmax(__Tensor& t) {
    __Tensor& x = *t.src()[0].get();
    assert(("Tensor must <= 3D for softmax" && x.dims() <= 3));
    assert(("Tensor must be float32 or fp16 for softmax on CPU" &&
            (x.dtype() == Dtype::float32 || x.dtype() == Dtype::float16)));
    assert("Only support contiguous tensors for now" && x.is_contiguous());
    if (t.dtype() == Dtype::float32) {
        float* data = (float*)x.at(0);
        float* out = (float*)t.at(0);
        SOFTMAX(data, out, x);
    } else if (t.dtype() == Dtype::float16) {
        std::float16_t* data = (std::float16_t*)x.at(0);
        std::float16_t* out = (std::float16_t*)t.at(0);
        SOFTMAX(data, out, x);
    }
}

} // namespace hllm