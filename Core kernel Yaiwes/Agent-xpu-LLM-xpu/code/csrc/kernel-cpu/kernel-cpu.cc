#include "kernel-cpu.h"

namespace hllm {
static void __transpose(__Tensor& t) {
    // if (t.options<transpose_options>().copy) {
    //   // TODO: Implement copy
    //   throw std::runtime_error("Copy not implemented");
    // } else {
    //   t.set_data(*t.src()[0].get());
    //   t.set_offset(t.src()[0]->offset());
    // }
}

static void __view(__Tensor& t) {
    // if (t.options<view_options>().copy) {
    //   // TODO: Implement copy
    //   throw std::runtime_error("Copy not implemented");
    // } else {
    //   t.set_data(*t.src()[0].get());
    //   t.set_offset(t.options<view_options>().offset);
    //   assert(t.options<view_options>().shape[0] < 100000);
    //   t.set_shape(t.options<view_options>().dims, t.options<view_options>().shape[0],
    //   t.options<view_options>().shape[1],
    //               t.options<view_options>().shape[2], t.options<view_options>().shape[3]);
    //   t.set_strides(t.options<view_options>().strides[0], t.options<view_options>().strides[1],
    //   t.options<view_options>().strides[2],
    //                 t.options<view_options>().strides[3]);
    // }
}

static void __contiguous(__Tensor& t) {
    __Tensor& x = *t.src()[0].get();
    x.contiguous(t);
}

void kernel_cpu::set_kernel(Tensor& t) {
    switch (t->op()) {
        case op_t::PARAM:
        case op_t::CONSTANT:
            break;
        case op_t::MAT_ADD:
            t->set_backend(DeviceType::CPU, mat_add, __alloc_memory_warmup);
            break;
        case op_t::MAT_MUL:
            t->set_backend(DeviceType::CPU, mat_mul, __alloc_memory_warmup);
            break;
        case op_t::MAT_SCALE:
            t->set_backend(DeviceType::CPU, mat_scale, __alloc_memory_warmup);
            break;
        case op_t::MAT_VEC_MUL:
            t->set_backend(DeviceType::CPU, mat_vec_mul, __alloc_memory_warmup);
            break;
        case op_t::RMSNORM:
            t->set_backend(DeviceType::CPU, rmsnorm, __alloc_memory_warmup);
            break;
        case op_t::ROPE:
            if (t->options<rope_options>().inplace) {
                t->set_backend(DeviceType::CPU, rope, __inplace_warmup);
            } else {
                t->set_backend(DeviceType::CPU, rope, __alloc_memory_warmup);
            }
            break;
        case op_t::MHA:
            t->set_backend(DeviceType::CPU, mha, __alloc_memory_warmup);
            break;
        case op_t::SILU:
            t->set_backend(DeviceType::CPU, silu, __alloc_memory_warmup);
            break;
        case op_t::SOFTMAX:
            t->set_backend(DeviceType::CPU, softmax, __alloc_memory_warmup);
            break;
        case op_t::TRANSPOSE:
            if (t->options<transpose_options>().copy) {
                t->set_backend(DeviceType::CPU, __transpose, __alloc_memory_warmup);
            } else {
                t->set_backend(DeviceType::CPU, __transpose, __inplace_warmup);
            }
            break;
        case op_t::VIEW:
            if (t->options<view_options>().copy) {
                t->set_backend(DeviceType::CPU, __view, __alloc_memory_warmup);
            } else {
                t->set_backend(DeviceType::CPU, __view, __inplace_warmup);
            }
            break;
        case op_t::CONTIGUOUS:
            t->set_backend(DeviceType::CPU, __contiguous, __alloc_memory_warmup);
            break;
        // quantization
        case op_t::MAT_MUL_W8A32:
            t->set_backend(DeviceType::CPU, mat_mul_w8a32, __alloc_memory_warmup);
            break;
        case op_t::MAT_VEC_MUL_W8A32:
            t->set_backend(DeviceType::CPU, mat_vec_mul_w8a32, __alloc_memory_warmup);
            break;
        default:
            throw std::runtime_error("Unknown op type");
    }
};
}; // namespace hllm

void kernel_cpu::set_kernel(Tensor& t) {
    switch (t->op()) {
        case op_t::PARAM:
        case op_t::CONSTANT:
            break;
    }
}