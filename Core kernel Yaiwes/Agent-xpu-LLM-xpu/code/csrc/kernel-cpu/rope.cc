#include "kernel-cpu.h"

#include <assert.h>
#include <cmath>

namespace hllm {

template <typename T>
void static rope(T* x, T* out, int pos, int dim, int n_heads, std::optional<Tensor> freqs_cis) {
    assert((dim % n_heads) == 0);
    int head_size = dim / n_heads;

    if (freqs_cis.has_value()) {
        assert((int)freqs_cis.value().get()->shape_of(1) == head_size / 2);
        auto freqs_cis_tensor = freqs_cis.value().get();

#pragma omp parallel for
        for (int i = 0; i < dim; i += 2) {
            int head_dim = i % head_size;
            float fcr = *(float*)freqs_cis_tensor->at(pos, head_dim / 2, 0);
            float fci = *(float*)freqs_cis_tensor->at(pos, head_dim / 2, 1);
            T x0 = x[i];
            T x1 = x[i + 1];
            out[i] = T(x0 * fcr - x1 * fci);
            out[i + 1] = T(x0 * fci + x1 * fcr);
        }
    } else {
#pragma omp parallel for
        for (int i = 0; i < dim; i += 2) {
            float fcr, fci;
            int head_dim = i % head_size;
            float freq = 1.0 / powf(10000.0, head_dim / (float)head_size);
            fcr = cosf(pos * freq);
            fci = sinf(pos * freq);
            T x0 = x[i];
            T x1 = x[i + 1];
            out[i] = T(x0 * fcr - x1 * fci);
            out[i + 1] = T(x0 * fci + x1 * fcr);
        }
    }
}

void cpu::rope(__Tensor& t) {
    using opset_ns::rope_options;
    // if(t.debug_id == 2)
    // {
    //   std::cout << "stop" << std::endl;
    // }
    auto& options = t.options<rope_options>();
    if (options.inplace) {
        t.set_data(*t.src()[0].get());
        t.set_offset(t.src()[0]->offset());
    }
    int pos = options.pos;
    int n_heads = options.n_heads;
    auto freqs_cis = options.freqs_cis;
    __Tensor& X = *t.src()[0].get();
    assert("Only support contiguous tensors for now" && X.is_contiguous());
    if (X.dtype() == Dtype::float32) {
        if (X.dims() == 1) {
            int dim = X.shape_of(0);
            hllm::rope((float*)X.at(0), (float*)t.at(0), pos, dim, n_heads, freqs_cis);
        } else if (X.dims() == 2) {
            int dim = X.shape_of(1);
            for (int i = 0; i < (int)X.shape_of(0); i++) {
                hllm::rope((float*)X.at(i, 0), (float*)t.at(i, 0), i, dim, n_heads, freqs_cis);
            }
        } else {
            assert(("Invalid tensor dimension for rope" && false));
        }
    } else if (X.dtype() == Dtype::float16) {
        if (X.dims() == 1) {
            int dim = X.shape_of(0);
            hllm::rope((std::float16_t*)X.at(0), (std::float16_t*)t.at(0), pos, dim, n_heads,
                       freqs_cis);
        } else if (X.dims() == 2) {
            int dim = X.shape_of(1);
            for (int i = 0; i < (int)X.shape_of(0); i++) {
                hllm::rope((std::float16_t*)X.at(i, 0), (std::float16_t*)t.at(0), i, dim, n_heads,
                           freqs_cis);
            }
        } else {
            assert(("Invalid tensor dimension for rope" && false));
        }
    } else {
        assert(("Unsupported data type" && false));
    }
}
} // namespace hllm