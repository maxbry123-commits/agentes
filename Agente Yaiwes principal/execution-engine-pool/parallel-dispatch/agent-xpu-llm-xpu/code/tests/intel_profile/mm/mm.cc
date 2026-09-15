#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <omp.h>
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset1.hpp>
#include <openvino/opsets/opset14.hpp>
#include <random>
#include <stdfloat>
#include <string>
#include <vector>

size_t shape1, shape2, shape3;
std::string device;
std::string dtype;

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start) {
  auto end = std::chrono::steady_clock::now();
  return std::chrono::duration_cast<std::chrono::microseconds>(end - start)
      .count();
}

int64_t compile_time, runtime;

template <typename T>
void prepare_data_and_run(ov::InferRequest &infer_request,
                          ov::element::Type ov_dtype) {
  std::vector<T> input_data1(shape1 * shape2);
  std::vector<T> input_data2(shape2 * shape3);
  infer_request.set_input_tensor(
      0, ov::Tensor(ov_dtype, ov::Shape{shape1, shape2}, input_data1.data()));
  infer_request.set_input_tensor(
      1, ov::Tensor(ov_dtype, ov::Shape{shape3, shape2}, input_data2.data()));
  std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
  std::uniform_real_distribution<std::float16_t> dist_fp16(-1.0, 1.0);
  std::uniform_int_distribution<int8_t> dist_int8(-127, 127);
  std::uniform_int_distribution<int32_t> dist_int32(-127, 127);
  auto generate_input = [&]() {
#pragma omp parallel for
    for (int i = 0; i < shape1 * shape2; ++i) {
      if (ov_dtype == ov::element::f32) {
        input_data1[i] = dist_fp32(generator);
      } else if (ov_dtype == ov::element::f16) {
        input_data1[i] = dist_fp16(generator);
      } else if (ov_dtype == ov::element::i8) {
        input_data1[i] = dist_int8(generator);
      } else if (ov_dtype == ov::element::i32) {
        input_data1[i] = dist_int32(generator);
      }
    }
#pragma omp parallel for
    for (int i = 0; i < shape2 * shape3; ++i) {
      if (ov_dtype == ov::element::f32) {
        input_data2[i] = dist_fp32(generator);
      } else if (ov_dtype == ov::element::f16) {
        input_data2[i] = dist_fp16(generator);
      } else if (ov_dtype == ov::element::i8) {
        input_data2[i] = dist_int8(generator);
      } else if (ov_dtype == ov::element::i32) {
        input_data2[i] = dist_int32(generator);
      }
    }
  };

  runtime = 0;
  for (int i = 0; i < 5; i++) {
    generate_input();
    auto begin = std::chrono::steady_clock::now();
    infer_request.infer();
    runtime += elapsed_time_us(begin);
  }
  runtime /= 5;
}

int main(int argv, char **argc) {
  if (argv != 6) {
    std::cout
        << "Usage: " << argc[0]
        << " <device (npu/gpu/cpu)> <dtype (fp32/fp16/int8/int32)> <shape1> "
           "<shape2> <shape3>"
        << std::endl;
    return 1;
  }

  device = argc[1];
  dtype = argc[2];
  shape1 = std::stoi(argc[3]);
  shape2 = std::stoi(argc[4]);
  shape3 = std::stoi(argc[5]);

  size_t num_ops = 2 * shape1 * shape2 * shape3;

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

  auto ov_dtype = ov::element::f32;
  if (dtype == "fp16" || dtype == "FP16") {
    ov_dtype = ov::element::f16;
  } else if (dtype == "int8" || dtype == "INT8") {
    ov_dtype = ov::element::i8;
  } else if (dtype == "fp32" || dtype == "FP32") {
    ov_dtype = ov::element::f32;
  } else if (dtype == "int32") {
    ov_dtype = ov::element::i32;
  } else {
    std::cout << "Unknown dtype: " << dtype << std::endl;
    return 1;
  }

  // Define the model
  auto input1 = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{shape1, shape2});
  auto input2 = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::Shape{shape3, shape2});
  auto matmul =
      std::make_shared<ov::opset1::MatMul>(input1, input2, false, true);
  auto result = std::make_shared<ov::op::v0::Result>(matmul);
  auto function = std::make_shared<ov::Model>(
      ov::ResultVector{result}, ov::ParameterVector{input1, input2});

  // Compile the model
  auto begin = std::chrono::steady_clock::now();
  auto compiled_model = core.compile_model(function, device);
  compile_time = elapsed_time_us(begin);

  // Create an inference request
  auto infer_request = compiled_model.create_infer_request();

  // Prepare input data
  if (ov_dtype == ov::element::f32) {
    prepare_data_and_run<float>(infer_request, ov_dtype);
  } else if (ov_dtype == ov::element::f16) {
    prepare_data_and_run<std::float16_t>(infer_request, ov_dtype);
  } else if (ov_dtype == ov::element::i8) {
    prepare_data_and_run<int8_t>(infer_request, ov_dtype);
  } else if (ov_dtype == ov::element::i32) {
    prepare_data_and_run<int32_t>(infer_request, ov_dtype);
  }

  double tops = (double)num_ops / (double)runtime / 1e6;

  std::cout << "Compile time (us): " << compile_time << std::endl;
  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << tops << std::endl;

  return 0;
}
