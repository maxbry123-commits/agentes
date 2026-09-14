#include "kernel-cpu.h"

#include <cstdint>
#include <emmintrin.h>
#include <immintrin.h>
#include <omp.h>

static constexpr int MAX_THREADS = 96;

template <typename T>
static void mat_vec_mul(const T* W, const T* x, T* Xout, const int N, const int d) {
    memset(reinterpret_cast<char*>(Xout), 0, N * sizeof(T));
#pragma omp parallel for
    for (int i = 0; i < N; i++) {
        T sum = 0;
        for (int j = 0; j < d; j++) {
            sum += W[i * d + j] * x[j];
        }
        Xout[i] = sum;
    }
}

namespace hllm {

void cpu::mat_vec_mul(__Tensor& t) {
    __Tensor& W = *t.src()[0].get();
    __Tensor& x = *t.src()[1].get();
    assert(W.get_quant_type() == QuantType::none && x.get_quant_type() == QuantType::none);

    assert(("W should be a 2D tensor" && W.dims() == 2));
    assert(("x should be a 1D tensor" && x.dims() == 1));
    assert(("W and x should have the same data type" && W.dtype() == x.dtype()));
    assert(("W and x should have the same shape at dim 1" && W.shape_of(1) == x.shape_of(0)));
    int N = W.shape_of(0);
    int d = W.shape_of(1);
    auto dtype = W.dtype();
    assert(("Xout should be a 1D tensor" && t.dims() == 1));
    assert(("Xout should have the shape (N,)" && (int)t.shape_of(0) == N));
    assert("Xout should be contiguous" && t.is_contiguous());

    __Tensor&& W__ = W.is_contiguous() ? W : W.contiguous();
    __Tensor&& x__ = W.is_contiguous() ? x : x.contiguous();
    if (dtype == Dtype::float32) {
        ::mat_vec_mul<float>((float*)(W__.at(0)), (float*)(x__.at(0)), (float*)(t.at(0)), N, d);
    } else if (dtype == Dtype::float16) {
        ::mat_vec_mul<std::float16_t>((std::float16_t*)(W__.at(0)), (std::float16_t*)(x__.at(0)),
                                      (std::float16_t*)(t.at(0)), N, d);
    } else {
        assert(("Unsupported data type in matvecmul" && false));
    }
}
} // namespace hllm