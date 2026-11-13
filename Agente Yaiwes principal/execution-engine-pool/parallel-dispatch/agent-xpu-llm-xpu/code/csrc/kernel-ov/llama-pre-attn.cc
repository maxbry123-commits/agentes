#include "basic/memory-block.h"
#include "kernel-ov.h"

namespace hllm {
namespace ov_kernel {

std::shared_ptr<ov::Model>
get_pre_attn_w8_model(ov::element::Type a_dtype_ov, const int input_shape, const size_t dim,
                      const size_t n_heads, const size_t n_kv_heads, const char* attn_wq_weight_ptr,
                      const char* attn_wk_weight_ptr, const char* attn_wv_weight_ptr,
                      const char* attn_rms_weight_ptr, const float attn_wq_scale,
                      const float attn_wk_scale, const float attn_wv_scale) {

    const size_t head_dim = dim / n_heads;
    const size_t kv_dim = head_dim * n_kv_heads;

    // Define the input parameters
    std::shared_ptr<ov::opset15::Parameter> prompt_embedding;
    if (input_shape < 0) {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    } else {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(input_shape), dim});
    }

    auto params = ov::ParameterVector{prompt_embedding};

    // Bind ov constants with weight pointers
    auto attn_rms_weight =
        std::make_shared<ov::opset15::Constant>(a_dtype_ov, ov::Shape{dim}, attn_rms_weight_ptr);

    auto attn_wq_w8 = std::make_shared<ov::opset15::Constant>(ov::element::i8, ov::Shape{dim, dim},
                                                              attn_wq_weight_ptr);
    auto attn_wq = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(attn_wq_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {attn_wq_scale}));
    auto attn_wk_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{kv_dim, dim}, attn_wk_weight_ptr);
    auto attn_wk = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(attn_wk_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {attn_wk_scale}));
    auto attn_wv_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{kv_dim, dim}, attn_wv_weight_ptr);
    auto attn_wv = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(attn_wv_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {attn_wv_scale}));

    std::shared_ptr<ov::opset15::Multiply> prompt_norm;

    // RMSnorm
    {
        auto x = prompt_embedding;
        auto w = attn_rms_weight;

        // 1. Input Scaling for Numerical Stability
        auto reduce_axes = ov::opset15::Constant::create(ov::element::i64, {1}, {-1});

        // Calculate scaling factor to prevent underflow
        auto abs_x = std::make_shared<ov::opset15::Abs>(x);
        auto max_abs = std::make_shared<ov::opset15::ReduceMax>(abs_x, reduce_axes, true);
        auto safety_eps = ov::opset15::Constant::create(a_dtype_ov, {}, {1e-12f});
        auto alpha = std::make_shared<ov::opset15::Divide>(
            ov::opset15::Constant::create(a_dtype_ov, {}, {1.0f}),
            std::make_shared<ov::opset15::Maximum>(max_abs, safety_eps));

        // 2. Scaled Computations
        auto x_scaled = std::make_shared<ov::opset15::Multiply>(x, alpha);
        auto x_sq = std::make_shared<ov::opset15::Multiply>(x_scaled, x_scaled);

        // 3. Mean Square Calculation
        auto sum_sq = std::make_shared<ov::opset15::ReduceSum>(x_sq, reduce_axes, true);
        auto mean_sq = std::make_shared<ov::opset15::Divide>(
            sum_sq, ov::opset15::Constant::create(a_dtype_ov, {}, {static_cast<float>(dim)}));

        // 4. Adjusted Epsilon Handling
        auto eps = ov::opset15::Constant::create(a_dtype_ov, {}, {1e-5f});
        auto scaled_eps = std::make_shared<ov::opset15::Multiply>(
            eps, std::make_shared<ov::opset15::Multiply>(alpha, alpha));

        // 5. RMS Normalization
        auto rms = std::make_shared<ov::opset15::Sqrt>(
            std::make_shared<ov::opset15::Add>(mean_sq, scaled_eps));
        auto normalized = std::make_shared<ov::opset15::Divide>(x_scaled, rms);

        // 6. Weight Application
        prompt_norm = std::make_shared<ov::opset15::Multiply>(normalized, w);
    }

    // QKV Generation
    auto Q = std::make_shared<ov::opset15::MatMul>(prompt_norm, attn_wq, false, true);
    auto K = std::make_shared<ov::opset15::MatMul>(prompt_norm, attn_wk, false, true);
    auto V = std::make_shared<ov::opset15::MatMul>(prompt_norm, attn_wv, false, true);
    auto Q_res = std::make_shared<ov::opset15::Result>(Q);
    auto K_res = std::make_shared<ov::opset15::Result>(K);
    auto V_res = std::make_shared<ov::opset15::Result>(V);

    auto model = std::make_shared<ov::Model>(ov::ResultVector{Q_res, K_res, V_res}, params);
    model->set_friendly_name("LlamaPreAttnModel-W8");
    return model;
}

/**
 * @returns (QKV, QKV_scales)
 */
std::tuple<std::shared_ptr<MemoryBlock>, std::shared_ptr<MemoryBlock>>
concat_QKV(size_t dtype_size, const char* wq, const char* wk, const char* wv, float q_scale,
           float k_scale, float v_scale, size_t dim, size_t kv_dim) {
    auto qkv = std::make_shared<MemoryBlock>((dim * dim + 2 * kv_dim * dim) * dtype_size);
    auto qkv_scales = std::make_shared<MemoryBlock>((dim + 2 * kv_dim) * sizeof(float));
    memcpy(qkv->get_ptr(), wq, dim * dim * dtype_size);
    memcpy(qkv->get_ptr() + dim * dim * dtype_size, wk, kv_dim * dim * dtype_size);
    memcpy(qkv->get_ptr() + (dim * dim + kv_dim * dim) * dtype_size, wv, kv_dim * dim * dtype_size);
    std::fill_n((float*)qkv_scales->get_ptr(), dim, q_scale);
    std::fill_n((float*)qkv_scales->get_ptr() + dim, kv_dim, k_scale);
    std::fill_n((float*)qkv_scales->get_ptr() + dim + kv_dim, kv_dim, v_scale);
    return std::make_tuple(qkv, qkv_scales);
}

std::shared_ptr<ov::Model> get_pre_attn_w8_concat_model(
    ov::element::Type a_dtype_ov, const int input_shape, const size_t dim, const size_t n_heads,
    const size_t n_kv_heads, const char* attn_wq_weight_ptr, const char* attn_wk_weight_ptr,
    const char* attn_wv_weight_ptr, const char* attn_rms_weight_ptr, const float attn_wq_scale,
    const float attn_wk_scale, const float attn_wv_scale) {

    const size_t head_dim = dim / n_heads;
    const size_t kv_dim = head_dim * n_kv_heads;

    // Define the input parameters
    std::shared_ptr<ov::opset15::Parameter> prompt_embedding;
    if (input_shape < 0) {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    } else {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(input_shape), dim});
    }

    auto params = ov::ParameterVector{prompt_embedding};

    // Concat QKV weights
    auto [attn_wqkv_data, attn_wqkv_scales_data] =
        concat_QKV(sizeof(int8_t), attn_wq_weight_ptr, attn_wk_weight_ptr, attn_wv_weight_ptr,
                   attn_wq_scale, attn_wk_scale, attn_wv_scale, dim, kv_dim);

    // Bind ov constants with weight pointers
    auto attn_rms_weight =
        std::make_shared<ov::opset15::Constant>(a_dtype_ov, ov::Shape{dim}, attn_rms_weight_ptr);

    auto attn_wqkv_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{dim + 2 * kv_dim, dim}, attn_wqkv_data->get_ptr());
    auto attn_wqkv_scales = std::make_shared<ov::opset15::Constant>(
        ov::element::f32, ov::Shape{dim + 2 * kv_dim, 1}, attn_wqkv_scales_data->get_ptr());
    auto attn_wqkv = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(attn_wqkv_w8, a_dtype_ov),
        std::make_shared<ov::opset15::Convert>(attn_wqkv_scales, a_dtype_ov));

    std::shared_ptr<ov::opset15::Multiply> prompt_norm;

    // RMSnorm
    {
        auto x = prompt_embedding;
        auto w = attn_rms_weight;

        // 1. Input Scaling for Numerical Stability
        auto reduce_axes = ov::opset15::Constant::create(ov::element::i64, {1}, {-1});

        // Calculate scaling factor to prevent underflow
        auto abs_x = std::make_shared<ov::opset15::Abs>(x);
        auto max_abs = std::make_shared<ov::opset15::ReduceMax>(abs_x, reduce_axes, true);
        auto safety_eps = ov::opset15::Constant::create(a_dtype_ov, {}, {1e-12f});
        auto alpha = std::make_shared<ov::opset15::Divide>(
            ov::opset15::Constant::create(a_dtype_ov, {}, {1.0f}),
            std::make_shared<ov::opset15::Maximum>(max_abs, safety_eps));

        // 2. Scaled Computations
        auto x_scaled = std::make_shared<ov::opset15::Multiply>(x, alpha);
        auto x_sq = std::make_shared<ov::opset15::Multiply>(x_scaled, x_scaled);

        // 3. Mean Square Calculation
        auto sum_sq = std::make_shared<ov::opset15::ReduceSum>(x_sq, reduce_axes, true);
        auto mean_sq = std::make_shared<ov::opset15::Divide>(
            sum_sq, ov::opset15::Constant::create(a_dtype_ov, {}, {static_cast<float>(dim)}));

        // 4. Adjusted Epsilon Handling
        auto eps = ov::opset15::Constant::create(a_dtype_ov, {}, {1e-5f});
        auto scaled_eps = std::make_shared<ov::opset15::Multiply>(
            eps, std::make_shared<ov::opset15::Multiply>(alpha, alpha));

        // 5. RMS Normalization
        auto rms = std::make_shared<ov::opset15::Sqrt>(
            std::make_shared<ov::opset15::Add>(mean_sq, scaled_eps));
        auto normalized = std::make_shared<ov::opset15::Divide>(x_scaled, rms);

        // 6. Weight Application
        prompt_norm = std::make_shared<ov::opset15::Multiply>(normalized, w);
    }

    // QKV Generation
    auto QKV = std::make_shared<ov::opset15::MatMul>(prompt_norm, attn_wqkv, false, true);
    auto QKV_result = std::make_shared<ov::opset15::Result>(QKV);

    auto model = std::make_shared<ov::Model>(ov::ResultVector{QKV_result}, params);
    model->set_friendly_name("LlamaPreAttnConcatModel-W8");
    return model;
}

} // namespace ov_kernel
} // namespace hllm