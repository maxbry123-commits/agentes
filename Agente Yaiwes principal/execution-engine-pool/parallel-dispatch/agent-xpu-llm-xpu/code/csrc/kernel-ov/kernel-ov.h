#pragma once

#include <cstddef>
#include <memory>
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>

namespace hllm {
namespace ov_kernel {

enum class KernelType {
    pre_attn_w8,
    post_attn_w8,
    final_out_w8,
    llama3_layer_w8,
};

/**
 * @brief Creates an OpenVINO model for the Llama attention.
 *
 * Support prefill/decode modes, static or dynamic (seq_len = -1) models, GQA or MHA
 *
 * Model Inputs:
 *   - Q: [seq_len, dim] - Query tensor (w/o positional embedding)
 *   - K: [seq_len, kv_dim] - Key tensor (w/o positional embedding)
 *   - k_cache: [seq_len, kv_dim] - K cache (not used in prefill)
 *   - V_final: [seq_len, kv_dim] - Value tensor (V cache)
 *   - freq_cis_tensor: [seq_len, 1, head_dim/2, 2] - Rotary positional embedding tensor
 *   - is_decode: [] (boolean) - Whether the model is in decode (generation) mode
 *
 * Model Output:
 *   - weighted_V: [seq_len, dim] - Weighted V tensor
 *   - K_rope_reshape: [seq_len, kv_dim] - Roped K tensor (updated K cache)
 */

std::shared_ptr<ov::Model> get_attn_model(ov::element::Type dtype_ov, const int seq_len, size_t dim,
                                          size_t n_heads, size_t n_kv_heads);

/**
 * @brief Creates an OpenVINO model for the final output layer of Llama with int8 quantization.
 *
 * This function constructs a computational graph that applies:
 *   1. Final RMS normalization to the last hidden embedding.
 *   2. Output projection to vocabulary logits using quantized weights (int8 with scale).
 *
 * @param a_dtype_ov            OpenVINO element type for activations (e.g., f16, f32)
 * @param input_shape           Sequence length dimension (-1 for dynamic, positive for fixed)
 * @param dim                   Hidden dimension size
 * @param vocab_size            Vocabulary size (output dimension)
 * @param final_rms_weight_ptr  Pointer to RMS normalization weight vector (shape: [dim])
 * @param final_wo_weight_ptr   Pointer to quantized output projection weight matrix (int8, shape:
 * [vocab_size, dim])
 * @param final_wo_scale        Scale factor for output projection weights
 *
 * @return OpenVINO model with:
 *   - Input: last_embedding [input_shape, dim] (output of post_attn)
 *   - Output: logits [input_shape, vocab_size] (f32)
 */

std::shared_ptr<ov::Model>
get_final_out_w8_model(ov::element::Type a_dtype_ov, const int input_shape, const size_t dim,
                       const size_t vocab_size, const char* final_rms_weight_ptr,
                       const char* final_wo_weight_ptr, const float final_wo_scale);

/**
 * @brief Builds an OpenVINO model for a single Llama3 transformer layer with int8 quantized
 * weights.
 *
 * This function constructs the computation graph for a Llama3 transformer layer, including:
 *   - Pre-attention RMS normalization and QKV projection (int8 quantized)
 *   - Rotary positional embedding (freq_cis_tensor)
 *   - Multi-head attention with key/value cache update
 *   - Output projection (int8 quantized)
 *   - Feed-forward network (int8 quantized)
 *   - Residual connections and layer normalization
 *
 * @param a_dtype_ov         OpenVINO element type for activations (e.g., f16, f32)
 * @param seq_len            Sequence length dimension (-1 for dynamic, positive for fixed)
 * @param dim                Hidden dimension size
 * @param n_heads            Number of attention heads
 * @param n_kv_heads         Number of key/value heads
 * @param hidden_dim         Feed-forward hidden dimension size
 * @param attn_rms_weight_ptr Pointer to attention RMSNorm weights [dim]
 * @param attn_wq_weight_ptr  Pointer to Q projection weights [dim, dim] (int8)
 * @param attn_wk_weight_ptr  Pointer to K projection weights [kv_dim, dim] (int8)
 * @param attn_wv_weight_ptr  Pointer to V projection weights [kv_dim, dim] (int8)
 * @param attn_wo_weight_ptr  Pointer to output projection weights [dim, dim] (int8)
 * @param ffn_rms_weight_ptr  Pointer to FFN RMSNorm weights [dim]
 * @param ffn_gate_weight_ptr Pointer to FFN gate weights [hidden_dim, dim] (int8)
 * @param ffn_down_weight_ptr Pointer to FFN down-projection weights [dim, hidden_dim] (int8)
 * @param ffn_up_weight_ptr   Pointer to FFN up-projection weights [hidden_dim, dim] (int8)
 * @param attn_wq_scale       Scale for Q weights
 * @param attn_wk_scale       Scale for K weights
 * @param attn_wv_scale       Scale for V weights
 * @param attn_wo_scale       Scale for output projection weights
 * @param ffn_gate_scale      Scale for FFN gate weights
 * @param ffn_down_scale      Scale for FFN down-projection weights
 * @param ffn_up_scale        Scale for FFN up-projection weights
 *
 * @return std::shared_ptr<ov::Model>
 *   - Inputs:
 *       0. prompt_embedding: [seq_len, dim]         (input hidden states)
 *       1. freq_cis_tensor: [seq_len, 1, head_dim/2, 2] (rotary positional embedding)
 *       2. k_cache: [*, kv_dim]                    (key cache, shape depends on mode)
 *       3. v_cache: [*, kv_dim]                    (value cache, shape depends on mode)
 *       4. is_decode: []                           (boolean, indicates decode/generation mode)
 *   - Results:
 *       0. output embedding: [seq_len, dim] or [1, dim] (layer output, or [1, vocab_size] if final)
 *       1. updated k_cache: [*, kv_dim]
 *       2. updated v_cache: [*, kv_dim]
 */
std::shared_ptr<ov::Model> get_llama3_layer_w8_model(
    ov::element::Type a_dtype_ov, const int seq_len, const size_t dim, const size_t n_heads,
    const size_t n_kv_heads, const size_t hidden_dim, const char* attn_rms_weight_ptr,
    const char* attn_wq_weight_ptr, const char* attn_wk_weight_ptr, const char* attn_wv_weight_ptr,
    const char* attn_wo_weight_ptr, const char* ffn_rms_weight_ptr, const char* ffn_gate_weight_ptr,
    const char* ffn_down_weight_ptr, const char* ffn_up_weight_ptr, const float attn_wq_scale,
    const float attn_wk_scale, const float attn_wv_scale, const float attn_wo_scale,
    const float ffn_gate_scale, const float ffn_down_scale, const float ffn_up_scale);

/**
 * @brief Creates an OpenVINO model for Llama post-attention computation with int8 quantization
 * This process includes 1) attn output and 2) ffn
 *
 * @param a_dtype_ov         The OpenVINO element type for activations (e.g., ov::element::f16 or
 * ov::element::f32).
 * @param input_shape        The input sequence length. If negative, a dynamic shape is used.
 * @param dim                The hidden dimension size.
 * @param hidden_dim         The intermediate (FFN) hidden dimension size.
 * @param attn_wo_weight_ptr Pointer to the int8 attention output projection weights (shape: [dim,
 * dim]).
 * @param ffn_rms_weight_ptr Pointer to the RMSNorm weights (shape: [dim]).
 * @param ffn_gate_weight_ptr Pointer to the int8 FFN gate weights (shape: [hidden_dim, dim]).
 * @param ffn_down_weight_ptr Pointer to the int8 FFN down-projection weights (shape: [dim,
 * hidden_dim]).
 * @param ffn_up_weight_ptr   Pointer to the int8 FFN up-projection weights (shape: [hidden_dim,
 * dim]).
 * @param attn_wo_scale      Scale factor for dequantizing the attention output projection weights.
 * @param ffn_gate_scale     Scale factor for dequantizing the FFN gate weights.
 * @param ffn_down_scale     Scale factor for dequantizing the FFN down-projection weights.
 * @param ffn_up_scale       Scale factor for dequantizing the FFN up-projection weights.
 *
 * @return std::shared_ptr<ov::Model>
 *    - Input 1: prompt_embedding [input_shape, dim]
 *    - Input 2: weighted_V_reshape [input_shape, dim]
 *    - Output: ffn_out_prompt_embedding [input_shape, dim]
 */
std::shared_ptr<ov::Model> get_post_attn_w8_model(
    ov::element::Type a_dtype_ov, const int input_shape, const size_t dim, const size_t hidden_dim,
    const char* attn_wo_weight_ptr, const char* ffn_rms_weight_ptr, const char* ffn_gate_weight_ptr,
    const char* ffn_down_weight_ptr, const char* ffn_up_weight_ptr, const float attn_wo_scale,
    const float ffn_gate_scale, const float ffn_down_scale, const float ffn_up_scale);

/**
 * @brief Creates an OpenVINO model for Llama pre-attention computation with int8 quantization
 *
 * This function constructs a computational graph that performs:
 * 1. RMS normalization on the input embeddings
 * 2. QKV projection using quantized weights (int8 with scales)
 *
 * @param a_dtype_ov OpenVINO element type for activations (e.g., f16, f32)
 * @param input_shape Sequence length dimension (-1 for dynamic, positive for fixed)
 * @param dim Hidden dimension size
 * @param n_heads Number of attention heads
 * @param n_kv_heads Number of key/value heads (for grouped-query attention)
 * @param attn_wq_weight_ptr Pointer to quantized query weight matrix (int8)
 * @param attn_wk_weight_ptr Pointer to quantized key weight matrix (int8)
 * @param attn_wv_weight_ptr Pointer to quantized value weight matrix (int8)
 * @param attn_rms_weight_ptr Pointer to RMS normalization weight vector
 * @param attn_wq_scale Scale factor for query weights
 * @param attn_wk_scale Scale factor for key weights
 * @param attn_wv_scale Scale factor for value weights
 *
 * @return OpenVINO model with:
 *   - Input: prompt_embedding [seq_len, dim]
 *   - Output 1: Q projection [seq_len, dim]
 *   - Output 2: K projection [seq_len, kv_dim]
 *   - Output 3: V projection [seq_len, kv_dim]
 */
std::shared_ptr<ov::Model>
get_pre_attn_w8_model(ov::element::Type a_dtype_ov, const int input_shape, const size_t dim,
                      const size_t n_heads, const size_t n_kv_heads, const char* attn_wq_weight_ptr,
                      const char* attn_wk_weight_ptr, const char* attn_wv_weight_ptr,
                      const char* attn_rms_weight_ptr, const float attn_wq_scale,
                      const float attn_wk_scale, const float attn_wv_scale);

// Concat QKV weights with output QKV projection [seq_len, dim + 2*kv_dim]
std::shared_ptr<ov::Model> get_pre_attn_w8_concat_model(
    ov::element::Type a_dtype_ov, const int input_shape, const size_t dim, const size_t n_heads,
    const size_t n_kv_heads, const char* attn_wq_weight_ptr, const char* attn_wk_weight_ptr,
    const char* attn_wv_weight_ptr, const char* attn_rms_weight_ptr, const float attn_wq_scale,
    const float attn_wk_scale, const float attn_wv_scale);

} // namespace ov_kernel
} // namespace hllm
