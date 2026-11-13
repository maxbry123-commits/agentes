#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>
#include <cstddef>
#include <tuple>
#include <list>
#include <array>
#include <stdfloat>
#include <random>

static std::shared_ptr<ov::Model> get_attn_model(ov::element::Type dtype_ov,
    size_t dim, size_t n_heads,
    size_t n_kv_heads) {
    using namespace ov;
    /// Define the input parameters
    size_t head_dim = dim / n_heads;
    size_t kv_dim = head_dim * n_kv_heads;

    auto Q = std::make_shared<opset15::Parameter>(
    dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    auto k_cache = std::make_shared<opset15::Parameter>(
    dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
    auto K = std::make_shared<opset15::Parameter>(
    dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
    auto V_final = std::make_shared<opset15::Parameter>(
    dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
    auto freq_cis_tensor = std::make_shared<opset15::Parameter>(
        dtype_ov,
        ov::PartialShape{ov::Dimension::dynamic(), 1, head_dim / 2, 2});
    auto is_decode =
    std::make_shared<opset15::Parameter>(ov::element::boolean, ov::Shape{});


     // ROPE
  std::shared_ptr<opset15::Concat> Q_rope;
  { // rope for Q
    // Create OpenVINO tensors, here we skip the reshape operation to make it
    // directly the right shape
    auto x_tensor = std::make_shared<opset15::Reshape>(
        Q,
        opset15::Constant::create(ov::element::i64, ov::Shape{4},
                                  std::vector<int64_t>{-1, (int64_t)n_heads,
                                                       (int64_t)head_dim / 2,
                                                       2}),
        false);

    // split x_tensor and to get the real and imaginary parts
    auto split_axis = ov::opset15::Constant::create(ov::element::i64, {}, {3});
    auto x_split = std::make_shared<ov::op::v1::Split>(x_tensor, split_axis, 2);
    auto x_real = x_split->output(0);
    auto x_imag = x_split->output(1);
    auto freq_cis_split =
        std::make_shared<ov::op::v1::Split>(freq_cis_tensor, split_axis, 2);
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
    Q_rope = std::make_shared<ov::op::v0::Concat>(
        ov::OutputVector{real, imag},
        3); // (prompt_len, n_heads, head_dim / 2, 2)
  };

  
  std::shared_ptr<ov::op::v0::Concat> K_rope;
  { // rope for K
    // Create OpenVINO tensors, here we skip the reshape operation to make it
    // directly the right shape
    auto x_tensor = std::make_shared<opset15::Reshape>(
        K,
        opset15::Constant::create(ov::element::i64, ov::Shape{4},
                                  std::vector<int64_t>{-1, (int64_t)n_kv_heads,
                                                       (int64_t)head_dim / 2,
                                                       2}),
        false);

    // split x_tensor and to get the real and imaginary parts
    auto split_axis = ov::opset15::Constant::create(ov::element::i64, {}, {3});
    auto x_split = std::make_shared<ov::op::v1::Split>(x_tensor, split_axis, 2);
    auto x_real = x_split->output(0);
    auto x_imag = x_split->output(1);
    auto freq_cis_split =
        std::make_shared<ov::op::v1::Split>(freq_cis_tensor, split_axis, 2);
    auto freq_real =
        freq_cis_split->output(0); // (prompt_len, 1, head_dim / 2, 1)
    auto freq_imag =
        freq_cis_split->output(1); // (prompt_len, 1, head_dim / 2, 1)

    // (a + bi) * (c + di) = (ac - bd) + (ad + bc)i
    auto ac = std::make_shared<ov::op::v1::Multiply>(x_real, freq_real);
    auto bd = std::make_shared<ov::op::v1::Multiply>(x_imag, freq_imag);
    auto ad = std::make_shared<ov::op::v1::Multiply>(x_real, freq_imag);
    auto bc = std::make_shared<ov::op::v1::Multiply>(x_imag, freq_real);

    auto real = std::make_shared<ov::op::v1::Subtract>(ac, bd);
    auto imag = std::make_shared<ov::op::v1::Add>(ad, bc);

    // Concatenate rotated components
    K_rope = std::make_shared<ov::op::v0::Concat>(
        ov::OutputVector{real, imag},
        3); // (prompt_len, n_heads, head_dim / 2, 2)
  }
  
    auto Q_reshape = std::make_shared<opset15::Reshape>(
    Q_rope,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{-1, (int64_t)n_heads, (int64_t)head_dim}),
    false);
    auto Q_transpose = std::make_shared<opset15::Transpose>(
    Q_reshape, opset15::Constant::create(ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{1, 0, 2}));

    auto K_rope_reshape = std::make_shared<opset15::Reshape>(
        K_rope,
        opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                  std::vector<int64_t>{-1, (int64_t)kv_dim}),
        false);

    auto K_final = std::make_shared<opset15::Select>(
        is_decode,
        std::make_shared<opset15::Concat>(
          ov::OutputVector{k_cache, K_rope_reshape},
          0),
        K_rope_reshape
    );

    // Reshape and transpose KV tensors as before
    auto K_reshape = std::make_shared<opset15::Reshape>(
    K_final,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim}),
    false);

    auto K_transpose = std::make_shared<opset15::Transpose>(
    K_reshape, opset15::Constant::create(ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{1, 0, 2}));
    auto V_reshape = std::make_shared<opset15::Reshape>(
    V_final,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim}),
    false);
    auto V_transpose = std::make_shared<opset15::Transpose>(
    V_reshape, opset15::Constant::create(ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{1, 0, 2}));

    // Calculate number of repeats needed
    int64_t repeat_count = n_heads / n_kv_heads;

    // Create a new dimension for the repeats
    auto K_reshape_for_repeat = std::make_shared<opset15::Reshape>(
    K_transpose,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{4},
    std::vector<int64_t>{(int64_t)n_kv_heads, 1, -1, (int64_t)head_dim}),
    false);

    auto V_reshape_for_repeat = std::make_shared<opset15::Reshape>(
    V_transpose,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{4},
    std::vector<int64_t>{(int64_t)n_kv_heads, 1, -1, (int64_t)head_dim}),
    false);

    // Create a tensor to broadcast across the new dimension
    auto ones =
    opset15::Constant::create(ov::element::i64, ov::Shape{4},
    std::vector<int64_t>{1, repeat_count, 1, 1});
    auto tile_axes =
    opset15::Constant::create(ov::element::i64, ov::Shape{4},
    std::vector<int64_t>{1, repeat_count, 1, 1});
    // Use Tile operation instead of Broadcast
    auto K_tiled =
    std::make_shared<opset15::Tile>(K_reshape_for_repeat, tile_axes);
    auto V_tiled =
    std::make_shared<opset15::Tile>(V_reshape_for_repeat, tile_axes);

    // Reshape back to the original format but with n_heads instead of n_kv_heads
    auto K_broadcast = std::make_shared<opset15::Reshape>(
    K_tiled,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{(int64_t)n_heads, -1, (int64_t)head_dim}),
    false);

    auto V_broadcast = std::make_shared<opset15::Reshape>(
    V_tiled,
    opset15::Constant::create(
    ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{(int64_t)n_heads, -1, (int64_t)head_dim}),
    false);

    auto scaled_dot_product_attention = std::make_shared<opset15::Select>(
    is_decode,
    std::make_shared<opset15::ScaledDotProductAttention>(
    Q_transpose, K_broadcast, V_broadcast, false),
    std::make_shared<opset15::ScaledDotProductAttention>(
    Q_transpose, K_broadcast, V_broadcast, true));

    auto weighted_V = std::make_shared<opset15::Transpose>(
    scaled_dot_product_attention,
    opset15::Constant::create(ov::element::i64, ov::Shape{3},
    std::vector<int64_t>{1, 0, 2}));
    auto weighted_V_reshape = std::make_shared<opset15::Reshape>(
    weighted_V,
    opset15::Constant::create(ov::element::i64, ov::Shape{2},
    std::vector<int64_t>{-1, (int64_t)dim}),
    false);

    auto model = std::make_shared<ov::Model>(
    ov::ResultVector{std::make_shared<opset15::Result>(weighted_V_reshape),
                    std::make_shared<opset15::Result>(K_rope)},
    ov::ParameterVector{Q, K, k_cache, V_final, freq_cis_tensor, is_decode});
    model->set_friendly_name("Llama3Attention");
    return model;
}
 
const char *USAGE = R"(Usage: real_attn <seq_len> <head_dim> <n_heads> <n_kv_heads>)";
ov::Core core;

std::float16_t *Q_buffer;
std::float16_t *K_buffer;
std::float16_t *V_buffer;
std::float16_t *freq_cis_buffer;
std::float16_t *k_cache_buffer;
std::float16_t *weighted_V_buffer;
std::float16_t *K_rope_buffer;

void prepare(int seq_len, int dim, int n_heads, int n_kv_heads) {
    size_t head_dim = dim / n_heads;
    size_t kv_dim = head_dim * n_kv_heads;

    Q_buffer = new std::float16_t[seq_len * dim];
    K_buffer = new std::float16_t[seq_len * kv_dim];
    V_buffer = new std::float16_t[seq_len * kv_dim];
    freq_cis_buffer = new std::float16_t[seq_len * 1 * head_dim / 2 * 2];
    k_cache_buffer = new std::float16_t[seq_len * kv_dim]; // Is not used in prefill
    weighted_V_buffer = new std::float16_t[seq_len * dim];
    K_rope_buffer = new std::float16_t[seq_len * kv_dim];

    auto rng = std::minstd_rand();
    std::uniform_real_distribution<std::float32_t> dist(-1.0f, 1.0f);
    for (size_t i = 0; i < seq_len * dim; ++i) {
        Q_buffer[i] = std::float16_t(dist(rng));
    }
    for (size_t i = 0; i < seq_len * kv_dim; i++) {
        K_buffer[i] = std::float16_t(dist(rng));
        V_buffer[i] = std::float16_t(dist(rng));
    }
    for (size_t i = 0; i < seq_len * head_dim / 2 * 2; ++i) {
        freq_cis_buffer[i] = std::float16_t(dist(rng));
    }
    return;
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        std::cerr << USAGE << std::endl;
        return 1;
    }

    size_t seq_len = std::stoul(argv[1]);
    size_t head_dim = std::stoul(argv[2]);
    size_t n_heads = std::stoul(argv[3]);
    size_t n_kv_heads = std::stoul(argv[4]);
    int dim = head_dim * n_heads;
    int kv_dim = head_dim * n_kv_heads;

    auto model = get_attn_model(
        ov::element::f16, dim, n_heads, n_kv_heads);
    auto compiled_model = core.compile_model(model, "GPU");
    auto infer_request = compiled_model.create_infer_request();
    prepare(seq_len, dim, n_heads, n_kv_heads);

    infer_request.set_input_tensor(
        0, ov::Tensor(ov::element::f16, ov::Shape{seq_len, dim}, Q_buffer));
    infer_request.set_input_tensor(
        1, ov::Tensor(ov::element::f16, ov::Shape{seq_len, kv_dim}, K_buffer));
    infer_request.set_input_tensor(
        2, ov::Tensor(ov::element::f16, ov::Shape{0, kv_dim}, k_cache_buffer));
    infer_request.set_input_tensor(
        3, ov::Tensor(ov::element::f16, ov::Shape{seq_len, kv_dim}, V_buffer));
    infer_request.set_input_tensor(
        4, ov::Tensor(ov::element::f16, ov::Shape{seq_len, 1, head_dim / 2, 2}, freq_cis_buffer));
    bool is_decode = false;
    infer_request.set_input_tensor(
        5, ov::Tensor(ov::element::boolean, ov::Shape{}, &is_decode));
    infer_request.set_output_tensor(
        0, ov::Tensor(ov::element::f16, ov::Shape{seq_len, dim}, weighted_V_buffer));
    infer_request.set_output_tensor(
        1, ov::Tensor(ov::element::f16, ov::Shape{seq_len, n_kv_heads, head_dim / 2, 2}, K_rope_buffer));

    infer_request.infer();
}