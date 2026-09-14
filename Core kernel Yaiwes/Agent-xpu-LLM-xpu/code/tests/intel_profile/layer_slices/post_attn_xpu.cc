#include "openvino/openvino.hpp"
#include "openvino/opsets/opset15.hpp"
#include "util.h"
#include <chrono>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

const size_t DIM = 4096;
const size_t N_HEADS = 32;
const size_t N_KV_HEADS = 8;
const size_t HIDDEN_DIM = 14336;
auto w_dtype = ov::element::i8;
auto a_dtype = ov::element::f32;
const int NUM_RUNS = 100;

static std::shared_ptr<ov::Model> get_post_attn_chunk_model(
    bool dyn, ov::element::Type dtype_ov, size_t dim, size_t n_heads,
    size_t n_kv_heads, size_t hidden_dim, const char *attn_wo_data,
    const char *ffn_rms_weight_data, const char *ffn_gate_data,
    const char *ffn_down_data, const char *ffn_up_data, float attn_wo_scale,
    float ffn_gate_scale, float ffn_down_scale, float ffn_up_scale,
    size_t chunk_size) {
  using namespace ov;
  /// Define the input parameters
  size_t head_dim = dim / n_heads;
  size_t kv_dim = head_dim * n_kv_heads;

  std::shared_ptr<opset15::Parameter> prompt_embedding, weighted_V_reshape,
      freq_cis_tensor;
  if (dyn) {
    prompt_embedding = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
    weighted_V_reshape = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::PartialShape{ov::Dimension::dynamic(), dim});
  } else {
    prompt_embedding = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::Shape{chunk_size, dim});
    weighted_V_reshape = std::make_shared<opset15::Parameter>(
        dtype_ov, ov::Shape{chunk_size, dim});
  }
  auto params = ov::ParameterVector{weighted_V_reshape, prompt_embedding};

  auto attn_wo_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{dim, dim}, attn_wo_data);
  auto ffn_rms_weight = std::make_shared<opset15::Constant>(
      dtype_ov, Shape{dim}, ffn_rms_weight_data);
  auto ffn_gate_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{hidden_dim, dim}, ffn_gate_data);
  auto ffn_down_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{dim, hidden_dim}, ffn_down_data);
  auto ffn_up_w8 = std::make_shared<opset15::Constant>(
      ov::element::i8, Shape{hidden_dim, dim}, ffn_up_data);

  auto attn_wo = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(attn_wo_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {attn_wo_scale}));

  auto ffn_gate = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(ffn_gate_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {ffn_gate_scale}));

  auto ffn_down = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(ffn_down_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {ffn_down_scale}));

  auto ffn_up = std::make_shared<opset15::Multiply>(
      std::make_shared<opset15::Convert>(ffn_up_w8, dtype_ov),
      opset15::Constant::create(dtype_ov, Shape{1}, {ffn_up_scale}));
  auto out = std::make_shared<opset15::MatMul>(weighted_V_reshape, attn_wo,
                                               false, true);
  auto attn_out_prompt_embedding =
      std::make_shared<opset15::Add>(out, prompt_embedding);

  // FFN
  std::shared_ptr<opset15::Multiply> ffn_prompt_norm;

  // RMSnorm
  {
    auto x = attn_out_prompt_embedding;
    auto w = ffn_rms_weight;

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
    ffn_prompt_norm = std::make_shared<opset15::Multiply>(normalized, w);
  }
  auto ffn_w1x =
      std::make_shared<opset15::MatMul>(ffn_prompt_norm, ffn_gate, false, true);
  auto ffn_w3x =
      std::make_shared<opset15::MatMul>(ffn_prompt_norm, ffn_up, false, true);

  std::shared_ptr<opset15::Multiply> w1x_w3x;
  {
    auto x1 = ffn_w1x;
    auto x3 = ffn_w3x;
    auto sigmoid = std::make_shared<ov::opset15::Sigmoid>(x1);
    auto w1x_sigmoid = std::make_shared<ov::opset15::Multiply>(x1, sigmoid);
    w1x_w3x = std::make_shared<ov::opset15::Multiply>(w1x_sigmoid, x3);
  }
  auto ffn_out =
      std::make_shared<opset15::MatMul>(w1x_w3x, ffn_down, false, true);
  auto ffn_out_prompt_embedding =
      std::make_shared<opset15::Add>(ffn_out, attn_out_prompt_embedding);

  auto outputs = ov::OutputVector{ffn_out_prompt_embedding};
  ov::ResultVector results;
  for (const auto &output : outputs) {
    results.push_back(std::make_shared<ov::op::v0::Result>(output));
  }

  // Create the model with ResultVector and ParameterVector
  auto model = std::make_shared<ov::Model>(results, params);
  model->set_friendly_name("Llama3PostAttnModel");
  return model;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        std::cout << "Usage: " << argv[0] << " <seqlen> <pct>" << std::endl;
        return 1;
    }
    size_t seqlen = std::stoul(argv[1]);
    float percentage = std::stof(argv[2]);
    if (percentage < 0 || percentage > 1) {
        std::cout << "percentage must be between 0 and 1" << std::endl;
        return 1;
    }
    // 根据比例拆分batch
    size_t seqlen_gpu = static_cast<size_t>(seqlen * percentage);
    size_t seqlen_npu = seqlen - seqlen_gpu;

    // 计算算子数量（分GPU和NPU部分分别计算）
    auto num_ops_gpu = 2 * seqlen_gpu * DIM * DIM +
                       2 * 2 * seqlen_gpu * DIM * HIDDEN_DIM +
                       2 * seqlen_gpu * HIDDEN_DIM * DIM;
    auto num_ops_npu = 2 * seqlen_npu * DIM * DIM +
                       2 * 2 * seqlen_npu * DIM * HIDDEN_DIM +
                       2 * seqlen_npu * HIDDEN_DIM * DIM;
    size_t num_ops_total = num_ops_gpu + num_ops_npu;

    // prepare weight data and input
    auto attn_wo_data = prepare_data<int8_t>(w_dtype, DIM * DIM);
    auto ffn_rms_weight_data = prepare_data<float>(a_dtype, DIM);
    auto ffn_gate_data = prepare_data<int8_t>(w_dtype, DIM * HIDDEN_DIM);
    auto ffn_down_data = prepare_data<int8_t>(w_dtype, DIM * HIDDEN_DIM);
    auto ffn_up_data = prepare_data<int8_t>(w_dtype, HIDDEN_DIM * DIM);

    float attn_wo_scale = 0.1f;
    float ffn_gate_scale = 0.1f;
    float ffn_down_scale = 0.1f;
    float ffn_up_scale = 0.1f;

    // 为两个设备分别准备输入数据
    std::vector<float> prompt_embedding_gpu(seqlen_gpu * DIM);
    std::vector<float> weighted_V_reshape_gpu(seqlen_gpu * DIM);
    std::vector<float> prompt_embedding_npu(seqlen_npu * DIM);
    std::vector<float> weighted_V_reshape_npu(seqlen_npu * DIM);

    ov::Core core;
    auto devices = core.get_available_devices();
    // 检查必须设备
    if (std::none_of(devices.begin(), devices.end(), [](const std::string &d) { return d == "GPU"; })) {
        std::cout << "GPU device not found" << std::endl;
        return 1;
    }
    if (std::none_of(devices.begin(), devices.end(), [](const std::string &d) { return d == "NPU"; })) {
        std::cout << "NPU device not found" << std::endl;
        return 1;
    }
    if (std::none_of(devices.begin(), devices.end(), [](const std::string &d) { return d == "CPU"; })) {
        std::cout << "CPU device not found" << std::endl;
        return 1;
    }

    // 分别构建GPU和NPU模型
    auto begin = std::chrono::steady_clock::now();
    // GPU使用动态shape，chunk_size设为seqlen_gpu
    auto post_attn_model_gpu = get_post_attn_chunk_model(
        true, a_dtype, DIM, N_HEADS, N_KV_HEADS, HIDDEN_DIM,
        (const char *)attn_wo_data.data(),
        (const char *)ffn_rms_weight_data.data(),
        (const char *)ffn_gate_data.data(), (const char *)ffn_down_data.data(),
        (const char *)ffn_up_data.data(), attn_wo_scale, ffn_gate_scale,
        ffn_down_scale, ffn_up_scale, seqlen_gpu);
    // NPU使用静态shape，chunk_size设为seqlen_npu
    auto post_attn_model_npu = get_post_attn_chunk_model(
        false, a_dtype, DIM, N_HEADS, N_KV_HEADS, HIDDEN_DIM,
        (const char *)attn_wo_data.data(),
        (const char *)ffn_rms_weight_data.data(),
        (const char *)ffn_gate_data.data(), (const char *)ffn_down_data.data(),
        (const char *)ffn_up_data.data(), attn_wo_scale, ffn_gate_scale,
        ffn_down_scale, ffn_up_scale, seqlen_npu);

    // 分别在GPU和NPU上编译模型
    auto compiled_model_gpu = core.compile_model(post_attn_model_gpu, "GPU");
    auto compiled_model_npu = core.compile_model(post_attn_model_npu, "NPU");
    auto compile_time = std::chrono::duration_cast<std::chrono::microseconds>(
                            std::chrono::steady_clock::now() - begin)
                            .count();
    std::cout << "Total compile time (us): " << compile_time << std::endl;

    // 创建各自的InferRequest
    auto infer_request_gpu = compiled_model_gpu.create_infer_request();
    auto infer_request_npu = compiled_model_npu.create_infer_request();
    infer_request_gpu.set_input_tensor(0, ov::Tensor(a_dtype, ov::Shape{seqlen_gpu, DIM},
                                                      weighted_V_reshape_gpu.data()));
    infer_request_gpu.set_input_tensor(1, ov::Tensor(a_dtype, ov::Shape{seqlen_gpu, DIM},
                                                      prompt_embedding_gpu.data()));
    infer_request_npu.set_input_tensor(0, ov::Tensor(a_dtype, ov::Shape{seqlen_npu, DIM},
                                                      weighted_V_reshape_npu.data()));
    infer_request_npu.set_input_tensor(1, ov::Tensor(a_dtype, ov::Shape{seqlen_npu, DIM},
                                                      prompt_embedding_npu.data()));
    std::vector<ov::InferRequest> infer_requests;
    infer_requests.push_back(infer_request_gpu);
    infer_requests.push_back(infer_request_npu);

    int64_t runtime_total = 0;
    // 并行执行NUM_RUNS次（第一轮丢弃）
    // 重置输入数据
    reset_data<float>(prompt_embedding_gpu, a_dtype);
    reset_data<float>(weighted_V_reshape_gpu, a_dtype);
    reset_data<float>(prompt_embedding_npu, a_dtype);
    reset_data<float>(weighted_V_reshape_npu, a_dtype);
    for (int i = 0; i < NUM_RUNS; i++) {

        auto start = std::chrono::steady_clock::now();
        // 异步启动两个设备的推理
        infer_request_gpu.start_async();
        infer_request_npu.start_async();
        // 等待两个设备结束
        infer_request_gpu.wait();
        infer_request_npu.wait();
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
                           std::chrono::steady_clock::now() - start)
                           .count();
        if (i > 0) {  // 丢弃第一次运行
            runtime_total += elapsed;
        }
    }
    double avg_runtime = runtime_total / static_cast<double>(NUM_RUNS - 1); // us
    double tops = num_ops_total / (avg_runtime * 1e-6) / 1e12; // TOPS

    std::cout << "Total runtime (us): " << avg_runtime << std::endl;
    std::cout << "Combined TOPS: " << tops << std::endl;

    return 0;
}