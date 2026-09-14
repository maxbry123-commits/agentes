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

size_t N;
std::string device;
std::string dtype;

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start) {
  auto end = std::chrono::steady_clock::now();
  return std::chrono::duration_cast<std::chrono::microseconds>(end - start)
      .count();
}

int64_t compile_time, runtime;

template <typename T>
std::vector<T> prepare_data(ov::element::Type ov_dtype, size_t size) {
  std::vector<T> input_data(size);
  std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
  std::uniform_real_distribution<std::float16_t> dist_fp16(-1.0, 1.0);
  std::uniform_int_distribution<int8_t> dist_int8(-127, 127);
  std::uniform_int_distribution<int32_t> dist_int32(-127, 127);
  auto generate_input = [&]() {
#pragma omp parallel for
    for (int i = 0; i < size; ++i) {
      if (ov_dtype == ov::element::f32) {
        input_data[i] = dist_fp32(generator);
      } else if (ov_dtype == ov::element::f16) {
        input_data[i] = dist_fp16(generator);
      } else if (ov_dtype == ov::element::i8) {
        input_data[i] = dist_int8(generator);
      } else if (ov_dtype == ov::element::i32) {
        input_data[i] = dist_int32(generator);
      }
    }
  };
  generate_input();
  return input_data;
}

template <typename T>
void prepare_data_and_run(ov::InferRequest &infer_request,
                          ov::element::Type ov_dtype, size_t input_n) {
  std::vector<std::vector<T>> inputdata(input_n);
  std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
  std::uniform_real_distribution<std::float16_t> dist_fp16(-1.0, 1.0);
  std::uniform_int_distribution<int8_t> dist_int8(-127, 127);
  std::uniform_int_distribution<int32_t> dist_int32(-127, 127);
  auto generate_input = [&]() {
    for (int i = 0; i < input_n; i++) {
      inputdata[i] = prepare_data<T>(ov_dtype, N * N);
      infer_request.set_input_tensor(
          i, ov::Tensor(ov_dtype, ov::Shape{N, N}, inputdata[i].data()));
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
  if (argv != 5) {
    std::cout << "Usage: " << argc[0]
              << " <device (npu/gpu/cpu)> <dtype (fp32/fp16/int8/int32)> <N> "
                 "<mm_times>"
              << std::endl;
    return 1;
  }

  device = argc[1];
  dtype = argc[2];
  N = std::stoi(argc[3]);
  int mm_times = std::stoi(argc[4]);

  size_t num_ops = 2 * N * N * N * mm_times;

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

  auto input1 =
      std::make_shared<ov::op::v0::Parameter>(ov_dtype, ov::Shape{N, N});

  auto inputs = std::vector<std::shared_ptr<ov::op::v0::Parameter>>(
      mm_times,
      std::make_shared<ov::op::v0::Parameter>(ov_dtype, ov::Shape{N, N}));

  // Define the model
  auto input2 =
      std::make_shared<ov::op::v0::Parameter>(ov_dtype, ov::Shape{N, N});
  std::vector<std::shared_ptr<ov::opset1::MatMul>> matmuls(mm_times);
  matmuls[0] =
      std::make_shared<ov::opset1::MatMul>(input1, input2, false, true);
  // Create a chain of matmuls
  for (int i = 1; i < mm_times; i++) {
    matmuls[i] = std::make_shared<ov::opset1::MatMul>(inputs[i], matmuls[i - 1],
                                                      false, true);
  }
  auto result = std::make_shared<ov::op::v0::Result>(matmuls[mm_times - 1]);
  auto parameter_vec = ov::ParameterVector{input1, input2};
  for (int i = 0; i < mm_times; i++) {
    parameter_vec.push_back(inputs[i]);
  }
  auto function =
      std::make_shared<ov::Model>(ov::ResultVector{result}, parameter_vec);

  // Compile the model
  auto begin = std::chrono::steady_clock::now();
  auto compiled_model = core.compile_model(function, device);
  compile_time = elapsed_time_us(begin);

  // Create an inference request
  auto infer_request = compiled_model.create_infer_request();

  // Prepare input data
  if (ov_dtype == ov::element::f32) {
    prepare_data_and_run<float>(infer_request, ov_dtype, mm_times + 2);
  } else if (ov_dtype == ov::element::f16) {
    prepare_data_and_run<std::float16_t>(infer_request, ov_dtype, mm_times + 2);
  } else if (ov_dtype == ov::element::i8) {
    prepare_data_and_run<int8_t>(infer_request, ov_dtype, mm_times + 2);
  } else if (ov_dtype == ov::element::i32) {
    prepare_data_and_run<int32_t>(infer_request, ov_dtype, mm_times + 2);
  }

  double tops = (double)num_ops / (double)runtime / 1e6;

  std::cout << "Compile time (us): " << compile_time << std::endl;
  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << tops << std::endl;
  return 0;
}
