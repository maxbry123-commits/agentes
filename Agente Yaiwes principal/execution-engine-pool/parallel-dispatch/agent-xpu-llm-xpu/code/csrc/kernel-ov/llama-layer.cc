#include "basic/memory-block.h"
#include "kernel-ov.h"

/**
 * @returns (QKV, QKV_scales)
 */
static std::tuple<std::shared_ptr<MemoryBlock>, std::shared_ptr<MemoryBlock>>
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

namespace hllm {
namespace ov_kernel {

std::shared_ptr<ov::Model> get_llama3_layer_w8_model(
    ov::element::Type a_dtype_ov, const int seq_len, const size_t dim, const size_t n_heads,
    const size_t n_kv_heads, const size_t hidden_dim, const char* attn_rms_weight_ptr,
    const char* attn_wq_weight_ptr, const char* attn_wk_weight_ptr, const char* attn_wv_weight_ptr,
    const char* attn_wo_weight_ptr, const char* ffn_rms_weight_ptr, const char* ffn_gate_weight_ptr,
    const char* ffn_down_weight_ptr, const char* ffn_up_weight_ptr, const float attn_wq_scale,
    const float attn_wk_scale, const float attn_wv_scale, const float attn_wo_scale,
    const float ffn_gate_scale, const float ffn_down_scale, const float ffn_up_scale) {
    // Define the input parameters
    size_t head_dim = dim / n_heads;
    size_t kv_dim = head_dim * n_kv_heads;
    auto [attn_wqkv_data, attn_wqkv_scales_data] =
        concat_QKV(sizeof(int8_t), attn_wq_weight_ptr, attn_wk_weight_ptr, attn_wv_weight_ptr,
                   attn_wq_scale, attn_wk_scale, attn_wv_scale, dim, kv_dim);

    std::shared_ptr<ov::opset15::Parameter> prompt_embedding;
    std::shared_ptr<ov::opset15::Parameter> freq_cis_tensor;
    if (seq_len < 0) {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
        freq_cis_tensor = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), 1, head_dim / 2, 2});
    } else {
        prompt_embedding = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), dim});
        freq_cis_tensor = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), 1, head_dim / 2, 2});
    }

    auto attn_rms_weight =
        std::make_shared<ov::opset15::Constant>(a_dtype_ov, ov::Shape{dim}, attn_rms_weight_ptr);
    auto attn_wqkv_w8 = std::make_shared<ov::opset15::Constant>(
        ov::element::i8, ov::Shape{dim + 2 * kv_dim, dim}, attn_wqkv_data->get_ptr());
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
    auto attn_wqkv_scales = std::make_shared<ov::opset15::Constant>(
        ov::element::f32, ov::Shape{dim + 2 * kv_dim, 1}, attn_wqkv_scales_data->get_ptr());

    auto attn_wqkv = std::make_shared<ov::opset15::Multiply>(
        std::make_shared<ov::opset15::Convert>(attn_wqkv_w8, a_dtype_ov),
        std::make_shared<ov::opset15::Convert>(attn_wqkv_scales, a_dtype_ov));

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

    // k_cache and v_cache are not used while prefill
    std::shared_ptr<ov::opset15::Parameter> k_cache, v_cache;
    if (seq_len < 0) {
        k_cache = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
        v_cache = std::make_shared<ov::opset15::Parameter>(
            a_dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
    } else { // assume npu prefill
        k_cache = std::make_shared<ov::opset15::Parameter>(a_dtype_ov, ov::Shape{0, kv_dim});
        v_cache = std::make_shared<ov::opset15::Parameter>(a_dtype_ov, ov::Shape{0, kv_dim});
    }
    auto is_decode = std::make_shared<ov::opset15::Parameter>(ov::element::boolean, ov::Shape{});

    ov::ParameterVector params = {prompt_embedding, freq_cis_tensor, k_cache, v_cache, is_decode};

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

    // Attention
    auto QKV = std::make_shared<ov::opset15::MatMul>(prompt_norm, attn_wqkv, false, true);
    // Split QKV into Q, K, V parts along the last dimension
    auto split_axis = ov::opset15::Constant::create(ov::element::i64, ov::Shape{}, {1});
    auto qkv_splits = std::make_shared<ov::opset15::VariadicSplit>(
        QKV, split_axis,
        ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                      std::vector<int64_t>{static_cast<long>(dim),
                                                           static_cast<long>(kv_dim),
                                                           static_cast<long>(kv_dim)}));

    auto Q = qkv_splits->output(0); // ov::Shape: (prompt_len, dim)
    auto K = qkv_splits->output(1); // ov::Shape: (prompt_len, kv_dim)
    auto V = qkv_splits->output(2); // ov::Shape: (prompt_len, kv_dim)

    // Reshape Q into (prompt_len, n_heads, head_dim)
    auto Q_reshape_for_concat = std::make_shared<ov::opset15::Reshape>(
        Q,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{4},
            std::vector<int64_t>{-1, (int64_t)n_heads, (int64_t)head_dim / 2, 2}),
        false);

    // Reshape K into (prompt_len, n_kv_heads, head_dim)
    auto K_reshape_for_concat = std::make_shared<ov::opset15::Reshape>(
        K,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{4},
            std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim / 2, 2}),
        false);

    // Concat Q and K on axis 1 (head dimension)
    auto QK = std::make_shared<ov::opset15::Concat>(
        ov::OutputVector{Q_reshape_for_concat, K_reshape_for_concat},
        1 // Concat on head dimension
    );    // ov::Shape: (prompt_len, n_heads + n_kv_heads, head_dim / 2, 2)

    // ROPE
    std::shared_ptr<ov::opset15::Concat> QK_rope;
    { // rope for QK
        auto x_tensor = QK;

        // split x_tensor and to get the real and imaginary parts
        auto split_axis = ov::opset15::Constant::create(ov::element::i64, {}, {3});
        auto x_split = std::make_shared<ov::op::v1::Split>(x_tensor, split_axis, 2);
        auto x_real = x_split->output(0);
        auto x_imag = x_split->output(1);
        auto freq_cis_split = std::make_shared<ov::op::v1::Split>(freq_cis_tensor, split_axis, 2);
        auto freq_real = freq_cis_split->output(0);
        auto freq_imag = freq_cis_split->output(1);

        // (a + bi) * (c + di) = (ac - bd) + (ad + bc)i
        auto ac = std::make_shared<ov::op::v1::Multiply>(x_real, freq_real);
        auto bd = std::make_shared<ov::op::v1::Multiply>(x_imag, freq_imag);
        auto ad = std::make_shared<ov::op::v1::Multiply>(x_real, freq_imag);
        auto bc = std::make_shared<ov::op::v1::Multiply>(x_imag, freq_real);

        auto real = std::make_shared<ov::op::v1::Subtract>(ac, bd);
        auto imag = std::make_shared<ov::op::v1::Add>(ad, bc);

        // Concatenate rotated components
        QK_rope = std::make_shared<ov::op::v0::Concat>(
            ov::OutputVector{real, imag},
            3); // (prompt_len, n_heads + n_kv_heads, head_dim / 2, 2)
    };
    // Split QK_rope into Q and K parts along head dimension (dim 1)
    auto qk_split_axis = ov::opset15::Constant::create(ov::element::i64, ov::Shape{}, {1});
    auto qk_splits = std::make_shared<ov::opset15::VariadicSplit>(
        QK_rope, qk_split_axis,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{2},
            std::vector<int64_t>{static_cast<long>(n_heads), static_cast<long>(n_kv_heads)}));

    // Get Q and K parts
    auto Q_rope = qk_splits->output(0); // ov::Shape: (prompt_len, n_heads, head_dim/2, 2)
    auto K_rope = qk_splits->output(1); // ov::Shape: (prompt_len, n_kv_heads, head_dim/2, 2)

    // Reshape K_rope similarly
    auto K_rope_reshape = std::make_shared<ov::opset15::Reshape>(
        K_rope,
        ov::opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                      std::vector<int64_t>{-1, (int64_t)kv_dim}),
        false);

    auto K_final = std::make_shared<ov::opset15::Select>(
        is_decode,
        std::make_shared<ov::opset15::Concat>(ov::OutputVector{k_cache, K_rope_reshape}, 0),
        K_rope_reshape);
    K_final->set_friendly_name("K_final");
    auto V_final = std::make_shared<ov::opset15::Select>(
        is_decode, std::make_shared<ov::opset15::Concat>(ov::OutputVector{v_cache, V}, 0), V);
    V_final->set_friendly_name("V_final");
    auto K_output = K_rope_reshape;
    auto V_output = V;

    auto Q_reshape = std::make_shared<ov::opset15::Reshape>(
        Q_rope,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{3},
            std::vector<int64_t>{-1, (int64_t)n_heads, (int64_t)head_dim}),
        false);
    auto Q_transpose = std::make_shared<ov::opset15::Transpose>(
        Q_reshape, ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                                 std::vector<int64_t>{1, 0, 2}));

    // Reshape and transpose KV tensors as before
    auto K_reshape = std::make_shared<ov::opset15::Reshape>(
        K_final,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{3},
            std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim}),
        false);
    auto K_transpose = std::make_shared<ov::opset15::Transpose>(
        K_reshape, ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                                 std::vector<int64_t>{1, 0, 2}));
    auto V_reshape = std::make_shared<ov::opset15::Reshape>(
        V_final,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{3},
            std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim}),
        false);
    auto V_transpose = std::make_shared<ov::opset15::Transpose>(
        V_reshape, ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                                 std::vector<int64_t>{1, 0, 2}));

    // Calculate number of repeats needed
    int64_t repeat_count = n_heads / n_kv_heads;

    // Create a new dimension for the repeats
    auto K_reshape_for_repeat = std::make_shared<ov::opset15::Reshape>(
        K_transpose,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{4},
            std::vector<int64_t>{(int64_t)n_kv_heads, 1, -1, (int64_t)head_dim}),
        false);

    auto V_reshape_for_repeat = std::make_shared<ov::opset15::Reshape>(
        V_transpose,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{4},
            std::vector<int64_t>{(int64_t)n_kv_heads, 1, -1, (int64_t)head_dim}),
        false);

    // Create a tensor to broadcast across the new dimension
    auto ones = ov::opset15::Constant::create(ov::element::i64, ov::Shape{4},
                                              std::vector<int64_t>{1, repeat_count, 1, 1});
    auto tile_axes = ov::opset15::Constant::create(ov::element::i64, ov::Shape{4},
                                                   std::vector<int64_t>{1, repeat_count, 1, 1});
    // Use Tile operation instead of Broadcast
    auto K_tiled = std::make_shared<ov::opset15::Tile>(K_reshape_for_repeat, tile_axes);
    auto V_tiled = std::make_shared<ov::opset15::Tile>(V_reshape_for_repeat, tile_axes);

    // Reshape back to the original format but with n_heads instead of n_kv_heads
    auto K_broadcast = std::make_shared<ov::opset15::Reshape>(
        K_tiled,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{3},
            std::vector<int64_t>{(int64_t)n_heads, -1, (int64_t)head_dim}),
        false);

    auto V_broadcast = std::make_shared<ov::opset15::Reshape>(
        V_tiled,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{3},
            std::vector<int64_t>{(int64_t)n_heads, -1, (int64_t)head_dim}),
        false);

    auto scaled_dot_product_attention = std::make_shared<ov::opset15::Select>(
        is_decode,
        std::make_shared<ov::opset15::ScaledDotProductAttention>(Q_transpose, K_broadcast,
                                                                 V_broadcast, false),
        std::make_shared<ov::opset15::ScaledDotProductAttention>(Q_transpose, K_broadcast,
                                                                 V_broadcast, true));
    scaled_dot_product_attention->set_friendly_name("scaled_dot_product_attention");
    auto weighted_V = std::make_shared<ov::opset15::Transpose>(
        scaled_dot_product_attention, ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                                                    std::vector<int64_t>{1, 0, 2}));
    auto weighted_V_reshape = std::make_shared<ov::opset15::Reshape>(
        weighted_V,
        ov::opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                      std::vector<int64_t>{-1, (int64_t)dim}),
        false);
    auto out = std::make_shared<ov::opset15::MatMul>(weighted_V_reshape, attn_wo, false, true);
    auto attn_out_prompt_embedding = std::make_shared<ov::opset15::Add>(out, prompt_embedding);

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

    auto outputs = ov::OutputVector{ffn_out_prompt_embedding, K_output, V_output};
    ov::ResultVector results;
    for (const auto& output : outputs) {
        results.push_back(std::make_shared<ov::op::v0::Result>(output));
    }

    // Create the model with ResultVector and ParameterVector
    auto model = std::make_shared<ov::Model>(results, params);
    return model;
}

std::shared_ptr<ov::Model> get_llama3_final_layer_w8_model(
    ov::element::Type a_dtype_ov, const int seq_len, const size_t dim, const size_t n_heads,
    const size_t n_kv_heads, const size_t hidden_dim, const size_t vocab_size,
    const char* attn_rms_weight_ptr, const char* attn_wq_weight_ptr, const char* attn_wk_weight_ptr,
    const char* attn_wv_weight_ptr, const char* attn_wo_weight_ptr, const char* ffn_rms_weight_ptr,
    const char* ffn_gate_weight_ptr, const char* ffn_down_weight_ptr, const char* ffn_up_weight_ptr,
    const char* final_rms_weight_data, const char* final_wo_data, const float attn_wq_scale,
    const float attn_wk_scale, const float attn_wv_scale, const float attn_wo_scale,
    const float ffn_gate_scale, const float ffn_down_scale, const float ffn_up_scale,
    const float final_wo_scale) {
    {
        // First get the base transformer layer model
        auto transformer_model = get_llama3_layer_w8_model(
            a_dtype_ov, seq_len, dim, n_heads, n_kv_heads, hidden_dim, attn_rms_weight_ptr,
            attn_wq_weight_ptr, attn_wk_weight_ptr, attn_wv_weight_ptr, attn_wo_weight_ptr,
            ffn_rms_weight_ptr, ffn_gate_weight_ptr, ffn_down_weight_ptr, ffn_up_weight_ptr,
            attn_wq_scale, attn_wk_scale, attn_wv_scale, attn_wo_scale, ffn_gate_scale,
            ffn_down_scale, ffn_up_scale);

        // Extract the parameters and final embedding output from the transformer model
        auto prompt_embedding = transformer_model->get_parameters()[0];
        auto freq_cis_tensor = transformer_model->get_parameters()[1];
        auto k_cache = transformer_model->get_parameters()[2];
        auto v_cache = transformer_model->get_parameters()[3];
        auto is_decode = transformer_model->get_parameters()[4];

        // Use the same parameters as the transformer model
        ov::ParameterVector params = {prompt_embedding, freq_cis_tensor, k_cache, v_cache,
                                      is_decode};
        auto transformer_final_output =
            transformer_model->get_results()[0]->get_input_source_output(0);
        auto transformer_output_k_output =
            transformer_model->get_results()[1]->get_input_source_output(0);
        auto transformer_output_v_output =
            transformer_model->get_results()[2]->get_input_source_output(0);

        auto last_embedding = std::make_shared<ov::opset15::Gather>(
            transformer_final_output,
            ov::opset15::Constant::create(ov::element::i64, ov::Shape{1}, {-1}),
            ov::opset15::Constant::create(ov::element::i64, ov::Shape{}, {0}) // Axis 0
        );

        // Add the final RMSNorm and output projection
        auto final_rms_weight = std::make_shared<ov::opset15::Constant>(a_dtype_ov, ov::Shape{dim},
                                                                        final_rms_weight_data);
        auto final_wo_w8 = std::make_shared<ov::opset15::Constant>(
            ov::element::i8, ov::Shape{vocab_size, dim}, final_wo_data);

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

        // Create the final model with the new outputs
        ov::OutputVector outputs = {final_output, transformer_output_k_output,
                                    transformer_output_v_output};
        ov::ResultVector results;
        for (const auto& output : outputs) {
            results.push_back(std::make_shared<ov::op::v0::Result>(output));
        }

        // Create and return the final model
        auto final_model = std::make_shared<ov::Model>(results, params);
        return final_model;
    }

} // namespace ov_kernel
} // namespace ov_kernel
} // namespace hllm
