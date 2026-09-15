#include "util.h"
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>
#include <stdfloat>

const size_t DIM = 4096;
const size_t N_HEADS = 32;
const size_t N_KV_HEADS = 8;
auto dtype = ov::element::f32;
const int NUM_RUNS = 6;

static std::shared_ptr<ov::Model>
get_attn_model(bool is_dyn, ov::element::Type dtype_ov, size_t seqlen,
               size_t dim, size_t n_heads, size_t n_kv_heads,
               bool is_decode = false) {
  using namespace ov;
  /// Define the input parameters
  size_t head_dim = dim / n_heads;
  size_t kv_dim = head_dim * n_kv_heads;

  std::shared_ptr<ov::op::v0::Parameter> Q, K, V_final, freq_cis_tensor;
  if (is_dyn) {
    Q = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    K = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
    V_final = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), kv_dim});
    freq_cis_tensor = std::make_shared<opset15::Parameter>(
        ov::element::f32,
        ov::PartialShape{ov::Dimension::dynamic(), 1, head_dim / 2, 2});
  } else {
    Q = std::make_shared<opset15::Parameter>(dtype_ov,
                                             ov::PartialShape{seqlen, dim});
    K = std::make_shared<opset15::Parameter>(dtype_ov,
                                             ov::PartialShape{seqlen, kv_dim});
    V_final = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{seqlen, kv_dim});
    freq_cis_tensor = std::make_shared<opset15::Parameter>(
        ov::element::f32, ov::PartialShape{seqlen, 1, head_dim / 2, 2});
  }
  Q->set_friendly_name("Q_input");
  K->set_friendly_name("K_input");
  V_final->set_friendly_name("V_input");
  freq_cis_tensor->set_friendly_name("freq_cis_input");

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
  auto K_rope_final = std::make_shared<opset15::Reshape>(
      K_rope,
      opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                std::vector<int64_t>{-1, (int64_t)kv_dim}),
      false);

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
  auto Q_rope_final = std::make_shared<opset15::Reshape>(
      Q_rope,
      opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                std::vector<int64_t>{-1, (int64_t)dim}),
      false);

  auto Q_reshape = std::make_shared<opset15::Reshape>(
      Q_rope_final,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{3},
          std::vector<int64_t>{-1, (int64_t)n_heads, (int64_t)head_dim}),
      false);
  Q_reshape->set_friendly_name("Q_reshape");

  auto Q_transpose = std::make_shared<opset15::Transpose>(
      Q_reshape, opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                           std::vector<int64_t>{1, 0, 2}));
  Q_transpose->set_friendly_name("Q_transpose");

  // Reshape and transpose KV tensors as before
  auto K_reshape = std::make_shared<opset15::Reshape>(
      K_rope_final,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{3},
          std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim}),
      false);
  K_reshape->set_friendly_name("K_reshape");

  auto K_transpose = std::make_shared<opset15::Transpose>(
      K_reshape, opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                           std::vector<int64_t>{1, 0, 2}));
  K_transpose->set_friendly_name("K_transpose");

  auto V_reshape = std::make_shared<opset15::Reshape>(
      V_final,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{3},
          std::vector<int64_t>{-1, (int64_t)n_kv_heads, (int64_t)head_dim}),
      false);
  V_reshape->set_friendly_name("V_reshape");

  auto V_transpose = std::make_shared<opset15::Transpose>(
      V_reshape, opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                           std::vector<int64_t>{1, 0, 2}));
  V_transpose->set_friendly_name("V_transpose");

  // Calculate number of repeats needed
  int64_t repeat_count = n_heads / n_kv_heads;

  // Create a new dimension for the repeats
  auto K_reshape_for_repeat = std::make_shared<opset15::Reshape>(
      K_transpose,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{4},
          std::vector<int64_t>{(int64_t)n_kv_heads, 1, -1, (int64_t)head_dim}),
      false);
  K_reshape_for_repeat->set_friendly_name("K_reshape_for_repeat");

  auto V_reshape_for_repeat = std::make_shared<opset15::Reshape>(
      V_transpose,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{4},
          std::vector<int64_t>{(int64_t)n_kv_heads, 1, -1, (int64_t)head_dim}),
      false);
  V_reshape_for_repeat->set_friendly_name("V_reshape_for_repeat");

  // Create a tensor to broadcast across the new dimension
  auto ones =
      opset15::Constant::create(ov::element::i64, ov::Shape{4},
                                std::vector<int64_t>{1, repeat_count, 1, 1});
  ones->set_friendly_name("ones_constant");

  auto tile_axes =
      opset15::Constant::create(ov::element::i64, ov::Shape{4},
                                std::vector<int64_t>{1, repeat_count, 1, 1});
  tile_axes->set_friendly_name("tile_axes_constant");

  // Use Tile operation instead of Broadcast
  auto K_tiled =
      std::make_shared<opset15::Tile>(K_reshape_for_repeat, tile_axes);
  K_tiled->set_friendly_name("K_tiled");

  auto V_tiled =
      std::make_shared<opset15::Tile>(V_reshape_for_repeat, tile_axes);
  V_tiled->set_friendly_name("V_tiled");

  // Reshape back to the original format but with n_heads instead of n_kv_heads
  auto K_broadcast = std::make_shared<opset15::Reshape>(
      K_tiled,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{3},
          std::vector<int64_t>{(int64_t)n_heads, -1, (int64_t)head_dim}),
      false);
  K_broadcast->set_friendly_name("K_broadcast");

  auto V_broadcast = std::make_shared<opset15::Reshape>(
      V_tiled,
      opset15::Constant::create(
          ov::element::i64, ov::Shape{3},
          std::vector<int64_t>{(int64_t)n_heads, -1, (int64_t)head_dim}),
      false);
  V_broadcast->set_friendly_name("V_broadcast");

  auto sdpa_true = std::make_shared<opset15::ScaledDotProductAttention>(
      Q_transpose, K_broadcast, V_broadcast, true);
  sdpa_true->set_friendly_name("sdpa_with_mask");

  auto sdpa_false = std::make_shared<opset15::ScaledDotProductAttention>(
      Q_transpose, K_broadcast, V_broadcast, false);
  sdpa_false->set_friendly_name("sdpa_no_mask");

  auto scaled_dot_product_attention = is_decode ? sdpa_true : sdpa_false;
  scaled_dot_product_attention->set_friendly_name("selected_sdpa");

  auto weighted_V = std::make_shared<opset15::Transpose>(
      scaled_dot_product_attention,
      opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                std::vector<int64_t>{1, 0, 2}));
  weighted_V->set_friendly_name("weighted_V_transposed");

  auto weighted_V_reshape = std::make_shared<opset15::Reshape>(
      weighted_V,
      opset15::Constant::create(ov::element::i64, ov::Shape{2},
                                std::vector<int64_t>{-1, (int64_t)dim}),
      false);
  weighted_V_reshape->set_friendly_name("weighted_V_reshaped");

  auto result = std::make_shared<opset15::Result>(weighted_V_reshape);
  result->set_friendly_name("attention_output");

  auto model = std::make_shared<ov::Model>(
      ov::ResultVector{result},
      ov::ParameterVector{Q, K, V_final, freq_cis_tensor});
  model->set_friendly_name("Llama3Attention");
  return model;
}

int main(int argc, char **argv) {
  size_t seqlen;
  std::string device;
  if (argc != 3) {
    std::cout << "Usage: " << argv[0] << "<device> <seqlen>" << std::endl;
    return 1;
  }
  device = argv[1];
  seqlen = std::stoi(argv[2]);

  // Initialize OpenVINO runtime
  ov::Core core;
  auto devices = core.get_available_devices();
  // require both CPU, GPU and NPU
  if (std::none_of(devices.begin(), devices.end(),
                   [](const std::string &device) { return device == "CPU"; })) {
    std::cout << "CPU device not found" << std::endl;
    return 1;
  }
  if (std::none_of(devices.begin(), devices.end(),
                   [](const std::string &device) { return device == "GPU"; })) {
    std::cout << "GPU device not found" << std::endl;
    return 1;
  }
  if (std::none_of(devices.begin(), devices.end(),
                   [](const std::string &device) { return device == "NPU"; })) {
    std::cout << "NPU device not found" << std::endl;
    return 1;
  }
  size_t head_dim = DIM / N_HEADS;
  size_t kv_dim = head_dim * N_KV_HEADS;
  auto num_ops = 4 * seqlen * seqlen * DIM;
  double arith_intensity = (double)num_ops /
                           (seqlen * DIM + seqlen * kv_dim + seqlen * kv_dim) *
                           sizeof(float);
  std::cout << "Arithmetic intensity: " << arith_intensity << std::endl;

  int64_t compile_time = 0;
  int64_t runtime = 0;
  ov::InferRequest infer_request;

  auto begin = std::chrono::steady_clock::now();
  if (device == "gpu") {
    auto attn_model =
        get_attn_model(true, dtype, seqlen, DIM, N_HEADS, N_KV_HEADS);
    auto attn_model_compiled = core.compile_model(attn_model, "GPU");
    infer_request = attn_model_compiled.create_infer_request();
  } else if (device == "npu") {
    auto attn_model =
        get_attn_model(false, dtype, seqlen, DIM, N_HEADS, N_KV_HEADS);
    auto attn_model_compiled = core.compile_model(attn_model, "NPU");
    infer_request = attn_model_compiled.create_infer_request();
  } else if (device == "cpu") {
    auto attn_model =
        get_attn_model(true, dtype, seqlen, DIM, N_HEADS, N_KV_HEADS);
    auto attn_model_compiled = core.compile_model(attn_model, "CPU");
    infer_request = attn_model_compiled.create_infer_request();
  } else {
    std::cout << "Unknown device: " << device << std::endl;
    return 1;
  }
  compile_time = elapsed_time_us(begin);
  std::cout << "Compile time (us): " << compile_time << std::endl;

  // prepare inputs
  auto Q = std::vector<float>(seqlen * DIM);
  auto K = std::vector<float>(seqlen * kv_dim);
  auto V = std::vector<float>(seqlen * kv_dim);
  auto freq_cis = std::vector<float>(seqlen * head_dim);
  infer_request.set_input_tensor(0, ov::Tensor(dtype, {seqlen, DIM}, Q.data()));
  infer_request.set_input_tensor(1,
                                 ov::Tensor(dtype, {seqlen, kv_dim}, K.data()));
  infer_request.set_input_tensor(2,
                                 ov::Tensor(dtype, {seqlen, kv_dim}, V.data()));
  infer_request.set_input_tensor(
      3, ov::Tensor(dtype, {seqlen, 1, head_dim / 2, 2}, freq_cis.data()));

  // run npu and gpu alternatively to minimize interference
  for (int i = 0; i < NUM_RUNS; i++) {
    reset_data<float>(Q, dtype);
    reset_data<float>(K, dtype);
    reset_data<float>(V, dtype);
    reset_data<float>(freq_cis, dtype);
    auto begin = std::chrono::steady_clock::now();
    infer_request.infer();
    if (i > 0) {
      runtime += elapsed_time_us(begin);
    }
  }
  runtime /= (NUM_RUNS - 1);
  if (device == "npu") {
    runtime += compile_time;
  }
  auto tops = double(num_ops) / runtime / 1e6;

  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << tops << std::endl;

  return 0;
}