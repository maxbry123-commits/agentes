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

size_t batch_size, shape1, shape2, shape3;
size_t num_ops;
std::string device;
std::string dtype;
ov::Core core;

size_t BATCH_SIZE_HINT = 10;

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
void prepare_data_and_run_autobatching(ov::element::Type ov_dtype) {
  // Define the model
  auto input1 = std::make_shared<ov::op::v0::Parameter>(
      ov_dtype, ov::PartialShape{-1, shape2});
  auto input2 = std::make_shared<ov::op::v0::Constant>(
      ov_dtype, ov::Shape{shape3, shape2},
      prepare_data<T>(ov_dtype, shape3 * shape2));
  auto matmul =
      std::make_shared<ov::opset14::MatMul>(input1, input2, false, true);
  auto result = std::make_shared<ov::op::v0::Result>(matmul);
  auto function = std::make_shared<ov::Model>(ov::ResultVector{result},
                                              ov::ParameterVector{input1});

  // Compile the model
  auto begin = std::chrono::steady_clock::now();
  auto compiled_model = core.compile_model(
      function, device,
      ov::hint::performance_mode(
          ov::hint::PerformanceMode::THROUGHPUT), // Enable autobatching
      ov::hint::num_requests(
          BATCH_SIZE_HINT) // Optional: Limit parallel requests to 4
  );
  compile_time = elapsed_time_us(begin);

  // Create an inference request
  auto infer_requests = std::vector<ov::InferRequest>(batch_size);
  for (size_t i = 0; i < batch_size; i++) {
    infer_requests[i] = compiled_model.create_infer_request();
  }

  std::vector<std::vector<T>> decode_data(batch_size - 1,
                                         std::vector<T>(1 * shape2));
  std::vector<T> prefill_data(shape1 * shape2);

  infer_requests[0].set_input_tensor(
    0, ov::Tensor(ov_dtype, ov::Shape{shape1, shape2},
                  prefill_data.data()));

  for (int batch = 1; batch < batch_size; batch++) {
    infer_requests[batch].set_input_tensor(
        0, ov::Tensor(ov_dtype, ov::Shape{1, shape2},
                      decode_data[batch - 1].data()));
  }

  std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
  std::uniform_real_distribution<std::float16_t> dist_fp16(-1.0, 1.0);
  std::uniform_int_distribution<int8_t> dist_int8(-127, 127);
  std::uniform_int_distribution<int32_t> dist_int32(-127, 127);
  auto generate_input = [&]() {
#pragma omp parallel for
for(int i = 0; i < shape1 * shape2; i++)
{
  if (ov_dtype == ov::element::f32) {
    prefill_data[i] = dist_fp32(generator);
  } else if (ov_dtype == ov::element::f16) {
    prefill_data[i] = dist_fp16(generator);
  } else if (ov_dtype == ov::element::i8) {
    prefill_data[i] = dist_int8(generator);
  } else if (ov_dtype == ov::element::i32) {
    prefill_data[i] = dist_int32(generator);
  }
}

#pragma omp parallel for
    for (int batch = 0; batch < batch_size - 1; batch++) {
      for (int i = 0; i < shape2; ++i) {
        if (ov_dtype == ov::element::f32) {
          decode_data[batch][i] = dist_fp32(generator);
        } else if (ov_dtype == ov::element::f16) {
          decode_data[batch][i] = dist_fp16(generator);
        } else if (ov_dtype == ov::element::i8) {
          decode_data[batch][i] = dist_int8(generator);
        } else if (ov_dtype == ov::element::i32) {
          decode_data[batch][i] = dist_int32(generator);
        }
      }
    }
  };

  runtime = 0;
  for (int i = 0; i < 5; i++) {
    generate_input();
    auto begin = std::chrono::steady_clock::now();
    for (int batch = 0; batch < batch_size; batch++) {
      infer_requests[batch].start_async();
    }
    for (int batch = 0; batch < batch_size; batch++) {
      infer_requests[batch].wait();
    }
    runtime += elapsed_time_us(begin);
  }
  runtime /= 5;

  double tops = (double)num_ops / (double)runtime / 1e6;

  std::cout << "Compile time (us): " << compile_time << std::endl;
  std::cout << "Runtime (us): " << runtime << std::endl;
  std::cout << "Throughput (TOPS): " << tops << std::endl;
}

int main(int argv, char **argc) {
  if (argv != 7) {
    std::cout << "Usage: " << argc[0]
              << " <device (npu/gpu/cpu)> <dtype (fp32/fp16/int8/int32)> "
                 "<batch_size> <shape1> "
                 "<shape2> <shape3>"
              << std::endl;
    return 1;
  }

  device = argc[1];
  dtype = argc[2];
  batch_size = std::stoi(argc[3]);
  shape1 = std::stoi(argc[4]);
  shape2 = std::stoi(argc[5]);
  shape3 = std::stoi(argc[6]);
  num_ops = 2 * shape1 * shape2 * shape3 + 2 * 1 * shape2 * shape3 * (batch_size - 1);
  BATCH_SIZE_HINT = batch_size;

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


  std::cout << "Autobatching with " << device << " on " << dtype
            << " with hint batch size " << BATCH_SIZE_HINT << std::endl;
  // Prepare input data
  if (ov_dtype == ov::element::f32) {
    prepare_data_and_run_autobatching<float>(ov_dtype);
  } else if (ov_dtype == ov::element::f16) {
    prepare_data_and_run_autobatching<std::float16_t>(ov_dtype);
  } else if (ov_dtype == ov::element::i8) {
    prepare_data_and_run_autobatching<int8_t>(ov_dtype);
  } else if (ov_dtype == ov::element::i32) {
    prepare_data_and_run_autobatching<int32_t>(ov_dtype);
  }

  return 0;
}
