#include "kernel-cpu.h"

#include <cstdint>
#include <emmintrin.h>
#include <immintrin.h>
#include <omp.h>

static void __mat_vec_mul(const int8_t* W, const float* x, float* Xout, const int N, const int d,
                          float scaler) {
#pragma omp parallel for
    for (int i = 0; i < N; i++) {
        float sum = 0;
        for (int j = 0; j < d; j++) {
            sum += W[i * d + j] * x[j];
        }
        Xout[i] = sum * scaler;
    }
}

void hllm::cpu::mat_vec_mul_w8a32(__Tensor& t) {
    __Tensor& W = *t.src()[0].get();
    __Tensor& x = *t.src()[1].get();
    assert(W.get_quant_type() == QuantType::w8a32);
    assert(x.get_quant_type() == QuantType::none);
    assert(W.dims() == 2 && x.dims() == 1);
    assert(W.shape_of(1) == x.shape_of(0));
    assert(W.is_contiguous() && x.is_contiguous() && "Only support contiguous tensors for now");
    assert(W.dtype() == Dtype::int8 && x.dtype() == Dtype::float32);
    assert(W.get_group_size() == W.size() && "Only support layerwise quantization");
    auto dtype = x.dtype();
    float scaler = W.get_scales()[0];
    __mat_vec_mul(reinterpret_cast<const int8_t*>(W.at(0)), reinterpret_cast<const float*>(x.at(0)),
                  reinterpret_cast<float*>(t.at(0)), W.shape_of(0), W.shape_of(1), scaler);
}
