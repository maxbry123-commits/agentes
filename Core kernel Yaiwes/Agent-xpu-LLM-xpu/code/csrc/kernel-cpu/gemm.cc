#include "kernel-cpu.h"

#include <cstdint>
#include <cstring>
#include <emmintrin.h>
#include <immintrin.h>
#include <omp.h>

static constexpr int MAX_THREADS = 96;

namespace hllm {
// Matmul of two 2d matrices
// X_out = X_1 * X_2, where
// - X_1 is of shape (N, D)
// - X_2 is of shape (M, D) (mathematically, it should be (D, M))
// - X_out is of shape (N, M)
template <typename T>
static void mat_mul_2d_0_1(const T* X, const T* Y, T* t, const int N, const int D, const int M) {
    memset(reinterpret_cast<char*>(t), 0, N * M * sizeof(T));

#pragma omp parallel for collapse(2) // parallelize the outer two loops
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M; j++) {
            T sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[j * D + k];
            }
            t[i * M + j] = sum;
        }
    }
}

static void mat_mul_2d_0_1_fp32(const float* X, const float* Y, float* t, const int N, const int D,
                                const int M) {
    memset(t, 0, N * M * sizeof(float));

#if defined(__AVX512F__)
    int M_aligned = M - M % 16;
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M_aligned; j += 16) {
            __m512 sum = _mm512_setzero_ps();
            for (int k = 0; k < D; k++) {
                __m512 a = _mm512_set1_ps(X[i * D + k]);
                __m512 b = _mm512_set_ps(
                    Y[(j + 15) * D + k], Y[(j + 14) * D + k], Y[(j + 13) * D + k],
                    Y[(j + 12) * D + k], Y[(j + 11) * D + k], Y[(j + 10) * D + k],
                    Y[(j + 9) * D + k], Y[(j + 8) * D + k], Y[(j + 7) * D + k], Y[(j + 6) * D + k],
                    Y[(j + 5) * D + k], Y[(j + 4) * D + k], Y[(j + 3) * D + k], Y[(j + 2) * D + k],
                    Y[(j + 1) * D + k], Y[j * D + k]);
                sum = _mm512_fmadd_ps(a, b, sum);
            }
            _mm512_storeu_ps(&t[i * M + j], sum);
        }
    }
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = M_aligned; j < M; j++) {
            float sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[j * D + k];
            }
            t[i * M + j] = sum;
        }
    }

#elif defined(__AVX__) || defined(__AVY__)
    int M_aligned = M - M % 8;
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M_aligned; j += 8) {
            __m256 sum = _mm256_setzero_ps();
            for (int k = 0; k < D; k++) {
                __m256 a = _mm256_broadcast_ss(&X[i * D + k]);
                __m256 b = _mm256_set_ps(Y[(j + 7) * D + k], Y[(j + 6) * D + k], Y[(j + 5) * D + k],
                                         Y[(j + 4) * D + k], Y[(j + 3) * D + k], Y[(j + 2) * D + k],
                                         Y[(j + 1) * D + k], Y[j * D + k]);
                sum = _mm256_fmadd_ps(a, b, sum);
            }
            _mm256_storeu_ps(&t[i * M + j], sum);
        }
    }
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = M_aligned; j < M; j++) {
            float sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[j * D + k];
            }
            t[i * M + j] = sum;
        }
    }

#else
#pragma omp parallel for collapse(2) // parallelize the outer two loops
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M; j++) {
            float sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[j * D + k];
            }
            t[i * M + j] = sum;
        }
    }
#endif
}

// Matmul of two 2d matrices
// X_out = X_1 * X_2, where
// - X_1 is of shape (N, D)
// - X_2 is of shape (D, M)
// - X_out is of shape (N, M)
template <typename T>
static void mat_mul_2d_0_0(const T* X, const T* Y, T* t, const int N, const int D, const int M) {
    memset(reinterpret_cast<char*>(t), 0, N * M * sizeof(T));

#pragma omp parallel for collapse(2) // parallelize the outer two loops
    for (int k = 0; k < D; k++) {
        for (int i = 0; i < N; i++) {
            T Xik = X[i * D + k];
            for (int j = 0; j < M; j++) {
                t[i * M + j] += Xik * Y[k * M + j];
            }
        }
    }
}

static void mat_mul_2d_0_0_fp32(const float* X, const float* Y, float* t, const int N, const int D,
                                const int M) {
    memset(t, 0, N * M * sizeof(float));

#if defined(__AVX512F__)
    int M_aligned = M - M % 16;
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M_aligned; j += 16) {
            __m512 sum = _mm512_setzero_ps();
            for (int k = 0; k < D; k++) {
                __m512 a = _mm512_set1_ps(X[i * D + k]);
                __m512 b = _mm512_loadu_ps(&Y[k * M + j]);
                sum = _mm512_fmadd_ps(a, b, sum);
            }
            _mm512_storeu_ps(&t[i * M + j], sum);
        }
    }
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = M_aligned; j < M; j++) {
            float sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[k * M + j];
            }
            t[i * M + j] = sum;
        }
    }

#elif defined(__AVX__) || defined(__AVY__)
    int M_aligned = M - M % 8;
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M_aligned; j += 8) {
            __m256 sum = _mm256_setzero_ps();
            for (int k = 0; k < D; k++) {
                __m256 a = _mm256_broadcast_ss(&X[i * D + k]);
                __m256 b = _mm256_loadu_ps(&Y[k * M + j]);
                sum = _mm256_fmadd_ps(a, b, sum);
            }
            _mm256_storeu_ps(&t[i * M + j], sum);
        }
    }
#pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = M_aligned; j < M; j++) {
            float sum = 0;
            for (int k = 0; k < D; k++) {
                sum += X[i * D + k] * Y[k * M + j];
            }
            t[i * M + j] = sum;
        }
    }

#else
#pragma omp parallel for collapse(2) // parallelize the outer two loops
    for (int k = 0; k < D; k++) {
        for (int i = 0; i < N; i++) {
            float Xik = X[i * D + k];
            for (int j = 0; j < M; j++) {
                t[i * M + j] += Xik * Y[k * M + j];
            }
        }
    }
#endif
}

void cpu::mat_mul(__Tensor& t) {
    using opset_ns::mat_mul_options;
    mat_mul_options& options = t.options<mat_mul_options>();
    __Tensor& X = *t.src()[0].get();
    __Tensor& Y = *t.src()[1].get();
    assert(X.get_quant_type() == QuantType::none && Y.get_quant_type() == QuantType::none);

    assert(("X and Y should be 2D tensors" && X.dims() == 2 && Y.dims() == 2));
    assert(("X and Y should have the same shape at the dim" &&
            X.shape_of(!options.transposed1) == Y.shape_of((int)(options.transposed2))));

    int N = X.shape_of((int)options.transposed1);
    int D = X.shape_of(!options.transposed1);
    int M = Y.shape_of(!options.transposed2);
    auto dtype = X.dtype();
    assert(("t should be a 2D tensor" && t.dims() == 2));
    assert(
        ("t should have the shape (N, M)" && (int)t.shape_of(0) == N && (int)t.shape_of(1) == M));
    assert("t must be contiguous" && t.is_contiguous());
    __Tensor&& X__ = X.is_contiguous() ? X : X.contiguous();
    __Tensor&& Y__ = Y.is_contiguous() ? Y : Y.contiguous();

    if (dtype == Dtype::float32) {
        assert("X and Y should have the same data type" && Y.dtype() == Dtype::float32);
        if (!options.transposed1 && options.transposed2) {
            mat_mul_2d_0_1_fp32((float*)(X__.at(0)), (float*)(Y__.at(0)), (float*)(t.at(0)), N, D,
                                M);
        } else if (!options.transposed1 && !options.transposed2) {
            mat_mul_2d_0_0_fp32((float*)(X__.at(0)), (float*)(Y__.at(0)), (float*)(t.at(0)), N, D,
                                M);
        } else {
            assert(("Unsupported transposed in matmul" && false));
        }
    } else {
        assert("Unsupported data type in matmul" && false);
    }
}

} // namespace hllm