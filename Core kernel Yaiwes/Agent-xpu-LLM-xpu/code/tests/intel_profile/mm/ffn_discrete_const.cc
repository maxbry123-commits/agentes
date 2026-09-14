#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <omp.h>
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset1.hpp>
#include <openvino/opsets/opset14.hpp>
#include <openvino/opsets/opset15.hpp>
#include <random>
#include <stdfloat>
#include <string>
#include <vector>

constexpr size_t hidden_dim = 11008;
constexpr size_t dim = 4096;

float weight_ffn_gate[hidden_dim * dim]; // (hidden_dim, dim), w1
float weight_ffn_down[dim * hidden_dim]; // (dim, hidden_dim), w2
float weight_ffn_up[hidden_dim * dim];   // (hidden_dim, dim), w3

int seq_len;

std::string device;

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start) {
  auto end = std::chrono::steady_clock::now();
  return std::chrono::duration_cast<std::chrono::microseconds>(end - start)
      .count();
}

int main(int argc, char **argv) {
  if (argc != 3) {
    std::cout << "Usage: " << argv[0] << " <device (npu/gpu/cpu)> <seq_len>"
              << std::endl;
    return 1;
  }
  device = argv[1];
  seq_len = std::stoi(argv[2]);

  // Initialize OpenVINO runtime
  ov::Core core;
  auto devices = core.get_available_devices();
  if (device == "npu" || device == "NPU") {
    device = "NPU";
    if (std::none_of(
            devices.begin(), devices.end(),
            [](const std::string &device) { return device == "NPU"; })) {
      std::cout << "NPU device not found" << std::endl;
      return 1;
    }
  } else if (device == "gpu" || device == "GPU") {
    device = "GPU";
    if (std::none_of(
            devices.begin(), devices.end(),
            [](const std::string &device) { return device == "GPU"; })) {
      std::cout << "GPU device not found" << std::endl;
      return 1;
    }
  } else if (device == "cpu" || device == "CPU") {
    device = "CPU";
  } else {
    std::cout << "Unknown device: " << device << std::endl;
    return 1;
  }

  // Prepare weights
  std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
  for (int i = 0; i < hidden_dim * dim; i++) {
    weight_ffn_gate[i] = dist(generator);
  }
  for (int i = 0; i < dim * hidden_dim; i++) {
    weight_ffn_down[i] = dist(generator);
  }
  for (int i = 0; i < hidden_dim * dim; i++) {
    weight_ffn_up[i] = dist(generator);
  }
  std::vector<float> input_data(seq_len * dim);
  for (int i = 0; i < seq_len * dim; i++) {
    input_data[i] = dist(generator);
  }

  auto ov_dtype = ov::element::f32;
  auto input_ffn_gate = std::make_shared<ov::op::v0::Constant>(
      ov_dtype, ov::Shape{hidden_dim, dim}, weight_ffn_gate);
  auto input_ffn_down = std::make_shared<ov::op::v0::Constant>(
      ov_dtype, ov::Shape{dim, hidden_dim}, weight_ffn_down);
  auto input_ffn_up = std::make_shared<ov::op::v0::Constant>(
      ov_dtype, ov::Shape{hidden_dim, dim}, weight_ffn_up);
  auto input_prompt = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{seq_len, dim});
  std::vector<float> w1x_data(seq_len * hidden_dim);
  std::vector<float> w3x_data(seq_len * hidden_dim);
  std::vector<float> w1x_w3x_data(seq_len * hidden_dim);
  auto w1x = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{seq_len, hidden_dim});
  auto w3x = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{seq_len, hidden_dim});
  auto w1x_w3x = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{seq_len, hidden_dim});

  // MM1 (gate)
  auto mm1 = std::make_shared<ov::opset1::MatMul>(input_prompt, input_ffn_gate,
                                                  false, true);
  auto result_mm1 = std::make_shared<ov::op::v0::Result>(mm1);
  auto function_mm1 = std::make_shared<ov::Model>(
      ov::ResultVector{result_mm1}, ov::ParameterVector{input_prompt});
  auto compiled_model_mm1 = core.compile_model(function_mm1, device);
  auto infer_request_mm1 = compiled_model_mm1.create_infer_request();
  infer_request_mm1.set_input_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, dim}, input_data.data()));
  infer_request_mm1.set_output_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, hidden_dim}, w1x_data.data()));

  // MM2 (up)
  auto mm2 = std::make_shared<ov::opset1::MatMul>(input_prompt, input_ffn_up,
                                                  false, true);
  auto result_mm2 = std::make_shared<ov::op::v0::Result>(mm2);
  auto function_mm2 = std::make_shared<ov::Model>(
      ov::ResultVector{result_mm2}, ov::ParameterVector{input_prompt});
  auto compiled_model_mm2 = core.compile_model(function_mm2, device);
  auto infer_request_mm2 = compiled_model_mm2.create_infer_request();
  infer_request_mm2.set_input_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, dim}, input_data.data()));
  infer_request_mm2.set_output_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, hidden_dim}, w3x_data.data()));

  // SiLU
  auto w1x_sigmoid_self = std::make_shared<ov::opset15::Sigmoid>(w1x);
  auto w1x_sigmoid =
      std::make_shared<ov::opset15::Multiply>(w1x, w1x_sigmoid_self);
  auto w1x_sigmoid_w3x =
      std::make_shared<ov::opset15::Multiply>(w1x_sigmoid, w3x);
  auto result_silu = std::make_shared<ov::op::v0::Result>(w1x_sigmoid_w3x);
  auto function_silu = std::make_shared<ov::Model>(
      ov::ResultVector{result_silu}, ov::ParameterVector{w1x, w3x});
  auto compiled_model_silu = core.compile_model(function_silu, device);
  auto infer_request_silu = compiled_model_silu.create_infer_request();
  infer_request_silu.set_input_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, hidden_dim}, w1x_data.data()));
  infer_request_silu.set_input_tensor(
      1, ov::Tensor(ov_dtype, ov::Shape{seq_len, hidden_dim}, w3x_data.data()));
  infer_request_silu.set_output_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, hidden_dim},
                    w1x_w3x_data.data()));

  // MM3 (down)
  auto mm3 = std::make_shared<ov::opset1::MatMul>(w1x_w3x, input_ffn_down,
                                                  false, true);
  auto result_mm3 = std::make_shared<ov::op::v0::Result>(mm3);
  auto function_mm3 = std::make_shared<ov::Model>(ov::ResultVector{result_mm3},
                                                  ov::ParameterVector{w1x_w3x});
  auto compiled_model_mm3 = core.compile_model(function_mm3, device);
  auto infer_request_mm3 = compiled_model_mm3.create_infer_request();
  infer_request_mm3.set_input_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, hidden_dim},
                    w1x_w3x_data.data()));

  size_t num_ops = 2 * seq_len * dim * hidden_dim * 3; // omit SiLU

  auto begin = std::chrono::steady_clock::now();
  infer_request_mm1.infer();
  infer_request_mm2.infer();
  infer_request_silu.infer();
  infer_request_mm3.infer();
  auto runtime = elapsed_time_us(begin);

  double tops = (double)num_ops / (double)runtime / 1e6;

  std::cout << "Compile time (us): " << "N/A" << std::endl;
  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << tops << std::endl;

  return 0;
}