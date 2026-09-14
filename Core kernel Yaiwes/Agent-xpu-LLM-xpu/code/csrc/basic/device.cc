#include "device.h"

#include <cstring>

namespace hllm {

InferDevice get_infer_device(const char* device) {
    if (strcmp(device, "AUTO") == 0 || strcmp(device, "auto") == 0) {
        return hllm::InferDevice::AUTO;
    } else if (strcmp(device, "CPU") == 0 || strcmp(device, "cpu") == 0) {
        return hllm::InferDevice::CPU;
    } else if (strcmp(device, "IntelHetero") == 0 || strcmp(device, "intel-hetero") == 0) {
        return hllm::InferDevice::IntelHetero;
    } else if (strcmp(device, "IntelNPU") == 0 || strcmp(device, "intel-npu") == 0) {
        return hllm::InferDevice::IntelNPU;
    } else if (strcmp(device, "IntelGPU") == 0 || strcmp(device, "intel-gpu") == 0) {
        return hllm::InferDevice::IntelGPU;
    } else if (strcmp(device, "AmdNPU") == 0 || strcmp(device, "amd-npu") == 0) {
        return hllm::InferDevice::AmdNPU;
    } else if (strcmp(device, "CUDA") == 0 || strcmp(device, "cuda") == 0) {
        return hllm::InferDevice::CUDA;
    } else {
        return hllm::InferDevice::UNKNOWN;
    }
}

const char* get_infer_device_name(InferDevice device) {
    switch (device) {
        case hllm::InferDevice::AUTO:
            return "AUTO";
        case hllm::InferDevice::CPU:
            return "CPU";
        case hllm::InferDevice::IntelHetero:
            return "Intel (NPU and GPU)";
        case hllm::InferDevice::IntelNPU:
            return "Intel NPU";
        case hllm::InferDevice::IntelGPU:
            return "Intel GPU";
        case hllm::InferDevice::AmdNPU:
            return "AMD NPU";
        case hllm::InferDevice::CUDA:
            return "CUDA";
        default:
            return "UNKNOWN";
    }
}

} // namespace hllm