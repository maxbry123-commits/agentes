#include "kernel-cpu.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <numeric>

template <typename T>
static void MHA(T* Q, T* K, T* V, T* Out, int n_heads, int prompt_len, int context_len,
                int head_size, bool mask = false) {
    T* Scores = new T[n_heads * prompt_len * context_len]{};
#pragma omp parallel for
    for (int i = 0; i < n_heads * prompt_len * head_size; i++) {
        Out[i] = 0;
    }
#pragma omp parallel for
    for (int head = 0; head < n_heads; head++) {
        for (int i = 0; i < prompt_len; i++)
            for (int j = 0; j < context_len; j++)
                for (int k = 0; k < head_size; k++) {
                    Scores[head * prompt_len * context_len + i * context_len + j] +=
                        Q[head * prompt_len * head_size + i * head_size + k] *
                        K[head * context_len * head_size + j * head_size + k];
                }
        for (int i = 0; i < prompt_len; i++)
            for (int j = 0; j < context_len; j++) {
                Scores[head * prompt_len * context_len + i * context_len + j] /=
                    static_cast<T>(std::sqrt(head_size));
                Scores[head * prompt_len * context_len + i * context_len + j] +=
                    mask && j > i ? static_cast<T>(-INFINITY) : static_cast<T>(0);
            }
        for (int i = 0; i < prompt_len; i++) {
            T max_val =
                *std::max_element(Scores + head * prompt_len * context_len + i * context_len,
                                  Scores + head * prompt_len * context_len + (i + 1) * context_len);
            for (int j = 0; j < context_len; j++) {
                Scores[head * prompt_len * context_len + i * context_len + j] =
                    static_cast<T>(std::exp(
                        Scores[head * prompt_len * context_len + i * context_len + j] - max_val));
            }
            T sum =
                std::accumulate(Scores + head * prompt_len * context_len + i * context_len,
                                Scores + head * prompt_len * context_len + (i + 1) * context_len,
                                static_cast<T>(0));
            for (int j = 0; j < context_len; j++) {
                Scores[head * prompt_len * context_len + i * context_len + j] /= sum;
            }
        }
        for (int i = 0; i < prompt_len; i++)
            for (int j = 0; j < head_size; j++) {
                for (int k = 0; k < context_len; k++) {
                    Out[head * prompt_len * head_size + i * head_size + j] +=
                        Scores[head * prompt_len * context_len + i * context_len + k] *
                        V[head * context_len * head_size + k * head_size + j];
                }
            }
    }
    delete[] Scores;
}

template <typename T>
static void GQA(T* Q, T* K, T* V, T* Out, int n_heads, int group_size, int prompt_len,
                int context_len, int head_size, bool mask = false) {
    T* Scores = new T[n_heads * prompt_len * context_len]{};
#pragma omp parallel for
    for (int i = 0; i < n_heads * prompt_len * head_size; i++) {
        Out[i] = 0;
    }
#pragma omp parallel for
    for (int head = 0; head < n_heads; head++) {
        int headKV = head / group_size;
        for (int i = 0; i < prompt_len; i++)
            for (int j = 0; j < context_len; j++)
                for (int k = 0; k < head_size; k++) {
                    Scores[head * prompt_len * context_len + i * context_len + j] +=
                        Q[head * prompt_len * head_size + i * head_size + k] *
                        K[headKV * context_len * head_size + j * head_size + k];
                }
        for (int i = 0; i < prompt_len; i++)
            for (int j = 0; j < context_len; j++) {
                Scores[head * prompt_len * context_len + i * context_len + j] /=
                    static_cast<T>(std::sqrt(head_size));
                Scores[head * prompt_len * context_len + i * context_len + j] +=
                    mask && j > i ? static_cast<T>(-INFINITY) : static_cast<T>(0);
            }
        for (int i = 0; i < prompt_len; i++) {
            T max_val =
                *std::max_element(Scores + head * prompt_len * context_len + i * context_len,
                                  Scores + head * prompt_len * context_len + (i + 1) * context_len);
            for (int j = 0; j < context_len; j++) {
                Scores[head * prompt_len * context_len + i * context_len + j] =
                    static_cast<T>(std::exp(
                        Scores[head * prompt_len * context_len + i * context_len + j] - max_val));
            }
            T sum =
                std::accumulate(Scores + head * prompt_len * context_len + i * context_len,
                                Scores + head * prompt_len * context_len + (i + 1) * context_len,
                                static_cast<T>(0));
            for (int j = 0; j < context_len; j++) {
                Scores[head * prompt_len * context_len + i * context_len + j] /= sum;
            }
        }
        for (int i = 0; i < prompt_len; i++)
            for (int j = 0; j < head_size; j++) {
                for (int k = 0; k < context_len; k++) {
                    Out[head * prompt_len * head_size + i * head_size + j] +=
                        Scores[head * prompt_len * context_len + i * context_len + k] *
                        V[headKV * context_len * head_size + k * head_size + j];
                }
            }
    }
    delete[] Scores;
}

namespace hllm {
void cpu::mha(__Tensor& t) {
    __Tensor& Q = *t.src()[0].get();
    __Tensor& K = *t.src()[1].get();
    __Tensor& V = *t.src()[2].get();
    bool mask = t.options<hllm::opset_ns::mha_options>().mask;
    assert("Q, K, V, and Out should be 3D tensors" && Q.dims() == 3 && K.dims() == 3 &&
           V.dims() == 3 && t.dims() == 3);
    assert("Only support contiguous tensors for now" && t.is_contiguous());
    assert("Only support fp32 and fp16 now" && Q.dtype() == Dtype::float32 ||
           Q.dtype() == Dtype::float16);
    assert("Dtype of Q, K, V, and Out should be the same" && Q.dtype() == K.dtype() &&
           Q.dtype() == V.dtype() && Q.dtype() == t.dtype());
    Dtype dtype = Q.dtype();
    size_t n_heads = Q.shape_of(0), prompt_len = Q.shape_of(1), head_size = Q.shape_of(2);
    assert("heads of Q must be multiple of kv_heads" && K.shape_of(0) != 0 &&
           Q.shape_of(0) % K.shape_of(0) == 0);
    size_t group_size = Q.shape_of(0) / K.shape_of(0);
    size_t context_len = K.shape_of(1);

    // float sqrt_dim = sqrt((float)head_size);

    __Tensor&& Q_ = Q.is_contiguous() ? Q : Q.contiguous();
    __Tensor&& K_ = K.is_contiguous() ? K : K.contiguous();
    __Tensor&& V_ = V.is_contiguous() ? V : V.contiguous();
    // std::cout << "Q" << Q_ << std::endl;
    // std::cout << "K" << K_ << std::endl;
    // std::cout << "V" << V_ << std::endl;

    if (dtype == Dtype::float32) {
        float* Q_data = (float*)Q_.at(0);
        float* K_data = (float*)K_.at(0);
        float* V_data = (float*)V_.at(0);
        float* Out_data = (float*)t.at(0);
        group_size == 1 ? MHA(Q_data, K_data, V_data, Out_data, n_heads, prompt_len, context_len,
                              head_size, mask)
                        : GQA(Q_data, K_data, V_data, Out_data, n_heads, group_size, prompt_len,
                              context_len, head_size, mask);
    } else if (dtype == Dtype::float16) {
        std::float16_t* Q_data = (std::float16_t*)Q_.at(0);
        std::float16_t* K_data = (std::float16_t*)K_.at(0);
        std::float16_t* V_data = (std::float16_t*)V_.at(0);
        std::float16_t* Out_data = (std::float16_t*)t.at(0);
        group_size == 1 ? MHA(Q_data, K_data, V_data, Out_data, n_heads, prompt_len, context_len,
                              head_size, mask)
                        : GQA(Q_data, K_data, V_data, Out_data, n_heads, group_size, prompt_len,
                              context_len, head_size, mask);
    }
    return;
}
} // namespace hllm