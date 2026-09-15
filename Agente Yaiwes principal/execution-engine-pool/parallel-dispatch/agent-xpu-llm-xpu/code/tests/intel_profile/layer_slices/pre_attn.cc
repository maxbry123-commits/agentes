#include "util.h"
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>
#include <tuple>

const size_t DIM = 4096;
const size_t N_HEADS = 32;
const size_t N_KV_HEADS = 8;
const size_t HIDDEN_DIM = 14336;
auto w_dtype = ov::element::i8;
auto a_dtype = ov::element::f32;
const int NUM_RUNS = 6;

/**
 * @returns (QKV, QKV_scales)
 */
static std::tuple<std::shared_ptr<MemoryBlock>, std::shared_ptr<MemoryBlock>>
concat_QKV(size_t dtype_size, const char *wq, const char *wk, const char *wv,
           float q_scale, float k_scale, float v_scale, size_t dim,
           size_t kv_dim) {
  auto qkv = std::make_shared<MemoryBlock>((dim * dim + 2 * kv_dim * dim) *
                                           dtype_size);
  auto qkv_scales =
      std::make_shared<MemoryBlock>((dim + 2 * kv_dim) * sizeof(float));
  memcpy(qkv->get_ptr(), wq, dim * dim * dtype_size);
  memcpy(qkv->get_ptr() + dim * dim * dtype_size, wk,
         kv_dim * dim * dtype_size);
  memcpy(qkv->get_ptr() + (dim * dim + kv_dim * dim) * dtype_size, wv,
         kv_dim * dim * dtype_size);
  std::fill_n((float *)qkv_scales->get_ptr(), dim, q_scale);
  std::fill_n((float *)qkv_scales->get_ptr() + dim, kv_dim, k_scale);
  std::fill_n((float *)qkv_scales->get_ptr() + dim + kv_dim, kv_dim, v_scale);
  return std::make_tuple(qkv, qkv_scales);
}

/**
 * @warning This model works well on NPU, CPU, but wrong on GPU.
 */
static std::shared_ptr<ov::Model> get_qkv_seperated_pre_attn_model(
    bool dyn, ov::element::Type dtype_ov, size_t dim, size_t n_heads,
    size_t n_kv_heads, const void *attn_rms_weight_data,
    const void *attn_wq_data, const void *attn_wk_data,
    const void *attn_wv_data, float attn_wq_scale, float attn_wk_scale,
    float attn_wv_scale, size_t chunk_size) {
  using namespace ov;
  /// Define the input parameters
  size_t head_dim = dim / n_heads;
  size_t kv_dim = head_dim * n_kv_heads;

  std::shared_ptr<opset15::Parameter> prompt_embedding;
  if (dyn) {
    prompt_embedding = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
  } else {
    prompt_embedding = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::Shape{chunk_size, dim});
  }

  auto params = ov::ParameterVector{prompt_embedding};

  auto attn_rms_weight = std::make_shared<opset15::Constant>(
      dtype_ov, Shape{dim}, attn_rms_weight_data);
  auto attn_wq_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{dim, dim}, attn_wq_data);
  auto attn_wk_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{kv_dim, dim}, attn_wk_data);
  auto attn_wv_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{kv_dim, dim}, attn_wv_data);

  auto attn_wq = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(attn_wq_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {attn_wq_scale}));

  auto attn_wk = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(attn_wk_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {attn_wk_scale}));

  auto attn_wv = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(attn_wv_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {attn_wv_scale}));

  std::shared_ptr<opset15::Multiply> prompt_norm;

  // RMSnorm
  {
    auto x = prompt_embedding;
    auto w = attn_rms_weight;

    // 1. Input Scaling for Numerical Stability
    auto reduce_axes = opset15::Constant::create(element::i64, {1}, {-1});

    // Calculate scaling factor to prevent underflow
    auto abs_x = std::make_shared<opset15::Abs>(x);
    auto max_abs =
        std::make_shared<opset15::ReduceMax>(abs_x, reduce_axes, true);
    auto safety_eps = opset15::Constant::create(dtype_ov, {}, {1e-12f});
    auto alpha = std::make_shared<opset15::Divide>(
        opset15::Constant::create(dtype_ov, {}, {1.0f}),
        std::make_shared<opset15::Maximum>(max_abs, safety_eps));

    // 2. Scaled Computations
    auto x_scaled = std::make_shared<opset15::Multiply>(x, alpha);
    auto x_sq = std::make_shared<opset15::Multiply>(x_scaled, x_scaled);

    // 3. Mean Square Calculation
    auto sum_sq = std::make_shared<opset15::ReduceSum>(x_sq, reduce_axes, true);
    auto mean_sq = std::make_shared<opset15::Divide>(
        sum_sq,
        opset15::Constant::create(dtype_ov, {}, {static_cast<float>(dim)}));

    // 4. Adjusted Epsilon Handling
    auto eps = opset15::Constant::create(dtype_ov, {}, {1e-5f});
    auto scaled_eps = std::make_shared<opset15::Multiply>(
        eps, std::make_shared<opset15::Multiply>(alpha, alpha));

    // 5. RMS Normalization
    auto rms = std::make_shared<opset15::Sqrt>(
        std::make_shared<opset15::Add>(mean_sq, scaled_eps));
    auto normalized = std::make_shared<opset15::Divide>(x_scaled, rms);

    // 6. Weight Application
    prompt_norm = std::make_shared<opset15::Multiply>(normalized, w);
  }

  auto Q = std::make_shared<opset15::MatMul>(prompt_norm, attn_wq, false, true);
  auto K = std::make_shared<opset15::MatMul>(prompt_norm, attn_wk, false, true);
  auto V = std::make_shared<opset15::MatMul>(prompt_norm, attn_wv, false, true);

  auto Q_result = std::make_shared<ov::op::v0::Result>(Q);
  auto K_result = std::make_shared<ov::op::v0::Result>(K);
  auto V_result = std::make_shared<ov::op::v0::Result>(V);

  auto model = std::make_shared<ov::Model>(
      ov::ResultVector{Q_result, K_result, V_result}, params);
  model->set_friendly_name("Llama3PreAttnModel");
  return model;
}

/**
 * @warning This model works well on GPU, CPU but slow on NPU.
 */
static std::shared_ptr<ov::Model> get_qkv_batched_pre_attn_model(
    bool dyn, ov::element::Type dtype_ov, size_t dim, size_t n_heads,
    size_t n_kv_heads, const char *attn_rms_weight_data,
    const char *attn_wq_data, const char *attn_wk_data,
    const char *attn_wv_data, float attn_wq_scale, float attn_wk_scale,
    float attn_wv_scale, size_t chunk_size) {
  using namespace ov;
  /// Define the input parameters
  size_t head_dim = dim / n_heads;
  size_t kv_dim = head_dim * n_kv_heads;

  auto [attn_wqkv_data, attn_wqkv_scales_data] =
      concat_QKV(sizeof(int8_t), attn_wq_data, attn_wk_data, attn_wv_data,
                 attn_wq_scale, attn_wk_scale, attn_wv_scale, dim, kv_dim);

  std::shared_ptr<opset15::Parameter> prompt_embedding;
  if (dyn) {
    prompt_embedding = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
  } else {
    prompt_embedding = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::Shape{chunk_size, dim});
  }

  auto params = ov::ParameterVector{prompt_embedding};

  auto attn_rms_weight = std::make_shared<opset15::Constant>(
      dtype_ov, Shape{dim}, attn_rms_weight_data);
  auto attn_wqkv_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{dim + 2 * kv_dim, dim}, attn_wqkv_data->get_ptr());
  auto attn_wqkv_scales = std::make_shared<opset15::Constant>(
      ov::element::f32, Shape{dim + 2 * kv_dim, 1},
      attn_wqkv_scales_data->get_ptr());
  auto attn_wqkv = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(attn_wqkv_w8, dtype_ov),
      std::make_shared<opset15::Convert>(attn_wqkv_scales, dtype_ov));

  std::shared_ptr<opset15::Multiply> prompt_norm;

  // RMSnorm
  {
    auto x = prompt_embedding;
    auto w = attn_rms_weight;

    // 1. Input Scaling for Numerical Stability
    auto reduce_axes = opset15::Constant::create(element::i64, {1}, {-1});

    // Calculate scaling factor to prevent underflow
    auto abs_x = std::make_shared<opset15::Abs>(x);
    auto max_abs =
        std::make_shared<opset15::ReduceMax>(abs_x, reduce_axes, true);
    auto safety_eps = opset15::Constant::create(dtype_ov, {}, {1e-12f});
    auto alpha = std::make_shared<opset15::Divide>(
        opset15::Constant::create(dtype_ov, {}, {1.0f}),
        std::make_shared<opset15::Maximum>(max_abs, safety_eps));

    // 2. Scaled Computations
    auto x_scaled = std::make_shared<opset15::Multiply>(x, alpha);
    auto x_sq = std::make_shared<opset15::Multiply>(x_scaled, x_scaled);

    // 3. Mean Square Calculation
    auto sum_sq = std::make_shared<opset15::ReduceSum>(x_sq, reduce_axes, true);
    auto mean_sq = std::make_shared<opset15::Divide>(
        sum_sq,
        opset15::Constant::create(dtype_ov, {}, {static_cast<float>(dim)}));

    // 4. Adjusted Epsilon Handling
    auto eps = opset15::Constant::create(dtype_ov, {}, {1e-5f});
    auto scaled_eps = std::make_shared<opset15::Multiply>(
        eps, std::make_shared<opset15::Multiply>(alpha, alpha));

    // 5. RMS Normalization
    auto rms = std::make_shared<opset15::Sqrt>(
        std::make_shared<opset15::Add>(mean_sq, scaled_eps));
    auto normalized = std::make_shared<opset15::Divide>(x_scaled, rms);

    // 6. Weight Application
    prompt_norm = std::make_shared<opset15::Multiply>(normalized, w);
  }

  // Attention
  auto QKV =
      std::make_shared<opset15::MatMul>(prompt_norm, attn_wqkv, false, true);
  // Split QKV into Q, K, V parts along the last dimension
  auto split_axis = opset15::Constant::create(ov::element::i64, Shape{}, {1});
  auto qkv_splits = std::make_shared<opset15::VariadicSplit>(
      QKV, split_axis,
      opset15::Constant::create(ov::element::i64, ov::Shape{3},
                                std::vector<int64_t>{(int64_t)dim,
                                                     (int64_t)kv_dim,
                                                     (int64_t)kv_dim}));

  auto Q = qkv_splits->output(0); // Shape: (prompt_len, dim)
  auto K = qkv_splits->output(1); // Shape: (prompt_len, kv_dim)
  auto V = qkv_splits->output(2); // Shape: (prompt_len, kv_dim)

  auto Q_result = std::make_shared<opset15::Result>(Q);
  auto K_result = std::make_shared<opset15::Result>(K);
  auto V_result = std::make_shared<opset15::Result>(V);

  auto model = std::make_shared<ov::Model>(
      ov::ResultVector{Q_result, K_result, V_result}, params);
  model->set_friendly_name("Llama3PreAttnModel");
  return model;
}

int main(int argc, char **argv) {
  size_t seqlen;
  std::string device;
  if (argc != 3) {
    std::cout << "Usage: " << argv[0] << " <device> <seqlen>" << std::endl;
    return 1;
  }
  device = argv[1];
  seqlen = std::stoul(argv[2]);

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

  // prepare weight data
  size_t kv_dim = DIM / N_HEADS * N_KV_HEADS;
  size_t head_dim = DIM / N_HEADS;
  std::vector<float> attn_rms_weight_data = prepare_data<float>(a_dtype, DIM);
  std::vector<int8_t> attn_wq_data = prepare_data<int8_t>(w_dtype, DIM * DIM);
  std::vector<int8_t> attn_wk_data =
      prepare_data<int8_t>(w_dtype, kv_dim * DIM);
  std::vector<int8_t> attn_wv_data =
      prepare_data<int8_t>(w_dtype, kv_dim * DIM);
  float attn_wq_scale = 0.1f;
  float attn_wk_scale = 0.1f;
  float attn_wv_scale = 0.1f;

  int64_t compile_time = 0;
  int64_t runtime = 0;
  ov::InferRequest infer_request;
  auto prompt_embedding_data = std::vector<float>(seqlen * DIM);

  auto num_ops = 2 * seqlen * DIM * DIM + 4 * seqlen * DIM * kv_dim;
  size_t num_bytes = attn_rms_weight_data.size() * sizeof(float) +
                     attn_wq_data.size() * sizeof(int8_t) +
                     attn_wk_data.size() * sizeof(int8_t) +
                     attn_wv_data.size() * sizeof(int8_t) +
                     prompt_embedding_data.size() * sizeof(float) +
                     seqlen * DIM * sizeof(float) +               // input
                     seqlen * (DIM + 2 * kv_dim) * sizeof(float); // output
  double arith_intensity = double(num_ops) / double(num_bytes);

  std::cout << "Arithmetic intensity: " << arith_intensity << std::endl;

  // define and compile the function
  auto begin = std::chrono::steady_clock::now();
  std::shared_ptr<ov::Model> pre_attn_model;
  std::string device_name;
  if (device == "gpu") {
    pre_attn_model = get_qkv_seperated_pre_attn_model(
        true, a_dtype, DIM, N_HEADS, N_KV_HEADS,
        (const char *)attn_rms_weight_data.data(),
        (const char *)attn_wq_data.data(), (const char *)attn_wk_data.data(),
        (const char *)attn_wv_data.data(), attn_wq_scale, attn_wk_scale,
        attn_wv_scale, seqlen);
    device_name = "GPU";
  } else {
    pre_attn_model = get_qkv_batched_pre_attn_model(
        false, a_dtype, DIM, N_HEADS, N_KV_HEADS,
        (const char *)attn_rms_weight_data.data(),
        (const char *)attn_wq_data.data(), (const char *)attn_wk_data.data(),
        (const char *)attn_wv_data.data(), attn_wq_scale, attn_wk_scale,
        attn_wv_scale, seqlen);
    device_name = (device == "npu") ? "NPU" : "CPU";
  }

  auto pre_attn_model_compiled =
      core.compile_model(pre_attn_model, device_name);
  infer_request = pre_attn_model_compiled.create_infer_request();
  compile_time = elapsed_time_us(begin);

  // set input data
  infer_request.set_input_tensor(0, ov::Tensor(a_dtype, ov::Shape{seqlen, DIM},
                                               prompt_embedding_data.data()));

  std::cout << "Compile time (us): " << compile_time << std::endl;

  for (int i = 0; i < NUM_RUNS; i++) {
    reset_data<float>(prompt_embedding_data, a_dtype);
    auto begin = std::chrono::steady_clock::now();
    infer_request.infer();
    if (i > 0) {
      runtime += elapsed_time_us(begin);
    }
  }
  runtime /= (NUM_RUNS - 1);

  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << (double)num_ops / runtime / 1e6
            << std::endl;

  return 0;
}