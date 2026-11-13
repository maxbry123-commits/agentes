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
  std::vector<uint16_t> input_data_npu =
      prepare_data<uint16_t>(a_dtype, npu_mm_k * W_DIM);
  std::vector<uint16_t> input_data_gpu =
      prepare_data<uint16_t>(a_dtype, gpu_mm_k * W_DIM);
  std::vector<uint16_t> output_data_npu(npu_mm_k * W_DIM);
  std::vector<uint16_t> output_data_gpu(gpu_mm_k * W_DIM);

  // create npu model
  auto input_npu = std::make_shared<ov::op::v0::Parameter>(
      a_dtype, ov::Shape{npu_mm_k, W_DIM});
  auto mm_npu =
      std::make_shared<ov::opset15::MatMul>(input_npu, weight, false, true);
  auto result_npu = std::make_shared<ov::op::v0::Result>(mm_npu);
  auto model_npu = std::make_shared<ov::Model>(ov::ResultVector{result_npu},
                                               ov::ParameterVector{input_npu});
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
  npu_infer_request.set_output_tensor(
      0,
      ov::Tensor(a_dtype, ov::Shape{npu_mm_k, W_DIM}, output_data_npu.data()));

  // create gpu model
  auto input_gpu = std::make_shared<ov::op::v0::Parameter>(
      a_dtype, ov::PartialShape{ov::Dimension::dynamic(), W_DIM});
  auto mm_gpu =
      std::make_shared<ov::opset15::MatMul>(input_gpu, weight, false, true);
  auto result_gpu = std::make_shared<ov::op::v0::Result>(mm_gpu);
  auto model_gpu = std::make_shared<ov::Model>(ov::ResultVector{result_gpu},
                                               ov::ParameterVector{input_gpu});
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
  gpu_infer_request.set_output_tensor(
      0,
      ov::Tensor(a_dtype, ov::Shape{gpu_mm_k, W_DIM}, output_data_gpu.data()));

    // colocate npu and gpu runs
  std::vector<ov::InferRequest> npu_infer_requests;
  std::vector<ov::InferRequest> gpu_infer_requests;
  for (int i = 0; i < npu_times; ++i) {
    auto req = model_npu_compiled.create_infer_request();
    req.set_input_tensor(0, ov::Tensor(a_dtype, ov::Shape{npu_mm_k, W_DIM},
                                       input_data_npu.data()));
    npu_infer_requests.push_back(req);
  }
  for (int i = 0; i < gpu_times; ++i) {
    auto req = model_gpu_compiled.create_infer_request();
    req.set_input_tensor(0, ov::Tensor(a_dtype, ov::Shape{gpu_mm_k, W_DIM},
                                       input_data_gpu.data()));
    gpu_infer_requests.push_back(req);
  }
  // reset_data<uint16_t>(input_data_npu, a_dtype);
  // reset_data<uint16_t>(input_data_gpu, a_dtype);
  int64_t npu_runtime_colocated = 0;
  int64_t gpu_runtime_colocated = 0;
  int64_t total_time_colocated = 0;

  begin = std::chrono::steady_clock::now();
  for (auto &req : npu_infer_requests) {
    req.start_async();
  }
  for (auto &req : gpu_infer_requests) {
    req.start_async();
  }
  for (auto &req : npu_infer_requests) {
    req.wait();
  }
  for (auto &req : gpu_infer_requests) {
    req.wait();
  }
  total_time_colocated = elapsed_time_us(begin);
  for (auto &req : npu_infer_requests) {
    npu_runtime_colocated += get_req_runtime_us(req);
    write_kernel_profile_info(req);
  }
  npu_runtime_colocated =
      npu_times > 0 ? npu_runtime_colocated / npu_times : 0; // in us
  for (auto &req : gpu_infer_requests) {
    gpu_runtime_colocated += get_req_runtime_us(req);
    write_kernel_profile_info(req);
  }
  gpu_runtime_colocated =
      gpu_times > 0 ? gpu_runtime_colocated / gpu_times : 0; // in us

  std::cout << "NPU colocated runtime (us): " << npu_runtime_colocated
            << std::endl;
  std::cout << "GPU colocated runtime (us): " << gpu_runtime_colocated
            << std::endl;
  std::cout << "Total time for colocated runs (us): " << total_time_colocated
            << std::endl;

}