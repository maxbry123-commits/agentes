#include "util.h"
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
#include <stdfloat>
#include <string>
#include <vector>

#define TEST_NPU
#define TEST_XPU

constexpr int NUM_RUNS = 6;

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start) {
  auto end = std::chrono::steady_clock::now();
  return std::chrono::duration_cast<std::chrono::microseconds>(end - start)
      .count();
}

static std::string get_status_string(ov::ProfilingInfo::Status status) {
  switch (status) {
  case ov::ProfilingInfo::Status::NOT_RUN:
    return "NOT_RUN";
  case ov::ProfilingInfo::Status::OPTIMIZED_OUT:
    return "OPTIMIZED_OUT";
  case ov::ProfilingInfo::Status::EXECUTED:
    return "EXECUTED";
  default:
    return "UNKNOWN";
  }
}
void write_kernel_profile_info(ov::InferRequest &infer_request) {
  if (!allow_profile)
    return;

  static std::fstream os(
      "/home/haoran.li/LLM.xpu/tests/intel_profile/roofline/intel_profile.csv",
      std::ios_base::app);
  std::vector<ov::ProfilingInfo> profiling_info =
      infer_request.get_profiling_info();

  // Generate unique random ID
  static std::random_device rd;
  static std::mt19937_64 gen(rd());
  static std::uniform_int_distribution<uint64_t> dis;
  uint64_t unique_id = dis(gen);

  // Get model name and device name from infer_request
  std::string model_name =
      infer_request.get_compiled_model().get_property(ov::model_name);
  auto devices =
      infer_request.get_compiled_model().get_property(ov::execution_devices);
  std::string device_name =
      devices.empty()
          ? "UNKNOWN"
          : std::accumulate(devices.begin(), devices.end(), std::string(),
                            [](const std::string &a, const std::string &b) {
                              return a.empty() ? b : a + "," + b;
                            });
  static bool header_written = false;
  if (!header_written) {
    os << "ID,Model Name,Device Name,Node Name,Status,Real Time (us),CPU Time "
          "(us),Node Type,Execution Type\n";
    header_written = true;
  }
  for (const auto &info : profiling_info) {
    os << unique_id << "," << model_name << "," << device_name << ","
       << info.node_name << "," << get_status_string(info.status) << ","
       << info.real_time.count() << "," << info.cpu_time.count() << ","
       << info.node_type << "," << info.exec_type << "\n";
  }
  os.flush();
}

void init_data(std::vector<std::float16_t> &input_data) {
  static std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
#pragma omp parallel for
  for (int i = 0; i < input_data.size(); ++i) {
    input_data[i] = static_cast<std::float16_t>(dist_fp32(generator));
  }
}

int main(int argc, char **argv) {
  size_t shape1, shape2, shape3;
  float percentage = 0.0;
  if (argc != 5) {
    std::cout << "Usage: " << argv[0]
              << " <shape1> <shape2> <shape3> <percentage>" << std::endl;
    return 1;
  }
  shape1 = std::stoi(argv[1]);
  shape2 = std::stoi(argv[2]);
  shape3 = std::stoi(argv[3]);
  percentage = std::stof(argv[4]);
  if (percentage < 0 || percentage > 1) {
    std::cout << "percentage must be between 0 and 1" << std::endl;
    return 1;
  }

  // Initialize OpenVINO runtime
  ov::Core core;
  auto devices = core.get_available_devices();
  // require both GPU and NPU
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

  // prepare weights and inputs
  size_t shape1_gpu = shape1 * percentage;
  size_t shape1_npu = shape1 - shape1_gpu;
  std::vector<std::float16_t> weight_data(shape3 * shape2);
  init_data(weight_data);
  auto weight = std::make_shared<ov::op::v0::Constant>(
      ov::element::f16, ov::Shape{shape3, shape2}, weight_data);
  auto input_xnpu = std::make_shared<ov::op::v0::Parameter>(
      ov::element::f16, ov::Shape{shape1_npu, shape2});
  auto input_npu = std::make_shared<ov::op::v0::Parameter>(
      ov::element::f16, ov::Shape{shape1_npu, shape2});
  auto input_gpu = std::make_shared<ov::op::v0::Parameter>(
      ov::element::f16, ov::PartialShape{ov::Dimension::dynamic(), shape2});

  // define and compile gpu function
  auto matmul_gpu =
      std::make_shared<ov::opset1::MatMul>(input_gpu, weight, false, true);
  auto result_gpu = std::make_shared<ov::op::v0::Result>(matmul_gpu);
  auto function_gpu = std::make_shared<ov::Model>(
      ov::ResultVector{result_gpu}, ov::ParameterVector{input_gpu});
  auto begin = std::chrono::steady_clock::now();
  auto compiled_model_gpu = core.compile_model(
      function_gpu, "GPU",
      ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT),
      ov::enable_profiling(allow_profile));
  auto gpu_compile_time = elapsed_time_us(begin);

  // define and compile npu function
  int64_t npu_compile_time = 0;
#ifdef TEST_NPU
  auto matmul_npu =
      std::make_shared<ov::opset1::MatMul>(input_npu, weight, false, true);
  auto result_npu = std::make_shared<ov::op::v0::Result>(matmul_npu);
  auto function_npu = std::make_shared<ov::Model>(
      ov::ResultVector{result_npu}, ov::ParameterVector{input_npu});
  begin = std::chrono::steady_clock::now();
  auto compiled_model_npu = core.compile_model(
      function_npu, "NPU",
      ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT),
      ov::enable_profiling(allow_profile));
  npu_compile_time = elapsed_time_us(begin);
#endif
#ifdef TEST_XPU
  auto matmul_xnpu =
      std::make_shared<ov::opset1::MatMul>(input_xnpu, weight, false, true);
  auto result_xnpu = std::make_shared<ov::op::v0::Result>(matmul_xnpu);
  auto function_xnpu = std::make_shared<ov::Model>(
      ov::ResultVector{result_xnpu}, ov::ParameterVector{input_xnpu});
  begin = std::chrono::steady_clock::now();
  auto compiled_model_xnpu = core.compile_model(
      function_xnpu, "NPU",
      ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT),
      ov::enable_profiling(allow_profile));
#endif

  // run npu and gpu alternatively to minimize interference
  std::vector<std::float16_t> input_data(shape1 * shape2);
  int64_t npu_time = 0;
  int64_t gpu_time = 0;
  auto gpu_infer_request = compiled_model_gpu.create_infer_request();
  gpu_infer_request.set_input_tensor(
      0, ov::Tensor(ov::element::f16, ov::Shape{shape1_gpu, shape2},
                    input_data.data()));
#ifdef TEST_NPU
  auto npu_infer_request = compiled_model_npu.create_infer_request();
  npu_infer_request.set_input_tensor(
      0, ov::Tensor(ov::element::f16, ov::Shape{shape1_npu, shape2},
                    input_data.data() + shape1_gpu * shape2));
#endif
#ifdef TEST_XPU
  auto xpu1_infer_request = compiled_model_gpu.create_infer_request();
  xpu1_infer_request.set_input_tensor(
      0, ov::Tensor(ov::element::f16, ov::Shape{shape1_gpu, shape2},
                    input_data.data()));
  auto xpu2_infer_request = compiled_model_xnpu.create_infer_request();
  xpu2_infer_request.set_input_tensor(
      0, ov::Tensor(ov::element::f16, ov::Shape{shape1_npu, shape2},
                    input_data.data() + shape1_gpu * shape2));
#endif

  // put GPU and NPU in a same container
  std::vector<ov::InferRequest> infer_requests;
  infer_requests.push_back(xpu1_infer_request);
  infer_requests.push_back(xpu2_infer_request);

  int64_t xpu_time = 0;
  int64_t xgpu_time = 0;
  int64_t xnpu_time = 0;
#ifdef TEST_XPU
  for (int i = 0; i < NUM_RUNS; ++i) {
    init_data(input_data);
    auto start = std::chrono::steady_clock::now();
    for (auto &ir : infer_requests) {
      ir.start_async();
    }
    // first barrier
    for (auto &ir : infer_requests) {
      ir.wait();
      // write_kernel_profile_info(ir);
      // auto devices =
      // ir.get_compiled_model().get_property(ov::execution_devices);
      // std::string device_name = devices.empty() ? "UNKNOWN" :
      // std::accumulate(devices.begin(), devices.end(), std::string(),
      // [](const std::string& a, const std::string& b) { return a.empty() ? b :
      // a + "," + b; }); std::vector<ov::ProfilingInfo> profiling_info =
      // ir.get_profiling_info(); for (const auto &info : profiling_info) {
      //   if(i > 0){
      //     if (device_name == "GPU.0")
      //         xgpu_time += info.real_time.count();
      //     else
      //         xnpu_time += info.real_time.count();
      //   }
      // }
    }
    if (i > 0) { // discard the first run
      xpu_time += elapsed_time_us(start);
    }
  }
  xpu_time /= (NUM_RUNS - 1);  // in us
  xgpu_time /= (NUM_RUNS - 1); // in us
  xnpu_time /= (NUM_RUNS - 1); // in us
#endif

  for (int i = 0; i < NUM_RUNS; ++i) {
    init_data(input_data);
    // run gpu
    begin = std::chrono::steady_clock::now();
    gpu_infer_request.infer();
    if (i > 0) { // discard the first run
      gpu_time += elapsed_time_us(begin);
    }

    // run npu
#ifdef TEST_NPU
    auto begin = std::chrono::steady_clock::now();
    npu_infer_request.infer();
    if (i > 0) { // discard the first run
      npu_time += elapsed_time_us(begin);
    }
#endif
  }
  npu_time /= (NUM_RUNS - 1); // in us
  gpu_time /= (NUM_RUNS - 1); // in us

  // get statistics
  size_t num_ops = 2 * shape1 * shape2 * shape3;
  double arith_intensity =
      (double)num_ops / ((shape1 * shape2 + shape1 * shape3 + shape2 * shape3) *
                         sizeof(std::float16_t));
  double gpu_tops = (double)num_ops / gpu_time / 1e6;
  double npu_tops = npu_time > 0 ? (double)num_ops / npu_time / 1e6 : -1;
  double xpu_tops = xpu_time > 0 ? (double)num_ops / xpu_time / 1e6 : -1;
  double gpu_tops_x = xgpu_time > 0 ? (double)num_ops / xgpu_time / 1e6 : -1;
  double npu_tops_x = xnpu_time > 0 ? (double)num_ops / xnpu_time / 1e6 : -1;

  std::cout << "Arithmetic intensity: " << arith_intensity << std::endl;
  std::cout << "GPU compile time (us): " << gpu_compile_time << std::endl;
  std::cout << "NPU compile time (us): " << npu_compile_time << std::endl;
  std::cout << "GPU runtime (us): " << gpu_time << std::endl;
  std::cout << "NPU runtime (us): " << npu_time << std::endl;
  std::cout << "GPU_NPU runtime (us): " << xpu_time << std::endl;
  std::cout << "GPU in GPU_NPU runtime (us): " << xgpu_time << std::endl;
  std::cout << "NPU in GPU_NPU runtime (us): " << xnpu_time << std::endl;
  std::cout << "GPU throughput (TOPS): " << gpu_tops << std::endl;
  std::cout << "NPU throughput (TOPS): " << npu_tops << std::endl;
  std::cout << "GPU_NPU throughput (TOPS): " << xpu_tops << std::endl;
  std::cout << "GPU in GPU_NPU throughput (TOPS): " << gpu_tops_x << std::endl;
  std::cout << "NPU in GPU_NPU throughput (TOPS): " << npu_tops_x << std::endl;

  return 0;
}