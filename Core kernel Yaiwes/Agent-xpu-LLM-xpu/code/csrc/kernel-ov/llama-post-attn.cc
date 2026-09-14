#include "kernel-ov.h"

namespace hllm {
namespace ov_kernel {

std::shared_ptr<ov::Model> get_post_attn_w8_model(
    ov::element::Type a_dtype_ov, const int input_shape, const size_t dim, const size_t hidden_dim,
    const char* attn_wo_weight_ptr, const char* ffn_rms_weight_ptr, const char* ffn_gate_weight_ptr,
    const char* ffn_down_weight_ptr, const char* ffn_up_weight_ptr, const float attn_wo_scale,
    const float ffn_gate_scale, const float ffn_down_scale, const float ffn_up_scale) {

    // Define the input parameters
    std::shared_ptr<ov::opset15::Parameter> prompt_embedding, weighted_V_reshape;

    if (input_shape < 0) { // dynamic shape
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
        weighted_V_reshape = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    } else {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(input_shape), dim});
        weighted_V_reshape = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(input_shape), dim});
    }

    auto params = ov::ParameterVector{weighted_V_reshape, prompt_embedding};

    // Create ov constant from weight pointer
    auto attn_wo_w8 = std::make_shared<ov::opset15::Constant>(ov::element::i8, ov::Shape{dim, dim},
                                                              attn_wo_weight_ptr);
    auto ffn_rms_weight =
        std::make_shared<ov::opset15::Constant>(a_dtype_ov, ov::Shape{dim}, ffn_rms_weight_ptr);
    auto ffn_gate_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{hidden_dim, dim}, ffn_gate_weight_ptr);
    auto ffn_down_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{dim, hidden_dim}, ffn_down_weight_ptr);
    auto ffn_up_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{hidden_dim, dim}, ffn_up_weight_ptr);

    // Apply weight scale (dequantize)
    auto attn_wo = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(attn_wo_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {attn_wo_scale}));

    auto ffn_gate = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(ffn_gate_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {ffn_gate_scale}));

    auto ffn_down = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(ffn_down_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {ffn_down_scale}));

    auto ffn_up = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(ffn_up_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {ffn_up_scale}));

    // Attention output computation
    auto attn_out = std::make_shared<ov::opset15::MatMul>(weighted_V_reshape, attn_wo, false, true);
    auto attn_out_prompt_embedding = std::make_shared<ov::opset15::Add>(attn_out, prompt_embedding);

    // FFN
    std::shared_ptr<ov::opset15::Multiply> ffn_prompt_norm;

    // RMSnorm
    {
        auto x = attn_out_prompt_embedding;
        auto w = ffn_rms_weight;

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
        ffn_prompt_norm = std::make_shared<ov::opset15::Multiply>(normalized, w);
    }
    auto ffn_w1x = std::make_shared<ov::opset15::MatMul>(ffn_prompt_norm, ffn_gate, false, true);
    auto ffn_w3x = std::make_shared<ov::opset15::MatMul>(ffn_prompt_norm, ffn_up, false, true);

    std::shared_ptr<ov::opset15::Multiply> w1x_w3x;
    {
        auto x1 = ffn_w1x;
        auto x3 = ffn_w3x;
        auto sigmoid = std::make_shared<ov::opset15::Sigmoid>(x1);
        auto w1x_sigmoid = std::make_shared<ov::opset15::Multiply>(x1, sigmoid);
        w1x_w3x = std::make_shared<ov::opset15::Multiply>(w1x_sigmoid, x3);
    }
    auto ffn_out = std::make_shared<ov::opset15::MatMul>(w1x_w3x, ffn_down, false, true);
    auto ffn_out_prompt_embedding =
        std::make_shared<ov::opset15::Add>(ffn_out, attn_out_prompt_embedding);

    auto outputs = ov::OutputVector{ffn_out_prompt_embedding};
    ov::ResultVector results;
    for (const auto& output : outputs) {
        results.push_back(std::make_shared<ov::op::v0::Result>(output));
    }

    // Create the model with ResultVector and ParameterVector
    auto model = std::make_shared<ov::Model>(results, params);
    model->set_friendly_name("LlamaPostAttnModel-W8");
    return model;
}

} // namespace ov_kernel
} // namespace hllm