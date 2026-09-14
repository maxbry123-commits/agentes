#pragma once
enum class op_t {
    PARAM,
    CONSTANT,
    MAT_ADD,
    MAT_MUL,
    MAT_SCALE,
    MAT_VEC_MUL,
    RMSNORM,
    ROPE,
    MHA,
    SILU,
    SOFTMAX,
    TRANSPOSE,
    VIEW,
    CONTIGUOUS,
    // Experimental ops
    LLAMA2_LAYER,
    LLAMA3_LAYER,
    // Quantization ops
    MAT_MUL_W8A32,
    MAT_VEC_MUL_W8A32,
    // OV ops
    OV_ATTN,
    OV_PRE_ATTN,
    OV_POST_ATTN,
    OV_FINAL_OUT,
    OV_LLAMA_LAYER,
    // Null
    NONE,
};