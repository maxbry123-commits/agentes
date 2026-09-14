#include "backend.h"

#include "utils/logging.h"

#include <stdexcept>

static std::string get_any_value_str(const ov::Any& value) {
    if (value.empty()) {
        return "EMPTY VALUE";
    } else {
        std::string stringValue = value.as<std::string>();
        return stringValue.empty() ? "\"\"" : stringValue;
    }
}

namespace hllm {

ov::element::Type get_ov_dtype(hllm::Dtype dtype) {
    switch (dtype) {
        case hllm::Dtype::float32:
            return ov::element::f32;
        case hllm::Dtype::float16:
            return ov::element::f16;
        case hllm::Dtype::int32:
            return ov::element::i32;
        case hllm::Dtype::int8:
            return ov::element::i8;
        case hllm::Dtype::int4:
            return ov::element::i4;
        default:
            std::throw_with_nested(std::invalid_argument("Unsupported dtype for OpenVINO"));
            return ov::element::dynamic;
    }
}

std::vector<std::string> get_ov_devices(ov::Core& core) { return core.get_available_devices(); }

std::unordered_map<std::string, std::string> get_ov_device_info(ov::Core& core) {
    std::unordered_map<std::string, std::string> available_devices;
    std::vector<std::string> avail_devices = core.get_available_devices();
    for (auto&& device : avail_devices) {
        std::stringstream ss;
        auto properties = core.get_property(device, ov::supported_properties);
        for (auto&& property : properties) {
            if (property != ov::supported_properties.name()) {
                ss << "\t" << property << " : "
                   << get_any_value_str(core.get_property(device, property))
                   << (property.is_mutable() ? " (Mutable)" : " (Immutable)") << std::endl;
            }
        }
        available_devices[device] = ss.str();
    }
    return available_devices;
}

void print_ov_device_info(ov::Core& core, InferDevice device) {
    switch (device) {
        case InferDevice::IntelHetero: {
            logging::info() << "Available devices: " << get_infer_device_name(device);
            for (auto&& [dev, info] : get_ov_device_info(core)) {
                if (dev == "NPU" || dev == "GPU") {
                    logging::info() << "Device: " << dev << "\n" << info;
                }
            }
            break;
        }
        case InferDevice::IntelNPU: {
            logging::info() << "Available devices: " << get_infer_device_name(device);
            for (auto&& [dev, info] : get_ov_device_info(core)) {
                if (dev == "NPU") {
                    logging::info() << "Device: " << dev << "\n" << info;
                }
            }
            break;
        }
        case InferDevice::IntelGPU: {
            logging::info() << "Available devices: " << get_infer_device_name(device);
            for (auto&& [dev, info] : get_ov_device_info(core)) {
                if (dev == "GPU") {
                    logging::info() << "Device: " << dev << "\n" << info;
                }
            }
            break;
        }
        default:
            logging::error() << "Try to print info of an non-intel device";
            break;
    }
}

void check_ov_infer_device(ov::Core& core, InferDevice device) {
    switch (device) {
        case hllm::InferDevice::IntelHetero: {
            std::vector<std::string> devices = get_ov_devices(core);
            if (std::find(devices.begin(), devices.end(), "NPU") == devices.end()) {
                logging::error() << "Intel NPU not found";
                return;
            } else if (std::find(devices.begin(), devices.end(), "GPU") == devices.end()) {
                logging::error() << "Intel GPU not found";
                return;
            } else {
                return;
            }
        }

        case hllm::InferDevice::IntelNPU: {
            std::vector<std::string> devices = get_ov_devices(core);
            if (std::find(devices.begin(), devices.end(), "NPU") == devices.end()) {
                logging::error() << "No Intel NPU found";
                return;
            } else {
                return;
            }
        }

        case hllm::InferDevice::IntelGPU: {
            std::vector<std::string> devices = get_ov_devices(core);
            if (std::find(devices.begin(), devices.end(), "GPU") == devices.end()) {
                logging::error() << "No Intel GPU found";
                return;
            } else {
                return;
            }
        }

        default: {
            logging::error() << "Unknown or non-intel device";
            return;
        }
    }
}

} // namespace hllm