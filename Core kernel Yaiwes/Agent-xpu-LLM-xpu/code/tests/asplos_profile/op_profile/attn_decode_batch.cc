#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>
#include <memory>
#include <cstdint>
#include "../util.h"

#define DIM 3072
#define N_HEADS 24
#define N_KV_HEADS 8

struct DecodeJob {
    std::vector<uint16_t> q_proj;
    std::vector<uint16_t> k_proj;
    std::vector<uint16_t> k_cache;
    std::vector<uint16_t> v_cache;
    std::vector<uint16_t> weighted_v;
};

std::shared_ptr<ov::Model> get_attn_model(ov::element::Type dtype_ov, const int seq_len, size_t dim,
                                          size_t n_heads, size_t n_kv_heads) {

    // Define the input parameters
    size_t head_dim = dim / n_heads;
    size_t kv_dim = head_dim * n_kv_heads;

    std::shared_ptr<ov::opset15::Parameter> Q, k_cache, K, V_final, freq_cis_tensor, is_decode;
    if (seq_len == -1) {
        Q = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
        k_cache = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
        K = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
        V_final = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
        freq_cis_tensor = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), 1, head_dim / 2, 2});
    } else {
        Q = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), dim});
        k_cache = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), kv_dim});
        K = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), kv_dim});
        V_final = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), kv_dim});
        freq_cis_tensor = std::make_shared<ov::opset15::Parameter>(
            dtype_ov, ov::Shape{static_cast<unsigned long>(seq_len), 1, head_dim / 2, 2});
    }
    is_decode = std::make_shared<ov::opset15::Parameter>(ov::element::boolean, ov::Shape{});

    // ROPE
    std::shared_ptr<ov::opset15::Concat> Q_rope;
    { // rope for Q
        // Create OpenVINO tensors, here we skip the reshape operation to make it
        // directly the right shape
        auto x_tensor = std::make_shared<ov::opset15::Reshape>(
            Q,
            ov::opset15::Constant::create(
                ov::element::i64, ov::Shape{4},
                std::vector<int64_t>{-1, (int64_t)n_heads, (int64_t)head_dim / 2, 2}),
            false);

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
        Q_rope = std::make_shared<ov::op::v0::Concat>(ov::OutputVector{real, imag},
                                                      3); // (prompt_len, n_heads, head_dim / 2, 2)
    };

    std::shared_ptr<ov::op::v0::Concat> K_rope;
    { // rope for K
        // Create OpenVINO tensors, here we skip the reshape operation to make it
        // directly the right shape
        auto x_tensor = std::make_shared<ov::opset15::Reshape>(
            K,
            ov::opset15::Constant::create(
                ov::element::i64, ov::Shape{4},
                std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim / 2, 2}),
            false);

        // split x_tensor and to get the real and imaginary parts
        auto split_axis = ov::opset15::Constant::create(ov::element::i64, {}, {3});
        auto x_split = std::make_shared<ov::op::v1::Split>(x_tensor, split_axis, 2);
        auto x_real = x_split->output(0);
        auto x_imag = x_split->output(1);
        auto freq_cis_split = std::make_shared<ov::op::v1::Split>(freq_cis_tensor, split_axis, 2);
        auto freq_real = freq_cis_split->output(0); // (prompt_len, 1, head_dim / 2, 1)
        auto freq_imag = freq_cis_split->output(1); // (prompt_len, 1, head_dim / 2, 1)

        // (a + bi) * (c + di) = (ac - bd) + (ad + bc)i
        auto ac = std::make_shared<ov::op::v1::Multiply>(x_real, freq_real);
        auto bd = std::make_shared<ov::op::v1::Multiply>(x_imag, freq_imag);
        auto ad = std::make_shared<ov::op::v1::Multiply>(x_real, freq_imag);
        auto bc = std::make_shared<ov::op::v1::Multiply>(x_imag, freq_real);

        auto real = std::make_shared<ov::op::v1::Subtract>(ac, bd);
        auto imag = std::make_shared<ov::op::v1::Add>(ad, bc);

        // Concatenate rotated components
        K_rope = std::make_shared<ov::op::v0::Concat>(ov::OutputVector{real, imag},
                                                      3); // (prompt_len, n_heads, head_dim / 2, 2)
    }

    auto Q_reshape = std::make_shared<ov::opset15::Reshape>(
        Q_rope,
        ov::opset15::Constant::create(
            ov::element::i64, ov::Shape{3},
            std::vector<int64_t>{-1, (int64_t)n_heads, (int64_t)head_dim}),
        false);
    auto Q_transpose = std::make_shared<ov::opset15::Transpose>(
        Q_reshape, ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                                 std::vector<int64_t>{1, 0, 2}));

    auto K_rope_reshape = std::make_shared<ov::opset15::Reshape>(
        K_rope,
        ov::opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                      std::vector<int64_t>{-1, (int64_t)kv_dim}),
        false);

    auto K_final = std::make_shared<ov::opset15::Select>(
        is_decode,
        std::make_shared<ov::opset15::Concat>(ov::OutputVector{k_cache, K_rope_reshape}, 0),
        K_rope_reshape);

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

    auto weighted_V = std::make_shared<ov::opset15::Transpose>(
        scaled_dot_product_attention, ov::opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                                                    std::vector<int64_t>{1, 0, 2}));
    auto weighted_V_reshape = std::make_shared<ov::opset15::Reshape>(
        weighted_V,
        ov::opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                      std::vector<int64_t>{-1, (int64_t)dim}),
        false);

    auto model = std::make_shared<ov::Model>(
        ov::ResultVector{std::make_shared<ov::opset15::Result>(weighted_V_reshape),
                         std::make_shared<ov::opset15::Result>(K_rope_reshape)},
        ov::ParameterVector{Q, K, k_cache, V_final, freq_cis_tensor, is_decode});
    model->set_friendly_name("LlamaAttention");
    return model;

}

int main(int argc, char **argv) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <device> <batch_size> <seq_len>" << std::endl;
        return 1;
    }
    std::string device = argv[1];
    if (device != "gpu" and device != "cpu") {
        std::cerr << "Invalid device: " << device << std::endl;
        return 1;
    }
    std::transform(device.begin(), device.end(), device.begin(), ::toupper);
    int batch_size = std::stoi(argv[2]);
    size_t seq_len = std::stoul(argv[3]);

    ov::element::Type dtype = ov::element::f16;
    std::vector<uint16_t> freq_cis;
    int head_dim = DIM / N_HEADS;
    int kv_dim = head_dim * N_KV_HEADS;
    freq_cis = prepare_data<uint16_t>(dtype, 1 * head_dim / 2 * 2);
    bool is_decode = true;

    std::vector<DecodeJob> jobs;
    for (int i = 0; i < batch_size; i++) {
        DecodeJob job;
        job.q_proj = prepare_data<uint16_t>(dtype, 1 * DIM);
        job.k_proj = prepare_data<uint16_t>(dtype, 1 * kv_dim);
        job.k_cache = prepare_data<uint16_t>(dtype, (seq_len) * kv_dim);
        job.v_cache = prepare_data<uint16_t>(dtype, (seq_len + 1) * kv_dim);
        job.weighted_v = prepare_data<uint16_t>(dtype, 1 * DIM);
        jobs.push_back(job);
    }

    ov::Core core;
    auto model = get_attn_model(dtype, seq_len, DIM, N_HEADS, N_KV_HEADS);
    auto compiled_model = core.compile_model(model, device);
    std::vector<ov::InferRequest> irs;
    auto begin_compile = std::chrono::steady_clock::now();
    for (int i = 0; i < batch_size; i++) {
        auto ir = compiled_model.create_infer_request();
        ir.set_input_tensor(0, ov::Tensor(dtype, ov::Shape{1, DIM}, jobs[i].q_proj.data()));
        ir.set_input_tensor(1, ov::Tensor(dtype, ov::Shape{1, kv_dim}, jobs[i].k_proj.data()));
        ir.set_input_tensor(2, ov::Tensor(dtype, ov::Shape{seq_len, kv_dim}, jobs[i].k_cache.data()));
        ir.set_input_tensor(3, ov::Tensor(dtype, ov::Shape{seq_len + 1, kv_dim}, jobs[i].v_cache.data()));
        ir.set_input_tensor(4, ov::Tensor(dtype, ov::Shape{1, 1, head_dim / 2, 2}, freq_cis.data()));
        ir.set_input_tensor(5, ov::Tensor(ov::element::boolean, ov::Shape{}, &is_decode));
        // ir.set_output_tensor(0, ov::Tensor(dtype, ov::Shape{1, DIM}, jobs[i].weighted_v.data()));
        // ir.set_output_tensor(1, ov::Tensor(dtype, ov::Shape{1, kv_dim}, jobs[i].k_cache.data() + seq_len * kv_dim));
        irs.push_back(std::move(ir));
    }
    auto time_compile_us = elapsed_time_us(begin_compile);
    std::cout << "IR prepare time: " << time_compile_us << " us" << std::endl;

    auto begin_infer = std::chrono::steady_clock::now();
    for (auto& ir : irs) {
        ir.start_async();
    }
    for (auto& ir : irs) {
        ir.wait();
    }
    auto time_infer_us = elapsed_time_us(begin_infer);
    std::cout << "Infer time: " << time_infer_us << " us" << std::endl;

    return 0;
    
}