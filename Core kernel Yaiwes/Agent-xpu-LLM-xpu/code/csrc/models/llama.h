#pragma once

#include "basic/dtype.h"
#include "basic/tensor.h"
#include "models/models.h"

#include <unordered_map>

#define MODEL_HEADER_SIZE 256

namespace hllm {
class Llama {
  public:
    // Basic hyperparameters for the transformer model
    struct Config {
        int dim;        // transformer dimension
        int hidden_dim; // for ffn layers
        int n_layers;   // number of layers
        int n_heads;    // number of query heads
        int n_kv_heads; // number of key/value heads (can be < query heads because of
        // multiquery)
        int vocab_size;  // vocabulary size
        int max_seq_len; // max sequence length
        int group_size;  // group size for quantized model

        int kv_dim() { return n_kv_heads * (dim / n_heads); }
        int head_size() { return dim / n_heads; }
    };

    // Weight of a Llama layer, as a storage of weights
    struct LlamaLayerWeights {
        // Self-attention weights
        // Note that, dim == n_heads * head_size
        // input tensors are on the right-hand side of the weight matrices
        Tensor attn_rms_weight; // (, dim)
        Tensor attn_wq;         // (n_heads * head_size, dim)
        Tensor attn_wk;         // (n_kv_heads * head_size, dim)
        Tensor attn_wv;         // (n_kv_heads * head_size, dim)
        Tensor attn_wo;         // (dim, n_heads * head_size)
        // Feed-forward (FFN) weights
        Tensor ffn_rms_weight; // (, dim)
        Tensor ffn_gate;       // (hidden_dim, dim), w1
        Tensor ffn_down;       // (dim, hidden_dim), w2
        Tensor ffn_up;         // (hidden_dim, dim), w3
    };

    Llama(const char* model_path);
    ~Llama();

    Config get_config() const { return config_; }
    Dtype get_weight_dtype() const { return w_dtype_; }
    Dtype get_activation_dtype() const { return a_dtype_; }
    ModelType get_model_type() const { return model_type_; }
    QuantType get_quant_type() const { return quant_type_; }

    Tensor embed_prompt(std::vector<int> const& prompt) const;
    void embed_prompt(std::vector<int> const& prompt, char* dst) const;
    const char* get_vocab_path(ModelType model_type);

    Tensor get_token_embedding_table() const { return token_embedding_table; }
    Tensor get_final_rms_weight() const { return final_rms_weight; }
    Tensor get_out_weight() const { return out_weight; }
    Tensor get_freqs_cis() const { return freqs_cis; }

    LlamaLayerWeights const& get_layer_weights(int layer_id) const {
        return layer_weights[layer_id];
    }

    bool is_end_of_generation(int token) const;

    // Will not discard token embedding table and freqs_cis
    void discard_weights();

  protected:
    Config config_;
    Dtype w_dtype_ = Dtype::unknown;
    Dtype a_dtype_ = Dtype::unknown;
    ModelType model_type_;
    QuantType quant_type_;
    std::unordered_map<std::string, int> group_sizes_;

    // Model weight tensors
    LlamaLayerWeights* layer_weights;
    Tensor token_embedding_table;
    Tensor final_rms_weight;
    Tensor out_weight;
    Tensor freqs_cis;

    void load_model(const char* model_path);
    size_t init_int8_weights(const char* model_data_);
};
} // namespace hllm