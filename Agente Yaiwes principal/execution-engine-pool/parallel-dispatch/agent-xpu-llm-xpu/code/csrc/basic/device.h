#pragma once

namespace hllm {

enum class InferDevice {
    AUTO,        // Automatically select the device
    CPU,         // Use CPU
    IntelHetero, // Hetero infer w/ Intel NPU and GPU
    IntelNPU,    // Use Intel NPU
    IntelGPU,    // Use Intel GPU
    AmdNPU,      // Use AMD NPU
    CUDA,        // Use CUDA
    UNKNOWN
};

InferDevice get_infer_device(const char* device);
const char* get_infer_device_name(InferDevice device);

} // namespace hllm
