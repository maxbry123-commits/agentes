#include "kernel-cpu.h"

#include <cstdint>
#include <cstring>
#include <emmintrin.h>
#include <immintrin.h>
#include <omp.h>

static constexpr int MAX_THREADS = 96;

static void mat_mul_2d_0_1(const float* X, const int8_t* Y, float* t, const int N, const int D,
                           const int M, float scaler) {
#pragma omp parallel for collapse(2) // parallelize the outer two loops
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M; j++) {
            float sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[j * D + k];
            }
            t[i * M + j] = sum * scaler;
        }
    }
}

void hllm::cpu::mat_mul_w8a32(__Tensor& t) {
    __Tensor& X = *t.src()[0].get();
    __Tensor& W = *t.src()[1].get();
    assert(X.get_quant_type() == QuantType::none && W.get_quant_type() == QuantType::w8a32);

    assert(("X and Y should be 2D tensors" && X.dims() == 2 && W.dims() == 2));
    assert(W.get_group_size() == W.size() && "Only support layerwise quantization");
    assert(X.is_contiguous() && W.is_contiguous() && "Only support contiguous tensors for now");
    auto dtype = X.dtype();
    float scaler = W.get_scales()[0];

    if (dtype == Dtype::float32) {
        mat_mul_2d_0_1(reinterpret_cast<const float*>(X.at(0)),
                       reinterpret_cast<const int8_t*>(W.at(0)), reinterpret_cast<float*>(t.at(0)),
                       X.shape_of(0), X.shape_of(1), W.shape_of(0), scaler);

    } else {
        assert(("Unsupported transposed in matmul" && false));
    }
}
