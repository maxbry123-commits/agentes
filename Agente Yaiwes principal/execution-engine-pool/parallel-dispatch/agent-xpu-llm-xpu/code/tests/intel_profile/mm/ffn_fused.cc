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
  auto input_ffn_gate = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{hidden_dim, dim});
  auto input_ffn_down = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{dim, hidden_dim});
  auto input_ffn_up = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{hidden_dim, dim});
  auto input_prompt = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{seq_len, dim});

  // FFN up
  auto w1x = std::make_shared<ov::opset1::MatMul>(input_prompt, input_ffn_gate,
                                                  false, true);
  auto w3x = std::make_shared<ov::opset1::MatMul>(input_prompt, input_ffn_up,
                                                  false, true);
  // SiLU
  auto w1x_sigmoid_self = std::make_shared<ov::opset15::Sigmoid>(w1x);
  auto w1x_sigmoid =
      std::make_shared<ov::opset15::Multiply>(w1x, w1x_sigmoid_self);
  auto w1x_sigmoid_w3x =
      std::make_shared<ov::opset15::Multiply>(w1x_sigmoid, w3x);
  // FFN down
  auto out = std::make_shared<ov::opset1::MatMul>(w1x_sigmoid_w3x,
                                                  input_ffn_down, false, true);
  size_t num_ops = 2 * seq_len * dim * hidden_dim * 3; // omit SiLU

  auto result = std::make_shared<ov::op::v0::Result>(out);
  auto function = std::make_shared<ov::Model>(
      ov::ResultVector{result},
      ov::ParameterVector{input_prompt, input_ffn_gate, input_ffn_up,
                          input_ffn_down});

  auto begin = std::chrono::steady_clock::now();
  auto compiled_model = core.compile_model(function, device);
  auto compile_time = elapsed_time_us(begin);

  auto infer_request = compiled_model.create_infer_request();
  infer_request.set_input_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{seq_len, dim}, input_data.data()));
  infer_request.set_input_tensor(
      1, ov::Tensor(ov_dtype, ov::Shape{hidden_dim, dim}, weight_ffn_gate));
  infer_request.set_input_tensor(
      2, ov::Tensor(ov_dtype, ov::Shape{hidden_dim, dim}, weight_ffn_up));
  infer_request.set_input_tensor(
      3, ov::Tensor(ov_dtype, ov::Shape{dim, hidden_dim}, weight_ffn_down));

  begin = std::chrono::steady_clock::now();
  infer_request.infer();
  auto runtime = elapsed_time_us(begin);

  double tops = (double)num_ops / (double)runtime / 1e6;

  std::cout << "Compile time (us): " << compile_time << std::endl;
  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << tops << std::endl;

  return 0;
}