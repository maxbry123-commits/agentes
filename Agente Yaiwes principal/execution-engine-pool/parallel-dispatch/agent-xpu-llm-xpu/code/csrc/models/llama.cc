#include "llama.h"

#include "utils/logging.h"
#include "utils/utils.h"

#include <filesystem>

#ifdef _WIN32
#include <io.h>
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#endif

namespace hllm {
Llama::Llama(const char* model_path) {
    logging::info() << "Loading model from " << model_path;
    load_model(model_path);
    // print model info
    logging::info() << "Model info:";
    logging::info() << "  model_type: " << model_type_;
    logging::info() << "  dim: " << config_.dim;
    logging::info() << "  hidden_dim: " << config_.hidden_dim;
    logging::info() << "  n_layers: " << config_.n_layers;
    logging::info() << "  n_heads: " << config_.n_heads;
    logging::info() << "  n_kv_heads: " << config_.n_kv_heads;
    logging::info() << "  vocab size: " << config_.vocab_size;
    logging::info() << "  max_seq_len: " << config_.max_seq_len;
    logging::info() << "  w_dtype: " << w_dtype_;
    logging::info() << "  a_dtype: " << a_dtype_;
    logging::info() << "  group_size: " << config_.group_size;
}

Llama::~Llama() { delete[] layer_weights; }

Tensor Llama::embed_prompt(std::vector<int> const& prompt) const {
    Tensor prompt_embeddings =
        create_param(a_dtype_, {(size_t)prompt.size(), (size_t)config_.dim}, ALLOC_ZERO);
    for (int i = 0; i < (int)prompt.size(); i++) {
        memcpy((char*)prompt_embeddings->at(i, 0), (char*)token_embedding_table->at(prompt[i], 0),
               config_.dim * dtype_size(a_dtype_));
    }
    return prompt_embeddings;
}

void Llama::embed_prompt(std::vector<int> const& prompt, char* dst) const {
    for (int i = 0; i < (int)prompt.size(); i++) {
        memcpy(dst + i * config_.dim * dtype_size(a_dtype_),
               (char*)token_embedding_table->at(prompt[i], 0), config_.dim * dtype_size(a_dtype_));
    }
}

const char* Llama::get_vocab_path(ModelType model_type) {
    switch (model_type) {
        case ModelType::Llama2:
            if (std::filesystem::exists("bins/vocabulary/llama2.vocab")) {
                return "bins/vocabulary/llama2.vocab";
            } else if (std::filesystem::exists("/share/vocabulary/llama2.vocab")) {
                return "/share/vocabulary/llama2.vocab";
            } else {
                logging::error() << "Vocabulary file not found";
                return nullptr;
            }
        case ModelType::Llama3:
            if (std::filesystem::exists("bins/vocabulary/llama3.vocab")) {
                return "bins/vocabulary/llama3.vocab";
            } else if (std::filesystem::exists("/share/vocabulary/llama3.vocab")) {
                return "/share/vocabulary/llama3.vocab";
            } else {
                logging::error() << "Vocabulary file not found";
                return nullptr;
            }
        default:
            logging::error() << "Unsupported model type";
            return nullptr;
    }
}

bool Llama::is_end_of_generation(int token) const {
    if (model_type_ == ModelType::Llama2 && (token == 1 || token == 2)) {
        return true; // EOS or EOT
    }
    if (model_type_ == ModelType::Llama3 &&
        (token == 128001 || token == 128008 || token == 128009)) {
        return true; // 128001: EOS (text), 128008: EOM (message), 128009: EOT (turn)
    }
    return false;
}

void Llama::discard_weights() {
    // logging::debug() << "Llama model discarding weights";
    for (int i = 0; i < config_.n_layers; i++) {
        auto& layer_weight = layer_weights[i];
        layer_weight.attn_rms_weight.reset();
        layer_weight.attn_wq.reset();
        layer_weight.attn_wk.reset();
        layer_weight.attn_wv.reset();
        layer_weight.attn_wo.reset();
        layer_weight.ffn_rms_weight.reset();
        layer_weight.ffn_gate.reset();
        layer_weight.ffn_down.reset();
        layer_weight.ffn_up.reset();
    }
    final_rms_weight.reset();
    out_weight.reset();
}

void Llama::load_model(const char* model_path) {
    FILE* file = fopen(model_path, "rb");
    if (!file) {
        logging::error() << "Couldn't open file " << model_path;
    }

    // read in the magic number header
    uint32_t magic_number;
    if (fread(&magic_number, sizeof(uint32_t), 1, file) != 1) {
        logging::error() << "Error reading magic number from file " << model_path;
    }
    if (magic_number != 0x686c6c6d) {
        logging::error() << "Magic number mismatch in file " << model_path;
    }

    // read in the model type
    int32_t model_id;
    if (fread(&model_id, sizeof(int32_t), 1, file) != 1) {
        logging::error() << "Error reading model type from file " << model_path;
    }
    switch (model_id) {
        case 0:
            model_type_ = ModelType::Llama2;
            break;
        case 1:
            model_type_ = ModelType::Llama3;
            break;
        default:
            logging::error() << "Unsupported model type in file " << model_path;
    }

    // read in the version header (datatype)
    int32_t version;
    if (fread(&version, sizeof(int32_t), 1, file) != 1) {
        logging::error() << "Error reading version from file " << model_path;
    }

    if (version == 0) {
        w_dtype_ = Dtype::float32;
        a_dtype_ = Dtype::float32;
    } else if (version == 1) {
        w_dtype_ = Dtype::float16;
        a_dtype_ = Dtype::float16;
    } else if (version == 2) { // w8a32
        w_dtype_ = Dtype::int8;
        a_dtype_ = Dtype::float32;
    } else if (version == 3) { // w8a16
        w_dtype_ = Dtype::int8;
        a_dtype_ = Dtype::float16;
    } else if (version == 4) { // w4a32
        w_dtype_ = Dtype::int4;
        a_dtype_ = Dtype::float32;
    } else if (version == 5) { // w4a16
        w_dtype_ = Dtype::int4;
        a_dtype_ = Dtype::float16;
    } else {
        logging::error() << "Unsupported version in file " << model_path;
    }

    // read in the config header
    if (fread(&config_, sizeof(Config), 1, file) != 1) {
        logging::error() << "Error reading config from file " << model_path;
    }
    auto head_size_ = config_.dim / config_.n_heads;

    // Initialize group sizes
    if (config_.group_size == 0) {
        // group size is not set
    } else if (config_.group_size > 0) {
        group_sizes_["attn_wq"] = config_.group_size;
        group_sizes_["attn_wk"] = config_.group_size;
        group_sizes_["attn_wv"] = config_.group_size;
        group_sizes_["attn_wo"] = config_.group_size;
        group_sizes_["ffn_gate"] = config_.group_size;
        group_sizes_["ffn_down"] = config_.group_size;
        group_sizes_["ffn_up"] = config_.group_size;
        group_sizes_["out_weight"] = config_.group_size;

    } else if (config_.group_size == -1) {
        group_sizes_["attn_wq"] = config_.dim;
        group_sizes_["attn_wk"] = config_.dim;
        group_sizes_["attn_wv"] = config_.dim;
        group_sizes_["attn_wo"] = config_.n_heads * head_size_;
        group_sizes_["ffn_gate"] = config_.dim;
        group_sizes_["ffn_down"] = config_.hidden_dim;
        group_sizes_["ffn_up"] = config_.dim;
        group_sizes_["out_weight"] = config_.dim;

    } else if (config_.group_size == -2) {
        group_sizes_["attn_wq"] = config_.dim * config_.dim;
        group_sizes_["attn_wk"] =
            config_.dim * config_.dim / (config_.n_heads / config_.n_kv_heads);
        group_sizes_["attn_wv"] =
            config_.dim * config_.dim / (config_.n_heads / config_.n_kv_heads);
        group_sizes_["attn_wo"] = config_.dim * config_.dim;
        group_sizes_["ffn_gate"] = config_.hidden_dim * config_.dim;
        group_sizes_["ffn_down"] = config_.dim * config_.hidden_dim;
        group_sizes_["ffn_up"] = config_.hidden_dim * config_.dim;
        group_sizes_["out_weight"] = config_.dim * config_.vocab_size;
    } else {
        logging::error() << "Invalid group size in file " << model_path;
    }

    // figure out the file size for mmap
    fseek(file, 0, SEEK_END);            // move file pointer to end of file
    auto model_file_size_ = ftell(file); // get the file size, in bytes
    fclose(file);

    // memory map the Transformer weights into the model_data pointer
#ifdef _WIN32
    HANDLE model_fd_ = CreateFileA(model_path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING,
                                   FILE_ATTRIBUTE_NORMAL, NULL);
    if (model_fd_ == INVALID_HANDLE_VALUE) {
        logging::error() << "CreateFile failed!";
    }
    HANDLE file_mapping = CreateFileMappingA(model_fd_, NULL, PAGE_READONLY, 0, 0, NULL);
    if (file_mapping == NULL) {
        logging::error() << "CreateFileMapping failed!";
        CloseHandle(model_fd_);
    }
    char* model_data_ = (char*)MapViewOfFile(file_mapping, FILE_MAP_READ, 0, 0, 0);
    if (model_data_ == NULL) {
        logging::error() << "MapViewOfFile failed!";
        CloseHandle(file_mapping);
        CloseHandle(model_fd_);
    }
#else
    auto model_fd_ = open(model_path, O_RDONLY); // open in read only mode
    if (model_fd_ == -1) {
        logging::error() << "open failed!";
    }
    char* model_data_ = (char*)mmap(NULL, model_file_size_, PROT_READ, MAP_PRIVATE, model_fd_, 0);
    if (model_data_ == MAP_FAILED) {
        logging::error() << "mmap failed!";
    }
#endif
    auto last_time = get_time();
    size_t read_size = 0;

    if (w_dtype_ == Dtype::int8 && a_dtype_ == Dtype::float16) {
        quant_type_ = QuantType::w8a16;
        read_size = init_int8_weights(model_data_);
    } else if (w_dtype_ == Dtype::int8 && a_dtype_ == Dtype::float32) {
        quant_type_ = QuantType::w8a32;
        read_size = init_int8_weights(model_data_);
    } else {
        logging::error() << "Unsupported quantization type";
    }
    assert(("Model file size mismatch" && read_size == (size_t)model_file_size_));
// close the memory mapping
#ifdef _WIN32
    UnmapViewOfFile(model_data_);
    CloseHandle(file_mapping);
    CloseHandle(model_fd_);
#else
    munmap((void*)model_data_, model_file_size_);
    close(model_fd_);
#endif
    logging::info() << "Weights initialized in " << elapsed_time(last_time) << "s";
}

size_t Llama::init_int8_weights(const char* model_data_) {
    auto head_size_ = config_.dim / config_.n_heads;
    // skip the header
    char* weight_ptr = (char*)model_data_ + MODEL_HEADER_SIZE;

    // map the token embedding table
    token_embedding_table =
        create_constant(a_dtype_, {(size_t)config_.vocab_size, (size_t)config_.dim});
    token_embedding_table->copy_data(weight_ptr);
    weight_ptr += config_.vocab_size * config_.dim * dtype_size(a_dtype_);

    // map the weights for each layer
    layer_weights = new LlamaLayerWeights[config_.n_layers];

    assert(("dim must be divisible by n_heads" && config_.dim % config_.n_heads == 0));

    unsigned long long weight_size_per_layer = 0;

    // attn_rms_weight
    weight_size_per_layer += config_.dim * dtype_size(a_dtype_);

    // attn_wq data
    weight_size_per_layer += config_.dim * config_.dim * dtype_size(w_dtype_);
    // attn_wq scales
    weight_size_per_layer +=
        config_.n_heads * head_size_ * config_.dim / group_sizes_["attn_wq"] * sizeof(float);

    // attn_wk data
    weight_size_per_layer += config_.n_kv_heads * head_size_ * config_.dim * dtype_size(w_dtype_);
    // attn_wk scales
    weight_size_per_layer +=
        config_.n_kv_heads * head_size_ * config_.dim / group_sizes_["attn_wk"] * sizeof(float);

    // attn_wv data
    weight_size_per_layer += config_.n_kv_heads * head_size_ * config_.dim * dtype_size(w_dtype_);
    // attn_wv scales
    weight_size_per_layer +=
        config_.n_kv_heads * head_size_ * config_.dim / group_sizes_["attn_wv"] * sizeof(float);

    // attn_wo data
    weight_size_per_layer += config_.dim * config_.n_heads * head_size_ * dtype_size(w_dtype_);
    // attn_wo scales
    weight_size_per_layer +=
        config_.dim * config_.n_heads * head_size_ / group_sizes_["attn_wo"] * sizeof(float);

    // ffn_rms_weight
    weight_size_per_layer += config_.dim * dtype_size(a_dtype_);

    // ffn_gate data
    weight_size_per_layer += config_.hidden_dim * config_.dim * dtype_size(w_dtype_);
    // ffn_gate scales
    weight_size_per_layer +=
        config_.hidden_dim * config_.dim / group_sizes_["ffn_gate"] * sizeof(float);

    // ffn_down data
    weight_size_per_layer += config_.dim * config_.hidden_dim * dtype_size(w_dtype_);
    // ffn_down scales
    weight_size_per_layer +=
        config_.dim * config_.hidden_dim / group_sizes_["ffn_down"] * sizeof(float);

    // ffn_up data
    weight_size_per_layer += config_.hidden_dim * config_.dim * dtype_size(w_dtype_);
    // ffn_up scales
    weight_size_per_layer +=
        config_.hidden_dim * config_.dim / group_sizes_["ffn_up"] * sizeof(float);

    for (int l = 0; l < config_.n_layers; l++) {
        char* layer_weight_ptr = weight_ptr + l * weight_size_per_layer;

        layer_weights[l].attn_rms_weight = create_constant(a_dtype_, {(size_t)config_.dim});
        layer_weights[l].attn_rms_weight->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.dim * dtype_size(a_dtype_);

        layer_weights[l].attn_wq =
            create_constant(w_dtype_, {(size_t)config_.n_heads * head_size_, (size_t)config_.dim});
        layer_weights[l].attn_wq->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.n_heads * head_size_ * config_.dim * dtype_size(w_dtype_);
        layer_weights[l].attn_wq->set_group_size(group_sizes_["attn_wq"]);
        layer_weights[l].attn_wq->set_quant_type(quant_type_);
        layer_weights[l].attn_wq->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.n_heads * head_size_ * config_.dim / group_sizes_["attn_wq"] * sizeof(float);

        layer_weights[l].attn_wk = create_constant(
            w_dtype_, {(size_t)config_.n_kv_heads * head_size_, (size_t)config_.dim});
        layer_weights[l].attn_wk->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.n_kv_heads * head_size_ * config_.dim * dtype_size(w_dtype_);
        layer_weights[l].attn_wk->set_group_size(group_sizes_["attn_wk"]);
        layer_weights[l].attn_wk->set_quant_type(quant_type_);
        layer_weights[l].attn_wk->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.n_kv_heads * head_size_ * config_.dim / group_sizes_["attn_wk"] * sizeof(float);

        layer_weights[l].attn_wv = create_constant(
            w_dtype_, {(size_t)config_.n_kv_heads * head_size_, (size_t)config_.dim});
        layer_weights[l].attn_wv->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.n_kv_heads * head_size_ * config_.dim * dtype_size(w_dtype_);
        layer_weights[l].attn_wv->set_group_size(group_sizes_["attn_wv"]);
        layer_weights[l].attn_wv->set_quant_type(quant_type_);
        layer_weights[l].attn_wv->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.n_kv_heads * head_size_ * config_.dim / group_sizes_["attn_wv"] * sizeof(float);

        layer_weights[l].attn_wo =
            create_constant(w_dtype_, {(size_t)config_.dim, (size_t)config_.n_heads * head_size_});
        layer_weights[l].attn_wo->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.dim * config_.n_heads * head_size_ * dtype_size(w_dtype_);
        layer_weights[l].attn_wo->set_group_size(group_sizes_["attn_wo"]);
        layer_weights[l].attn_wo->set_quant_type(quant_type_);
        layer_weights[l].attn_wo->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.dim * config_.n_heads * head_size_ / group_sizes_["attn_wo"] * sizeof(float);

        layer_weights[l].ffn_rms_weight = create_constant(a_dtype_, {(size_t)config_.dim});
        layer_weights[l].ffn_rms_weight->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.dim * dtype_size(a_dtype_);

        layer_weights[l].ffn_gate =
            create_constant(w_dtype_, {(size_t)config_.hidden_dim, (size_t)config_.dim});
        layer_weights[l].ffn_gate->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.hidden_dim * config_.dim * dtype_size(w_dtype_);
        layer_weights[l].ffn_gate->set_group_size(group_sizes_["ffn_gate"]);
        layer_weights[l].ffn_gate->set_quant_type(quant_type_);
        layer_weights[l].ffn_gate->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.hidden_dim * config_.dim / group_sizes_["ffn_gate"] * sizeof(float);

        layer_weights[l].ffn_down =
            create_constant(w_dtype_, {(size_t)config_.dim, (size_t)config_.hidden_dim});
        layer_weights[l].ffn_down->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.dim * config_.hidden_dim * dtype_size(w_dtype_);
        layer_weights[l].ffn_down->set_group_size(group_sizes_["ffn_down"]);
        layer_weights[l].ffn_down->set_quant_type(quant_type_);
        layer_weights[l].ffn_down->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.dim * config_.hidden_dim / group_sizes_["ffn_down"] * sizeof(float);

        layer_weights[l].ffn_up =
            create_constant(w_dtype_, {(size_t)config_.hidden_dim, (size_t)config_.dim});
        layer_weights[l].ffn_up->copy_data(layer_weight_ptr);
        layer_weight_ptr += config_.hidden_dim * config_.dim * dtype_size(w_dtype_);
        layer_weights[l].ffn_up->set_group_size(group_sizes_["ffn_up"]);
        layer_weights[l].ffn_up->set_quant_type(quant_type_);
        layer_weights[l].ffn_up->copy_scales(layer_weight_ptr);
        layer_weight_ptr +=
            config_.hidden_dim * config_.dim / group_sizes_["ffn_up"] * sizeof(float);
    }

    weight_ptr += config_.n_layers * weight_size_per_layer;
    // map the final rmsnorm weight
    final_rms_weight = create_constant(a_dtype_, {(size_t)config_.dim});
    final_rms_weight->copy_data(weight_ptr);
    weight_ptr += config_.dim * dtype_size(a_dtype_);
    // map the output layer weight
    out_weight = create_constant(w_dtype_, {(size_t)config_.vocab_size, (size_t)config_.dim});
    out_weight->copy_data(weight_ptr);
    weight_ptr += config_.vocab_size * config_.dim * dtype_size(w_dtype_);
    out_weight->set_group_size(group_sizes_["out_weight"]);
    out_weight->set_quant_type(quant_type_);
    out_weight->copy_scales(weight_ptr);
    // std::cout << "outweight scales: " << out_weight->get_scales()[0] << " with size "
    //           << out_weight->get_scales().size() << std::endl;
    weight_ptr += config_.vocab_size * config_.dim / group_sizes_["out_weight"] * sizeof(float);
    // map the freqs_cis
    freqs_cis = create_constant(
        a_dtype_, {(size_t)config_.max_seq_len, (size_t)head_size_ / 2, 2}); // 2 for cos/sin
    freqs_cis->copy_data(weight_ptr);
    // std::cout << "freqs_cis_first_element: " << fp16_to_fp32(*(uint16_t*)freqs_cis->at(0, 0, 0))
    //           << std::endl;
    weight_ptr += config_.max_seq_len * head_size_ * dtype_size(a_dtype_);
    if (model_type_ == ModelType::Llama3) {
        // skip the second half of freqs_cis
        weight_ptr += config_.max_seq_len * head_size_ * dtype_size(a_dtype_);
    }
    return (char*)weight_ptr - (char*)model_data_;
}
} // namespace hllm