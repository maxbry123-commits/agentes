#pragma once

#include <cstddef>
#include <iostream>

#ifndef INT8_MAX
#define INT8_MAX 127
#endif
#ifndef INT4_MAX
#define INT4_MAX 7
#endif

// Enum class representing the supported NN data types.
namespace hllm {
enum class Dtype { float32, float16, bfloat16, int32, int16, int8, uint8, int4, uint4, unknown };

enum class QuantType { none, w4a32, w8a32, w8a16 };

enum class InferStage { prefill, decode, both };

enum class JobPriority { proactive, reactive, none };

// Returns the size of the given NN dtype in bytes.
size_t dtype_size(Dtype dtype);

// Stream operator overload for Dtype
inline std::ostream& operator<<(std::ostream& os, const Dtype& dtype) {
    switch (dtype) {
        case Dtype::float32:
            os << "float32";
            break;
        case Dtype::float16:
            os << "float16";
            break;
        case Dtype::bfloat16:
            os << "bfloat16";
            break;
        case Dtype::int32:
            os << "int32";
            break;
        case Dtype::int16:
            os << "int16";
            break;
        case Dtype::int8:
            os << "int8";
            break;
        case Dtype::uint8:
            os << "uint8";
            break;
        case Dtype::int4:
            os << "int4";
            break;
        case Dtype::uint4:
            os << "uint4";
            break;
        case Dtype::unknown:
            os << "unknown";
            break;
        default:
            os << "unknown";
            break;
    }
    return os;
}

// Stream operator overload for QuantType
inline std::ostream& operator<<(std::ostream& os, const QuantType& quant_type) {
    switch (quant_type) {
        case QuantType::none:
            os << "none";
            break;
        case QuantType::w4a32:
            os << "w4a32";
            break;
        case QuantType::w8a32:
            os << "w8a32";
            break;
        case QuantType::w8a16:
            os << "w8a16";
            break;
        default:
            os << "unknown";
            break;
    }
    return os;
}

// Stream operator overload for InferStage
inline std::ostream& operator<<(std::ostream& os, const InferStage& stage) {
    switch (stage) {
        case InferStage::prefill:
            os << "prefill";
            break;
        case InferStage::decode:
            os << "decode";
            break;
        case InferStage::both:
            os << "both";
            break;
        default:
            os << "unknown";
            break;
    }
    return os;
}

// Stream operator overload for JobPriority
inline std::ostream& operator<<(std::ostream& os, const JobPriority& priority) {
    switch (priority) {
        case JobPriority::proactive:
            os << "proactive";
            break;
        case JobPriority::reactive:
            os << "reactive";
            break;
        case JobPriority::none:
            os << "none";
            break;
        default:
            os << "unknown";
            break;
    }
    return os;
}

} // namespace hllm