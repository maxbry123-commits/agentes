#include "dtype.h"

#include <stdexcept>

namespace hllm {
size_t dtype_size(Dtype dtype) {
    switch (dtype) {
        case Dtype::float32:
            return 4;
            break;
        case Dtype::float16:
            return 2;
            break;
        case Dtype::bfloat16:
            return 2;
            break;
        case Dtype::int32:
            return 4;
            break;
        case Dtype::int16:
            return 2;
            break;
        case Dtype::int8:
            return 1;
            break;
        case Dtype::uint8:
            return 1;
            break;
        case Dtype::int4:
            throw std::runtime_error("dtype_size not implemented for int4");
            break;
        case Dtype::uint4:
            throw std::runtime_error("dtype_size not implemented for uint4");
            break;
        default:
            return 0;
    }
}

} // namespace hllm