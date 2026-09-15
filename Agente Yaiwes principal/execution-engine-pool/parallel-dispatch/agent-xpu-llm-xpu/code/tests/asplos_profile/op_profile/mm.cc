#include "../util.h"
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <omp.h>
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset1.hpp>
#include <openvino/opsets/opset14.hpp>
#include <random>
#ifdef _MSC_VER
#include <cstdint>
using float16_t = uint16_t;
#else
#include <stdfloat>
#endif
#include <string>
#include <vector>


const int NUM_RUNS =6;

void init_data(std::vector<float16_t> &input_data) {
  static std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
#pragma omp parallel for
  for (int i = 0; i < input_data.size(); ++i) {
    // store 32-bit float bits truncated to 16-bit integer representation
    input_data[i] = static_cast<float16_t>(dist_fp32(generator));
  }
}

int main(int argc, char **argv) {
  // usage: <program> <device:GPU|NPU> <sqlen>
  if (argc != 3) {
    std::cout << "Usage: " << argv[0] << " <device> <sqlen>" << std::endl;
    return 1;
  }
  std::string device = argv[1];
  size_t k = std::stoul(argv[2]);
  size_t shape1 = k, shape2 = 4096, shape3 = 4096;

  // calculate operations and arithmetic intensity
  size_t num_ops = 2 * shape1 * shape2 * shape3;
  double arith_intensity = static_cast<double>(num_ops) /
      ((shape1 * shape2 + shape1 * shape3 + shape2 * shape3) * sizeof(float16_t));

  // initialize OpenVINO
  ov::Core core;

  // prepare model: parameter and constant
  auto weight_data = prepare_data<float16_t>(ov::element::f16, shape3 * shape2);
  auto weight = std::make_shared<ov::op::v0::Constant>(
      ov::element::f16, ov::Shape{shape3, shape2}, weight_data);
  auto input = std::make_shared<ov::op::v0::Parameter>(
      ov::element::f16, ov::Shape{shape1, shape2});
  auto matmul = std::make_shared<ov::opset1::MatMul>(input, weight, false, true);
  auto result = std::make_shared<ov::op::v0::Result>(matmul);
  auto function = std::make_shared<ov::Model>(
      ov::ResultVector{result}, ov::ParameterVector{input});

  // run on selected device and record metrics for both
  int64_t gpu_compile_time = -1, npu_compile_time = -1;
  int64_t gpu_runtime = -1, npu_runtime = -1;
  double gpu_throughput = -1.0, npu_throughput = -1.0;
  auto run_device = [&](const std::string &dev, int64_t &out_ct, int64_t &out_rt, double &out_tp) {
    // compile
    auto ct0 = std::chrono::steady_clock::now();
    auto cm = core.compile_model(
        function, dev,
        ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
    out_ct = elapsed_time_us(ct0);
    // infer
    auto ir = cm.create_infer_request();
    int64_t total_rt = 0;
    for (int i = 0; i < NUM_RUNS; ++i) {
      auto data = prepare_data<float16_t>(ov::element::f16, shape1 * shape2);
      ir.set_input_tensor(0, ov::Tensor(ov::element::f16, ov::Shape{shape1, shape2}, data.data()));
      auto rt0 = std::chrono::steady_clock::now();
      ir.infer();
      if (i > 0) total_rt += elapsed_time_us(rt0);
    }
    out_rt = total_rt / (NUM_RUNS - 1);
    out_tp = static_cast<double>(num_ops) / out_rt / 1e6;
  };
  if (device == "GPU" || device == "gpu") {
    run_device("GPU", gpu_compile_time, gpu_runtime, gpu_throughput);
  } else if (device == "NPU" || device == "npu") {
    run_device("NPU", npu_compile_time, npu_runtime, npu_throughput);
  } else {
    std::cerr << "Unknown device: " << device << std::endl;
    return 1;
  }
  // output all metrics
  std::cout << "Arithmetic intensity: " << arith_intensity << std::endl;
  std::cout << "GPU compile time (us): " << gpu_compile_time << std::endl;
  std::cout << "NPU compile time (us): " << npu_compile_time << std::endl;
  std::cout << "GPU runtime (us): " << gpu_runtime << std::endl;
  std::cout << "NPU runtime (us): " << npu_runtime << std::endl;
  std::cout << "GPU throughput (TOPS): " << gpu_throughput << std::endl;
  std::cout << "NPU throughput (TOPS): " << npu_throughput << std::endl;
  return 0;
}