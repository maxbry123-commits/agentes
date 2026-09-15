#pragma once

#include "basic/device.h"
#include "basic/dtype.h"

#include <openvino/openvino.hpp>
#include <string>
#include <unordered_map>
#include <vector>

namespace hllm {
ov::element::Type get_ov_dtype(hllm::Dtype dtype);
std::vector<std::string> get_ov_devices(ov::Core& core);
std::unordered_map<std::string, std::string> get_ov_device_info(ov::Core& core);
void print_ov_device_info(ov::Core& core, InferDevice device);
void check_ov_infer_device(ov::Core& core, InferDevice device);
} // namespace hllm