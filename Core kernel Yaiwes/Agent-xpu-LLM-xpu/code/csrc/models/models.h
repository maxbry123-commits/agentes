#pragma once

#include <iostream>
namespace hllm {
enum class ModelType {
    Llama2,
    Llama3,
};

inline std::ostream& operator<<(std::ostream& os, const ModelType& model_type) {
    switch (model_type) {
        case ModelType::Llama2:
            os << "Llama2";
            break;
        case ModelType::Llama3:
            os << "Llama3";
            break;
        default:
            os << "unknown";
            break;
    }
    return os;
}
} // namespace hllm