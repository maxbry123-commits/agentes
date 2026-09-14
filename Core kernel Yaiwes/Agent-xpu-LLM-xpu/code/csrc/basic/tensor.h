#pragma once

#include "device.h"
#include "dtype.h"
#include "memory-block.h"
#include "opset.h"

#include <cassert>
#include <initializer_list>
#include <iostream>
#include <memory>
#include <vector>

typedef long offset_t;

#define HLLM_TENSOR_MAX_DIMS 4

namespace hllm {
enum { NO_ALLOC = 0, ALLOC = 1, ALLOC_ZERO = 2 };

class __Tensor;
using Tensor = std::shared_ptr<__Tensor>;
struct backend_t {
    InferDevice device;
    void* misc = nullptr;                       // pointer to any additional data
    void (*eval_callback)(__Tensor&) = nullptr; // this function will be called when eval is called,
                                                // *this will be passed to it
    void (*warmup_callback)(__Tensor&) = nullptr; // this function will be called before eval is
                                                  // called, *this will be passed to it
    void (*destroy_callback)(__Tensor&) = nullptr;
};

// Represents an N-dimensional tensor (up to 4D).
// This class provides information about the tensor's shape,
// data type, and the device where the data is stored.
// Data is stored in *row-major* order, with the last dimension being
// contiguous. All tensor operations should consider the stride, as the data may
// not always be contiguous in memory.
class __Tensor {
  public:
    // Set the data_ pointer to the given buffer. The buffer must be allocated
    // with the correct size (shape[0] * shape[1] * ... * shape[dims-1] *
    // dtype_size(dtype)).
    inline void set_data(std::shared_ptr<MemoryBlock> data) { data_ = data; }
    inline void set_data(__Tensor const& other) { data_ = other.data_; }
    inline void set_data(Tensor const& other) { data_ = other->data_; }
    char const* get_data() const { return data_->get_ptr(); }
    char* get_data() { return data_ ? data_->get_ptr() : nullptr; }
    size_t capacity() const { return data_ ? data_->get_size() : 0; }
    inline void allocate_data(bool alloc_zero = false) {
        data_ = std::make_shared<MemoryBlock>(size() * dtype_size(dtype_), alloc_zero);
    }
    // Copy the data from the given buffer to the tensor. The buffer must also be
    // allocated with the correct size.
    void copy_data(const void* data);

    InferDevice device() const {
        return backend_.eval_callback ? backend_.device : InferDevice::UNKNOWN;
    }
    Dtype dtype() const { return dtype_; }
    QuantType get_quant_type() const { return quant_type_; }
    void set_quant_type(QuantType quant_type) { quant_type_ = quant_type; }
    int dims() const { return dims_; }
    op_t op() const { return op_; }
    void set_op(op_t op) { op_ = op; }
    inline size_t shape_of(int dim) const {
        assert(("Invalid dimension" && dim < dims_ && dim >= -dims_));
        return shape_[dim >= 0 ? dim : dims_ + dim];
    }
    inline std::vector<size_t> shape() const {
        switch (dims_) {
            case 1:
                return {shape_[0]};
            case 2:
                return {shape_[0], shape_[1]};
            case 3:
                return {shape_[0], shape_[1], shape_[2]};
            case 4:
                return {shape_[0], shape_[1], shape_[2], shape_[3]};
            default:
                return {};
        }
    }
    size_t size() const { return shape_[0] * shape_[1] * shape_[2] * shape_[3]; }

    bool is_contiguous() const;

    offset_t strides(int dim) const {
        assert(("Invalid dimension" && dim < dims_));
        return strides_[dim];
    }
    std::vector<offset_t> stride() const {
        switch (dims_) {
            case 1:
                return {strides_[0]};
            case 2:
                return {strides_[0], strides_[1]};
            case 3:
                return {strides_[0], strides_[1], strides_[2]};
            case 4:
                return {strides_[0], strides_[1], strides_[2], strides_[3]};
            default:
                return {};
        }
    }
    size_t stride_bytes(int dim) const {
        assert(("Invalid dimension" && dim < dims_));
        return stride_bytes_[dim];
    }

    size_t offset(size_t i, size_t j = 0, size_t k = 0, size_t l = 0) const {
        return (i * strides_[0] + j * strides_[1] + k * strides_[2] + l * strides_[3]) + offset_;
    }

    char* at(size_t i, size_t j = 0, size_t k = 0, size_t l = 0) const {
        return (char*)(data_->get_ptr() + offset(i, j, k, l) * dtype_size(dtype_));
    }

    Tensor copy() const;
    __Tensor(Dtype dtype = Dtype::float32, std::vector<size_t> shape = {},
             int alloc_data = NO_ALLOC, const char* name = nullptr);

    void init_strides();

    void set_shape(std::initializer_list<size_t> shape);
    void set_shape(std::vector<size_t> shape);
    void set_shape(int dims, size_t dim0, size_t dim1 = 1, size_t dim2 = 1, size_t dim3 = 1);
    void set_offset(offset_t offset);
    offset_t offset() const { return offset_; }
    void set_strides(std::initializer_list<offset_t> strides);
    void set_strides(std::vector<offset_t> strides);
    void set_strides(offset_t stride0, offset_t stride1 = 0, offset_t stride2 = 0,
                     offset_t stride3 = 0);
    void set_name(const char* name) { name_ = name; }
    const char* name() const { return name_; }

    int get_group_size() const { return group_size_; }
    void set_group_size(int group_size) { group_size_ = group_size; }
    std::vector<float>& get_scales() { return scales_; }
    void copy_scales(const void* scales);

    // Create a view of the tensor with the given shape, stride and offset. The
    // new tensor shares underlying data with the original tensor.
    __Tensor view(std::initializer_list<size_t> shape, std::initializer_list<offset_t> strides,
                  offset_t offset = 0) const;

    // Make the tensor contiguous in memory.
    // The new tensor does not share the underlying data with the original tensor.
    __Tensor contiguous() const;

    /**
     * @brief Copy the data of the tensor to the contiguous tensor
     * @warning The shape of the tensor must be the same as the shape of the other
     * tensor. User must ensure this.
     */
    void contiguous(__Tensor& t) const;

    bool has_same_shape(const Tensor other) const;
    bool has_same_shape(const __Tensor& other) const;

    friend std::ostream& operator<<(std::ostream& os, const __Tensor& tensor);

    __Tensor as_type(Dtype dtype) const;

    void eval();

    // This function will be called before the first eval
    void warmup();

    void set_backend(backend_t backend) {
        if (backend_.destroy_callback) {
            backend_.destroy_callback(*this);
        }
        backend_ = backend;
    }

    void set_backend(InferDevice device, void (*eval_callback)(__Tensor&) = nullptr,
                     void (*warmup_callback)(__Tensor&) = nullptr,
                     void (*destroy_callback)(__Tensor&) = nullptr);

    backend_t& backend() { return backend_; }
    backend_t const& backend() const { return backend_; }

    template <typename T> T& options() { return *reinterpret_cast<T*>(options_.get()); }
    template <typename T> T const& options() const { return *reinterpret_cast<T*>(options_.get()); }
    template <typename T> void set_options(T const& options) {
        options_ = std::shared_ptr<char[]>(new char[sizeof(T)]);
        *reinterpret_cast<T*>(options_.get()) = options;
    }
    std::vector<Tensor>& src() { return src_; }
    std::vector<Tensor> const& src() const { return src_; }
    bool& modified() { return modified_; }
    bool const& modified() const { return modified_; }
    ~__Tensor();

#if DEBUG_MODE
    int debug_id = 0;
#endif

  private:
    Dtype dtype_ = Dtype::unknown;
    QuantType quant_type_ = QuantType::none;
    int dims_ = 0;
    size_t shape_[HLLM_TENSOR_MAX_DIMS] = {1, 1, 1, 1}; // shape of the tensor
    offset_t offset_ = 0;
    offset_t strides_[HLLM_TENSOR_MAX_DIMS] = {0};      // stride of each dimension
    offset_t stride_bytes_[HLLM_TENSOR_MAX_DIMS] = {0}; // stride of each dimension in bytes

    std::shared_ptr<MemoryBlock> data_ = nullptr;
    // Example of data access via the "data" pointer:
    //  data_[i * stride_[0] + j * stride_[1] + k * stride_[2] + l * stride_[3]]
    //  where i, j, k, l are the indices of the tensor.

    op_t op_ = op_t::PARAM;

    std::vector<Tensor> src_;

    backend_t backend_;

    // pointer to additional metadate, using malloc and free, will be freed in the
    // destructor must be set to nullptr if freed
    std::shared_ptr<char[]> options_ = nullptr;

    // Some operators are inplace operators, so for these operators must
    // invalidate the source tensor
    bool modified_ = false;

    const char* name_ = nullptr;

    // quantization parameters
    int group_size_ = 0;
    std::vector<float> scales_;

    void fill_stride_bytes();
    template <typename FromType, typename ToType>
    friend void copy_data(const __Tensor& src, __Tensor& dst);
};
Tensor create_param(Dtype dtype = Dtype::float32, std::vector<size_t> shape = {},
                    int alloc_data = NO_ALLOC, const char* name = nullptr);

/**
 * @brief Create a tensor with the given shape and data type. Although you can
 * provide it's data later, it is deemed as a constant which means that the data
 * will not be changed.
 */
Tensor create_constant(Dtype dtype = Dtype::float32, std::vector<size_t> shape = {},
                       int alloc_data = ALLOC_ZERO, const char* name = nullptr);
std::ostream& operator<<(std::ostream& os, const Tensor& tensor);
} // namespace hllm
