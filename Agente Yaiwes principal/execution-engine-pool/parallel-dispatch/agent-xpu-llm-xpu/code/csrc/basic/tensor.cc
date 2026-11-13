#include "tensor.h"

#include <cstring>
#include <iostream>
#include <numeric>

namespace hllm {
std::ostream& operator<<(std::ostream& os, const __Tensor& tensor) {
    static constexpr int MAX_ELEMENTS = 12;

    os << "Tensor(name=" << (tensor.name() ? tensor.name() : "None") << ", shape=[";
    for (int i = 0; i < tensor.dims(); ++i) {
        os << tensor.shape_of(i);
        if (i < tensor.dims() - 1) {
            os << ", ";
        }
    }
    os << "], dtype=" << static_cast<int>(tensor.dtype())
       << ", device=" << static_cast<int>(tensor.device()) << ", data=[";

    size_t total_elements = tensor.size();

    // assert("Not support discontiguous tensor" && tensor.is_contiguous());
    assert("Not implemented Printing Function" && (tensor.dtype_ == Dtype::float32));

    if (tensor.dtype_ == Dtype::float32) {
        if (total_elements > MAX_ELEMENTS) {
            size_t segment = MAX_ELEMENTS / 3;
            for (size_t i = 0; i < segment; ++i) {
                os << reinterpret_cast<const float*>(tensor.at(0))[i] << ", ";
            }
            os << "... , ";
            for (size_t i = total_elements / 2 - segment / 2; i < total_elements / 2 + segment / 2;
                 ++i) {
                os << reinterpret_cast<const float*>(tensor.at(0))[i] << ", ";
            }
            os << "... , ";
            for (size_t i = total_elements - segment; i < total_elements; ++i) {
                os << reinterpret_cast<const float*>(tensor.at(0))[i];
                if (i < total_elements - 1) {
                    os << ", ";
                }
            }
        } else {
            for (size_t i = 0; i < total_elements; ++i) {
                os << reinterpret_cast<const float*>(tensor.at(0))[i];
                if (i < total_elements - 1) {
                    os << ", ";
                }
            }
        }
    } else {
        // raise not implemented error
        throw std::runtime_error("Tensor printing not implemented for this dtype");

        // if (total_elements > MAX_ELEMENTS) {
        //   size_t segment = MAX_ELEMENTS / 3;
        //   for (size_t i = 0; i < segment; ++i) {
        //     os << reinterpret_cast<const std::float16_t *>(tensor.at(0))[i] << ", ";
        //   }
        //   os << "... , ";
        //   for (size_t i = total_elements / 2 - segment / 2;
        //        i < total_elements / 2 + segment / 2; ++i) {
        //     os << reinterpret_cast<const std::float16_t *>(tensor.at(0))[i] << ", ";
        //   }
        //   os << "... , ";
        //   for (size_t i = total_elements - segment; i < total_elements; ++i) {
        //     os << reinterpret_cast<const std::float16_t *>(tensor.at(0))[i];
        //     if (i < total_elements - 1) {
        //       os << ", ";
        //     }
        //   }
        // } else {
        //   for (size_t i = 0; i < total_elements; ++i) {
        //     os << reinterpret_cast<const std::float16_t *>(tensor.at(0))[i];
        //     if (i < total_elements - 1) {
        //       os << ", ";
        //     }
        //   }
        // }
    }
    os << "])";
    return os;
}

Tensor create_param(Dtype dtype, std::vector<size_t> shape, int alloc_data, const char* name) {
    return std::make_shared<__Tensor>(dtype, shape, alloc_data, name);
}

Tensor create_constant(Dtype dtype, std::vector<size_t> shape, int alloc_data, const char* name) {
    auto t = std::make_shared<__Tensor>(dtype, shape, alloc_data, name);
    t->set_op(op_t::CONSTANT);
    return t;
}

std::ostream& operator<<(std::ostream& os, const Tensor& tensor) {
    return tensor ? os << *tensor.get() : os;
}

void __Tensor::copy_data(const void* data) {
    if (data_ == nullptr) {
        this->allocate_data();
    }
    memcpy(data_->get_ptr(), data, size() * dtype_size(dtype_));
}

void __Tensor::copy_scales(const void* scales) {
    assert(("Group size is not set" && group_size_ > 0));
    int group_count = 0;
    if (dtype_ == Dtype::int8) {
        assert(("Tensor size should be divisible by group size" && size() % group_size_ == 0));
        group_count = size() / group_size_;
    } else if (dtype_ == Dtype::int4) {
        assert(
            ("Tensor size should be divisible by group size" && (size() * 2) % group_size_ == 0));
        group_count = size() * 2 / group_size_;
    } else {
        assert(("Unsupported quantization type" && false));
    }
    if (scales_.empty()) {
        scales_.resize(group_count);
    }
    memcpy(scales_.data(), scales, group_count * sizeof(float));
}

void __Tensor::init_strides() {
    strides_[dims_ - 1] = 1;
    for (int i = dims_ - 2; i >= 0; i--) {
        strides_[i] = shape_[i + 1] * strides_[i + 1];
    }
    fill_stride_bytes();
}

void __Tensor::set_shape(std::initializer_list<size_t> shape) {
    set_shape(std::vector<size_t>(shape));
}

void __Tensor::set_shape(std::vector<size_t> shape) {
    int dim = shape.size();
    assert(("Invalid number of dimensions" && dim > 0 && dim <= HLLM_TENSOR_MAX_DIMS));
    auto it = shape.begin();
    for (int i = 0; i < HLLM_TENSOR_MAX_DIMS; i++) {
        shape_[i] = i < dim ? *it++ : 1;
    }
    this->dims_ = dim;
}

void __Tensor::set_shape(int dims, size_t dim0, size_t dim1, size_t dim2, size_t dim3) {
    dims_ = dims;
    shape_[0] = dim0;
    shape_[1] = dim1;
    shape_[2] = dim2;
    shape_[3] = dim3;
}
void __Tensor::set_offset(offset_t offset) { offset_ = offset; }

void __Tensor::set_strides(std::initializer_list<offset_t> stride) {
    set_strides(std::vector<offset_t>(stride));
}

void __Tensor::set_strides(std::vector<offset_t> stride) {
    int dim = stride.size();
    assert(("Invalid number of dimensions" && dim > 0 && dim <= HLLM_TENSOR_MAX_DIMS &&
            dim == this->dims_));
    auto it = stride.begin();
    for (int i = 0; i < HLLM_TENSOR_MAX_DIMS; i++) {
        strides_[i] = i < dim ? *it++ : 1;
    }
    fill_stride_bytes();
}

void __Tensor::fill_stride_bytes() {
    for (int i = 0; i < dims_; i++) {
        stride_bytes_[i] = strides_[i] * dtype_size(dtype_);
    }
}

void __Tensor::set_strides(offset_t stride0, offset_t stride1, offset_t stride2, offset_t stride3) {
    strides_[0] = stride0;
    strides_[1] = stride1;
    strides_[2] = stride2;
    strides_[3] = stride3;
    fill_stride_bytes();
}

__Tensor __Tensor::view(std::initializer_list<size_t> shape, std::initializer_list<offset_t> stride,
                        offset_t offset) const {
    std::vector<size_t> shape_vec(shape);
    if (*shape_vec.begin() == 0) {
        *shape_vec.begin() = this->size() / std::accumulate(shape_vec.begin() + 1, shape_vec.end(),
                                                            1, std::multiplies<size_t>());
    }

    __Tensor t = __Tensor(dtype_, shape_vec, NO_ALLOC);
    t.set_strides(stride);
    t.set_offset(offset);
    t.data_ = data_;
    return t;
}

__Tensor __Tensor::contiguous() const {
    __Tensor t = __Tensor(dtype_, {shape_[0], shape_[1], shape_[2], shape_[3]});
    t.op_ = op_;
    t.init_strides();
    t.set_data(std::make_shared<MemoryBlock>(t.size() * dtype_size(dtype_)));
    this->contiguous(t);
    return t;
}

void __Tensor::contiguous(__Tensor& t) const {

    for (size_t i = 0; i < shape_[0]; i++) {
        for (size_t j = 0; j < shape_[1]; j++) {
            for (size_t k = 0; k < shape_[2]; k++) {
                for (size_t l = 0; l < shape_[3]; l++) {
                    memcpy(t.at(i, j, k, l), at(i, j, k, l), dtype_size(dtype_));
                }
            }
        }
    }
}

Tensor __Tensor::copy() const {
    Tensor t = create_param(dtype_, {shape_[0], shape_[1], shape_[2], shape_[3]});
    for (int i = 0; i < dims_; i++) {
        t->shape_[i] = shape_[i];
        t->strides_[i] = strides_[i];
        t->stride_bytes_[i] = stride_bytes_[i];
    }
    t->offset_ = offset_;
    if (data_ != nullptr) {
        t->copy_data(data_->get_ptr());
    }
    t->set_op(op_);
    t->set_quant_type(quant_type_);
    t->set_group_size(group_size_);
    t->scales_ = scales_;
    t->set_name(name_);
    return t;
}

__Tensor::__Tensor(Dtype dtype, std::vector<size_t> shape, int alloc_data, const char* name) {
    int dim = shape.size();
    dtype_ = dtype;
    dims_ = dim;
    this->set_name(name);
    this->set_shape(shape);
    this->init_strides();
    switch (alloc_data) {
        case hllm::ALLOC:
            this->allocate_data();
            break;
        case hllm::ALLOC_ZERO:
            this->allocate_data(true);
            break;
        default:
            break;
    }
}

bool __Tensor::is_contiguous() const {
    if (strides_[dims_ - 1] != 1) {
        return false;
    }
    for (int i = dims_ - 2; i >= 0; i--) {
        if (strides_[i] != (offset_t)shape_[i + 1] * strides_[i + 1]) {
            return false;
        }
    }
    return true;
}

bool __Tensor::has_same_shape(const Tensor other) const { return has_same_shape(*other.get()); }

bool __Tensor::has_same_shape(const __Tensor& other) const {
    if (dims_ != other.dims_) {
        return false;
    }
    for (int i = 0; i < dims_; i++) {
        if (shape_[i] != other.shape_[i]) {
            return false;
        }
    }
    return true;
}

template <typename FromType, typename ToType> void copy_data(const __Tensor& src, __Tensor& dst) {
    for (size_t i = 0; i < src.shape_of(0); i++) {
        for (size_t j = 0; j < src.shape_of(1); j++) {
            for (size_t k = 0; k < src.shape_of(2); k++) {
                for (size_t l = 0; l < src.shape_of(3); l++) {
                    *(ToType*)dst.at(i, j, k, l) = (ToType) * (FromType*)src.at(i, j, k, l);
                }
            }
        }
    }
}

__Tensor __Tensor::as_type(Dtype dtype) const {
    std::throw_with_nested(
        std::runtime_error("This function is under development and not callable at this moment"));

    // if (dtype == dtype_) {
    //     return *this;
    // }

    // __Tensor t = *this;
    // t.set_data(std::make_shared<MemoryBlock>(t.size() * dtype_size(dtype)));
    // assert(("Not implemented for this dtype" && dtype_ == Dtype::float16));
    // switch (dtype) {
    //     case Dtype::float32:
    //         hllm::copy_data<std::float16_t, float>(*this, t);
    //         break;
    //     default:
    //         assert(("Not implemented for this dtype" && false));
    //         break;
    // }
    // return t;
}

void __Tensor::eval() {
    if (backend_.eval_callback) {
        backend_.eval_callback(*this);
    }
}

void __Tensor::warmup() {
    if (backend_.warmup_callback) {
        backend_.warmup_callback(*this);
    }
}

void __Tensor::set_backend(InferDevice device, void (*eval_callback)(__Tensor&),
                           void (*warmup_callback)(__Tensor&),
                           void (*destroy_callback)(__Tensor&)) {
    backend_.device = device;
    backend_.eval_callback = eval_callback;
    backend_.warmup_callback = warmup_callback;
    backend_.destroy_callback = destroy_callback;
}

__Tensor::~__Tensor() {
    if (backend_.destroy_callback) {
        backend_.destroy_callback(*this);
    }
}
} // namespace hllm