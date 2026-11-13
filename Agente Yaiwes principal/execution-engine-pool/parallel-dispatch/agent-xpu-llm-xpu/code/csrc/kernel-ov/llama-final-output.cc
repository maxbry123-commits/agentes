#include "kernel-ov.h"

namespace hllm {
namespace ov_kernel {

std::shared_ptr<ov::Model>
get_final_out_w8_model(ov::element::Type a_dtype_ov, const int input_shape, const size_t dim,
                       const size_t vocab_size, const char* final_rms_weight_ptr,
                       const char* final_wo_weight_ptr, const float final_wo_scale) {
    // Define the input parameters
    std::shared_ptr<ov::opset15::Parameter> last_embedding;
    if (input_shape < 0) {
        last_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    } else {
        last_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(input_shape), dim});
    }

    auto params = ov::ParameterVector{last_embedding};

    // Prepare weight
    auto final_rms_weight =
        std::make_shared<ov::opset15::Constant>(a_dtype_ov, ov::Shape{dim}, final_rms_weight_ptr);
    auto final_wo_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{vocab_size, dim}, final_wo_weight_ptr);

    auto final_wo = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(final_wo_w8, a_dtype_ov),
        ov::opset15::Constant::create(a_dtype_ov, ov::Shape{1}, {final_wo_scale}));

    // RMSnorm for final layer
    std::shared_ptr<ov::opset15::Multiply> final_prompt_norm;
    {
        auto x = last_embedding;
        auto w = final_rms_weight;

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
        final_prompt_norm = std::make_shared<ov::opset15::Multiply>(normalized, w);
    }

    // Final output projection
    auto final_output =
        std::make_shared<ov::opset15::MatMul>(final_prompt_norm, final_wo, false, true);
    auto final_output_f32 = std::make_shared<ov::opset15::Convert>(final_output, ov::element::f32);

    // Create the final model with the new outputs
    ov::OutputVector outputs = {final_output_f32};
    ov::ResultVector results;
    for (const auto& output : outputs) {
        results.push_back(std::make_shared<ov::op::v0::Result>(output));
    }

    // Create and return the final model
    auto final_model = std::make_shared<ov::Model>(results, params);
    final_model->set_friendly_name("LlamaFinalModel-W8");
    return final_model;
}

} // namespace ov_kernel
} // namespace hllm