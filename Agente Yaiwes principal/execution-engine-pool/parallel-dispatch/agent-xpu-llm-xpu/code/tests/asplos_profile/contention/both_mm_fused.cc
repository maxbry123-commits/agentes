#include "../util.h"
#include <iostream>
#include <openvino/opsets/opset1.hpp>
#include <openvino/opsets/opset15.hpp>

constexpr size_t W_DIM = 4096;
auto w_dtype = ov::element::f16;
auto a_dtype = ov::element::f16;
size_t npu_mm_k;
size_t gpu_mm_k;
int npu_times;
int gpu_times;

int main(int argc, char **argv) {
  if (argc != 5) {
    std::cout << "Usage: " << argv[0]
              << " <npu_mm_k> <npu_times> <gpu_mm_k> <gpu_times>" << std::endl;
    return 1;
  }
  npu_mm_k = std::stoul(argv[1]);
  npu_times = std::stoi(argv[2]);
  gpu_mm_k = std::stoul(argv[3]);
  gpu_times = std::stoi(argv[4]);

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
  std::vector<uint16_t> weight_data =
      prepare_data<uint16_t>(w_dtype, W_DIM * W_DIM);
  auto weight = std::make_shared<ov::op::v0::Constant>(
      w_dtype, ov::Shape{W_DIM, W_DIM}, weight_data.data());
  std::vector<uint16_t> weight_data1 = 
        prepare_data<uint16_t>(w_dtype, W_DIM * W_DIM);
  auto weight1 = std::make_shared<ov::op::v0::Constant>(
    w_dtype, ov::Shape{W_DIM, W_DIM}, weight_data1.data());
  std::vector<uint16_t> input_data_npu =
      prepare_data<uint16_t>(a_dtype, npu_mm_k * W_DIM);
  std::vector<uint16_t> input_data_gpu =
      prepare_data<uint16_t>(a_dtype, gpu_mm_k * W_DIM);

  // create npu model
  auto npu_input = std::make_shared<ov::op::v0::Parameter>(
      a_dtype, ov::Shape{npu_mm_k, W_DIM});
  std::vector<std::shared_ptr<ov::opset15::MatMul>> npu_mms(npu_times);
  npu_mms[0] =
      std::make_shared<ov::opset15::MatMul>(npu_input, weight, false, true);
  for (int i = 1; i < npu_times; ++i) {
    npu_mms[i] = std::make_shared<ov::opset15::MatMul>(
        npu_mms[i - 1]->output(0), weight, false, true);
  }
  auto npu_result = std::make_shared<ov::op::v0::Result>(npu_mms.back());
  auto model_npu = std::make_shared<ov::Model>(ov::ResultVector{npu_result},
                                               ov::ParameterVector{npu_input});
  auto begin = std::chrono::steady_clock::now();
  auto model_npu_compiled =
      core.compile_model(model_npu, "NPU", ov::enable_profiling(allow_profile));
  int64_t npu_compile_time = elapsed_time_us(begin);
  std::cout << "Finish NPU compile, time (us): " << npu_compile_time
            << std::endl;
  auto npu_infer_request = model_npu_compiled.create_infer_request();
  npu_infer_request.set_input_tensor(
      0,
      ov::Tensor(a_dtype, ov::Shape{npu_mm_k, W_DIM}, input_data_npu.data()));

  // create gpu model
  auto gpu_input = std::make_shared<ov::op::v0::Parameter>(
      a_dtype, ov::PartialShape{ov::Dimension::dynamic(), W_DIM});
  std::vector<std::shared_ptr<ov::opset15::MatMul>> gpu_mms(gpu_times);
  gpu_mms[0] =
      std::make_shared<ov::opset15::MatMul>(gpu_input, weight1, false, true);
  for (int i = 1; i < gpu_times; ++i) {
    gpu_mms[i] = std::make_shared<ov::opset15::MatMul>(
        gpu_mms[i - 1]->output(0), weight, false, true);
  }
  auto gpu_result = std::make_shared<ov::op::v0::Result>(gpu_mms.back());
  auto model_gpu = std::make_shared<ov::Model>(ov::ResultVector{gpu_result},
                                               ov::ParameterVector{gpu_input});
  begin = std::chrono::steady_clock::now();
  auto model_gpu_compiled =
      core.compile_model(model_gpu, "GPU", ov::enable_profiling(allow_profile));
  int64_t gpu_compile_time = elapsed_time_us(begin);
  std::cout << "Finish GPU compile, time (us): " << gpu_compile_time
            << std::endl;
  auto gpu_infer_request = model_gpu_compiled.create_infer_request();
  gpu_infer_request.set_input_tensor(
      0,
      ov::Tensor(a_dtype, ov::Shape{gpu_mm_k, W_DIM}, input_data_gpu.data()));

  // standalone npu or gpu run
  int64_t npu_runtime_alone_profiler = 0;
  int64_t npu_runtime_alone_e2e = 0;
  int64_t gpu_runtime_alone_profiler = 0;
  int64_t gpu_runtime_alone_e2e = 0;

  begin = std::chrono::steady_clock::now();
  npu_infer_request.infer();
  npu_runtime_alone_e2e = elapsed_time_us(begin) / npu_times;
  npu_runtime_alone_profiler =
      get_req_runtime_us(npu_infer_request) / npu_times;
  write_kernel_profile_info(npu_infer_request);
  std::cout << "NPU alone runtime (us): " << npu_runtime_alone_e2e << std::endl;
  std::cout << "NPU alone profiler runtime (us): " << npu_runtime_alone_profiler
            << std::endl;

  sleep_seconds(2);

  begin = std::chrono::steady_clock::now();
  gpu_infer_request.infer();
  gpu_runtime_alone_e2e = elapsed_time_us(begin) / gpu_times;
  gpu_runtime_alone_profiler =
      get_req_runtime_us(gpu_infer_request) / gpu_times;
  write_kernel_profile_info(gpu_infer_request);
  std::cout << "GPU alone runtime (us): " << gpu_runtime_alone_e2e << std::endl;
  std::cout << "GPU alone profiler runtime (us): " << gpu_runtime_alone_profiler
            << std::endl;
  std::cout << "Total time for dist runs (us): "
            << npu_runtime_alone_e2e * npu_times +
                   gpu_runtime_alone_e2e * gpu_times
            << std::endl;
  sleep_seconds(2);

  // colocated npu and gpu run
  int64_t npu_runtime_colocated_profiler = 0;
  int64_t gpu_runtime_colocated_profiler = 0;
  int64_t hetero_runtime_e2e = 0;

  begin = std::chrono::steady_clock::now();
  npu_infer_request.start_async();
  gpu_infer_request.start_async();
  npu_infer_request.wait();
  gpu_infer_request.wait();
  hetero_runtime_e2e = elapsed_time_us(begin);
  npu_runtime_colocated_profiler =
      get_req_runtime_us(npu_infer_request) / npu_times;
  gpu_runtime_colocated_profiler =
      get_req_runtime_us(gpu_infer_request) / gpu_times;
  write_kernel_profile_info(npu_infer_request);
  write_kernel_profile_info(gpu_infer_request);

  std::cout << "NPU colocated profiler runtime (us): "
            << npu_runtime_colocated_profiler << std::endl;
  std::cout << "GPU colocated profiler runtime (us): "
            << gpu_runtime_colocated_profiler << std::endl;
  std::cout << "Total time for colocated runs (us): " << hetero_runtime_e2e
            << std::endl;
}
