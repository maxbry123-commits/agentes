#include "context.h"

#include "backend.h"
#include "basic/dtype.h"
#include "basic/tensor.h"
#include "end2end/infer-job.h"
#include "kernel-ov/kernel-ov.h"
#include "utils/logging.h"
#include "utils/utils.h"

#include <atomic>
#include <csignal>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <openvino/runtime/compiled_model.hpp>
#include <openvino/runtime/infer_request.hpp>
#include <sstream>

static std::atomic<bool> interrupted(false);

static void signal_handler(int signal) {
    if (signal == SIGINT) {
        interrupted.store(true);
    }
}

namespace hllm {
ContextOV::ContextOV(const char* model_path, bool enable_layer_decode, bool enable_ov_cache)
    : model_(model_path),
      sampler_(model_.get_config()
                   .vocab_size), // Default vocab size, will be updated after warmup if needed
      tokenizer_(model_.get_vocab_path(model_.get_model_type())), // Default vocab path
      prefill_gpu_ratio_(0), enable_layer_gpu_infer_(enable_layer_decode) {

    assert(model_.get_quant_type() == QuantType::w8a16 && model_.get_config().group_size == -2);

    a_dtype_ov_ = get_ov_dtype(model_.get_activation_dtype());
    // enable ov model caching
    if (enable_ov_cache) {
        // Cross-platform cache directory setup
        std::string cache_dir;
#ifdef _WIN32
        // Windows: Use %APPDATA% or %USERPROFILE%
        const char* appdata = std::getenv("APPDATA");
        if (appdata) {
            cache_dir = std::string(appdata) + "\\llm.xpu\\ov_cache";
        } else {
            const char* userprofile = std::getenv("USERPROFILE");
            if (userprofile) {
                cache_dir = std::string(userprofile) + "\\.cache\\llm.xpu\\ov_cache";
            } else {
                cache_dir = ".\\cache\\llm.xpu\\ov_cache"; // Fallback to current directory
            }
        }
#else
        // Unix/Linux: Use $HOME
        const char* home = std::getenv("HOME");
        if (home) {
            cache_dir = std::string(home) + "/.cache/llm.xpu/ov_cache";
        } else {
            cache_dir = "./cache/llm.xpu/ov_cache"; // Fallback to current directory
        }
#endif
        cache_dir_ = cache_dir;
        logging::info() << "OV cache dir: " << cache_dir_;
        std::filesystem::create_directories(cache_dir_);
        ov_core_.set_property(ov::cache_dir(cache_dir_));
    }
    auto begin = get_time();
    warmup_q8_kernels();
    logging::info() << "Warmup W8A16 OV kernels time: " << elapsed_time(begin) << "s";
    model_.discard_weights();
    alloc_activation_buffer();
}

ContextOV::~ContextOV() {
    // Stop async processing if it's running
    if (is_async_running()) {
        stop_async_processing();
    }
}

void ContextOV::alloc_activation_buffer() {
    Dtype a_dtype = model_.get_activation_dtype();
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();
    size_t vocab_size = model_.get_config().vocab_size;

    for (int i = 0; i < 2; i++) {
        prefill_buf[i].prompt_embedding = create_param(a_dtype, {CTX_LEN_, dim}, ALLOC_ZERO);
        prefill_buf[i].Q_proj = create_param(a_dtype, {CTX_LEN_, dim}, ALLOC_ZERO);
        prefill_buf[i].K_proj = create_param(a_dtype, {CTX_LEN_, kv_dim}, ALLOC_ZERO);
        prefill_buf[i].weighted_V = create_param(a_dtype, {CTX_LEN_, dim}, ALLOC_ZERO);
        prefill_buf[i].final_out = create_param(Dtype::float32, {1, vocab_size}, ALLOC_ZERO);
    }

    decode_buf.prompt_embedding = create_param(a_dtype, {MAX_DECODE_BATCH_SIZE_, dim}, ALLOC_ZERO);
    decode_buf.Q_proj = create_param(a_dtype, {MAX_DECODE_BATCH_SIZE_, dim}, ALLOC_ZERO);
    decode_buf.K_proj = create_param(a_dtype, {MAX_DECODE_BATCH_SIZE_, kv_dim}, ALLOC_ZERO);
    decode_buf.v_cache_decode = create_param(a_dtype, {MAX_DECODE_BATCH_SIZE_, kv_dim}, ALLOC_ZERO);
    decode_buf.weighted_V = create_param(a_dtype, {MAX_DECODE_BATCH_SIZE_, dim}, ALLOC_ZERO);
    decode_buf.final_out =
        create_param(Dtype::float32, {MAX_DECODE_BATCH_SIZE_, vocab_size}, ALLOC_ZERO);
}

void ContextOV::warmup_q8_kernels() {
    int layers = model_.get_config().n_layers;
    int dim = model_.get_config().dim;
    int hidden_dim = model_.get_config().hidden_dim;
    int vocab_size = model_.get_config().vocab_size;
    int n_heads = model_.get_config().n_heads;
    int n_kv_heads = model_.get_config().n_kv_heads;

    for (int l = 0; l < layers; l++) {
        // pre attn
        auto pre_attn_dyn_model = ov_kernel::get_pre_attn_w8_model(
            a_dtype_ov_, -1, dim, model_.get_config().n_heads, model_.get_config().n_kv_heads,
            model_.get_layer_weights(l).attn_wq->get_data(),
            model_.get_layer_weights(l).attn_wk->get_data(),
            model_.get_layer_weights(l).attn_wv->get_data(),
            model_.get_layer_weights(l).attn_rms_weight->get_data(),
            model_.get_layer_weights(l).attn_wq->get_scales()[0],
            model_.get_layer_weights(l).attn_wk->get_scales()[0],
            model_.get_layer_weights(l).attn_wv->get_scales()[0]);
        auto pre_attn_chunked_model = ov_kernel::get_pre_attn_w8_model(
            a_dtype_ov_, CHUNK_SIZE_, dim, model_.get_config().n_heads,
            model_.get_config().n_kv_heads, model_.get_layer_weights(l).attn_wq->get_data(),
            model_.get_layer_weights(l).attn_wk->get_data(),
            model_.get_layer_weights(l).attn_wv->get_data(),
            model_.get_layer_weights(l).attn_rms_weight->get_data(),
            model_.get_layer_weights(l).attn_wq->get_scales()[0],
            model_.get_layer_weights(l).attn_wk->get_scales()[0],
            model_.get_layer_weights(l).attn_wv->get_scales()[0]);
        auto pre_attn_dyn_gpu_model = ov_core_.compile_model(
            pre_attn_dyn_model, "GPU",
            ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
        auto pre_attn_chunked_npu_model = ov_core_.compile_model(
            pre_attn_chunked_model, "NPU",
            ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
        pre_attn_gpu_dyn_models_.push_back(std::move(pre_attn_dyn_gpu_model));
        pre_attn_npu_chunked_models_.push_back(std::move(pre_attn_chunked_npu_model));

        // attn
        auto attn_model = ov_kernel::get_attn_model(a_dtype_ov_, -1, dim, n_heads, n_kv_heads);
        attn_gpu_model_ = ov_core_.compile_model(
            attn_model, "GPU", ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
        attn_cpu_model_ = ov_core_.compile_model(
            attn_model, "CPU", ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));

        // post attn
        auto post_attn_dyn_model = ov_kernel::get_post_attn_w8_model(
            a_dtype_ov_, -1, dim, hidden_dim, model_.get_layer_weights(l).attn_wo->get_data(),
            model_.get_layer_weights(l).ffn_rms_weight->get_data(),
            model_.get_layer_weights(l).ffn_gate->get_data(),
            model_.get_layer_weights(l).ffn_down->get_data(),
            model_.get_layer_weights(l).ffn_up->get_data(),
            model_.get_layer_weights(l).attn_wo->get_scales()[0],
            model_.get_layer_weights(l).ffn_gate->get_scales()[0],
            model_.get_layer_weights(l).ffn_down->get_scales()[0],
            model_.get_layer_weights(l).ffn_up->get_scales()[0]);
        auto post_attn_chunked_model = ov_kernel::get_post_attn_w8_model(
            a_dtype_ov_, CHUNK_SIZE_, dim, hidden_dim,
            model_.get_layer_weights(l).attn_wo->get_data(),
            model_.get_layer_weights(l).ffn_rms_weight->get_data(),
            model_.get_layer_weights(l).ffn_gate->get_data(),
            model_.get_layer_weights(l).ffn_down->get_data(),
            model_.get_layer_weights(l).ffn_up->get_data(),
            model_.get_layer_weights(l).attn_wo->get_scales()[0],
            model_.get_layer_weights(l).ffn_gate->get_scales()[0],
            model_.get_layer_weights(l).ffn_down->get_scales()[0],
            model_.get_layer_weights(l).ffn_up->get_scales()[0]);
        auto post_attn_dyn_gpu_model = ov_core_.compile_model(
            post_attn_dyn_model, "GPU",
            ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
        auto post_attn_chunked_npu_model = ov_core_.compile_model(
            post_attn_chunked_model, "NPU",
            ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
        post_attn_gpu_dyn_models_.push_back(std::move(post_attn_dyn_gpu_model));
        post_attn_npu_chunked_models_.push_back(std::move(post_attn_chunked_npu_model));

        // layer gpu models
        if (enable_layer_gpu_infer_) {
            auto layer_llama_model = ov_kernel::get_llama3_layer_w8_model(
                a_dtype_ov_, -1, dim, n_heads, n_kv_heads, hidden_dim,
                model_.get_layer_weights(l).attn_rms_weight->get_data(),
                model_.get_layer_weights(l).attn_wq->get_data(),
                model_.get_layer_weights(l).attn_wk->get_data(),
                model_.get_layer_weights(l).attn_wv->get_data(),
                model_.get_layer_weights(l).attn_wo->get_data(),
                model_.get_layer_weights(l).ffn_rms_weight->get_data(),
                model_.get_layer_weights(l).ffn_gate->get_data(),
                model_.get_layer_weights(l).ffn_down->get_data(),
                model_.get_layer_weights(l).ffn_up->get_data(),
                model_.get_layer_weights(l).attn_wq->get_scales()[0],
                model_.get_layer_weights(l).attn_wk->get_scales()[0],
                model_.get_layer_weights(l).attn_wv->get_scales()[0],
                model_.get_layer_weights(l).attn_wo->get_scales()[0],
                model_.get_layer_weights(l).ffn_gate->get_scales()[0],
                model_.get_layer_weights(l).ffn_down->get_scales()[0],
                model_.get_layer_weights(l).ffn_up->get_scales()[0]);
            auto layer_gpu_model_compiled = ov_core_.compile_model(
                layer_llama_model, "GPU",
                ov::hint::performance_mode(ov::hint::PerformanceMode::THROUGHPUT));
            layer_gpu_models_.push_back(std::move(layer_gpu_model_compiled));
        }
    }
    logging::info() << "GPU kernel's best # of reqs: "
                    << pre_attn_gpu_dyn_models_[0].get_property(
                           ov::optimal_number_of_infer_requests);
    logging::info() << "NPU kernel's best # of reqs: "
                    << pre_attn_npu_chunked_models_[0].get_property(
                           ov::optimal_number_of_infer_requests);

    // final out
    auto final_out_model = ov_kernel::get_final_out_w8_model(
        a_dtype_ov_, -1, dim, vocab_size, model_.get_final_rms_weight()->get_data(),
        model_.get_out_weight()->get_data(), model_.get_out_weight()->get_scales()[0]);
    final_out_gpu_model_ = ov_core_.compile_model(final_out_model, "GPU");
}

void ContextOV::prefill_job_swapin(InferJob job, int buf_idx) {
    model_.embed_prompt(job->prompt_tokens, prefill_buf[buf_idx].prompt_embedding->at(0));
}

void ContextOV::prefill_job_swapout(InferJob job, int buf_idx) {
    // wrap up the whole prefill
    job->stage = InferStage::decode;
    job->tok_pos = job->prompt_tokens.size();
    job->current_layer = 0;
    // sample the next token
    int next_token = sampler_.sample(prefill_buf[buf_idx].final_out->at(0), job->temperature,
                                     job->top_p, job->seed);
    job->generated_tokens.push_back(next_token);
}

void ContextOV::decode_job_batch_swapin(std::vector<InferJob>& jobs) {
    for (size_t i = 0; i < jobs.size(); i++) {
        int new_token = jobs[i]->generated_tokens.back();
        model_.embed_prompt({new_token}, decode_buf.prompt_embedding->at(i));
    }
}

void ContextOV::proceed_pre_attn_prefill(InferJob job, std::string device, size_t start_idx,
                                         size_t len, int buf_idx) {
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();
    if (device == "NPU") {
        assert(len == CHUNK_SIZE_ && "Only NPU chunked prefill is supported");
        auto ir = pre_attn_npu_chunked_models_[job->current_layer].create_infer_request();
        ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                          prefill_buf[buf_idx].prompt_embedding->at(start_idx)));
        ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                           prefill_buf[buf_idx].Q_proj->at(start_idx)));
        ir.set_output_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{len, kv_dim},
                                           prefill_buf[buf_idx].K_proj->at(start_idx)));
        ir.set_output_tensor(
            2, ov::Tensor(a_dtype_ov_, ov::Shape{len, kv_dim}, job->v_cache->at(start_idx)));
        ir.infer();
    } else if (device == "GPU") {
        auto ir = pre_attn_gpu_dyn_models_[job->current_layer].create_infer_request();
        ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                          prefill_buf[buf_idx].prompt_embedding->at(start_idx)));
        ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                           prefill_buf[buf_idx].Q_proj->at(start_idx)));
        ir.set_output_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{len, kv_dim},
                                           prefill_buf[buf_idx].K_proj->at(start_idx)));
        ir.set_output_tensor(
            2, ov::Tensor(a_dtype_ov_, ov::Shape{len, kv_dim}, job->v_cache->at(start_idx)));
        ir.infer();
    }
    job->last_finished_op = op_t::OV_PRE_ATTN;
}

void ContextOV::proceed_attn_prefill(InferJob job, std::string device, int buf_idx) {
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();
    size_t head_size = model_.get_config().head_size();
    size_t prompt_len = job->prompt_tokens.size();

    assert(device == "GPU" && "Only GPU attn prefill is supported");
    auto ir = attn_gpu_model_.create_infer_request();
    ir.set_input_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{prompt_len, dim}, prefill_buf[buf_idx].Q_proj->at(0)));
    ir.set_input_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{prompt_len, kv_dim},
                                      prefill_buf[buf_idx].K_proj->at(0)));
    // ir.set_input_tensor(2, nullptr); // k_cache is not used as input in prefill
    ir.set_input_tensor(
        3, ov::Tensor(a_dtype_ov_, ov::Shape{prompt_len, kv_dim}, job->v_cache->at(0)));
    ir.set_input_tensor(4, ov::Tensor(a_dtype_ov_, ov::Shape{prompt_len, 1, head_size / 2, 2},
                                      model_.get_freqs_cis()->at(0)));
    bool is_decode = false;
    ir.set_input_tensor(5, ov::Tensor(ov::element::boolean, ov::Shape{}, &is_decode));

    ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{prompt_len, dim},
                                       prefill_buf[buf_idx].weighted_V->at(0)));
    ir.set_output_tensor(
        1, ov::Tensor(a_dtype_ov_, ov::Shape{prompt_len, kv_dim}, job->k_cache->at(0)));
    ir.infer();

    job->last_finished_op = op_t::OV_ATTN;
}

void ContextOV::proceed_post_attn_prefill(InferJob job, std::string device, size_t start_idx,
                                          size_t len, int buf_idx) {
    size_t dim = model_.get_config().dim;
    if (device == "NPU") {
        assert(len == CHUNK_SIZE_ && "Only NPU chunked prefill is supported");
        auto ir = post_attn_npu_chunked_models_[job->current_layer].create_infer_request();
        ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                          prefill_buf[buf_idx].prompt_embedding->at(start_idx)));
        ir.set_input_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                          prefill_buf[buf_idx].weighted_V->at(start_idx)));
        ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                           prefill_buf[buf_idx].prompt_embedding->at(start_idx)));
        ir.infer();
    } else if (device == "GPU") {
        auto ir = post_attn_gpu_dyn_models_[job->current_layer].create_infer_request();
        ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                          prefill_buf[buf_idx].prompt_embedding->at(start_idx)));
        ir.set_input_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                          prefill_buf[buf_idx].weighted_V->at(start_idx)));
        ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{len, dim},
                                           prefill_buf[buf_idx].prompt_embedding->at(start_idx)));
        ir.infer();
    }

    job->last_finished_op = op_t::OV_POST_ATTN;
    // wrap up this layer's prefill
    if (job->current_layer < model_.get_config().n_layers - 1) {
        job->current_layer++;
    }
}

void ContextOV::proceed_final_out_prefill(InferJob job, std::string device, int buf_idx) {
    size_t dim = model_.get_config().dim;
    size_t vocab_size = model_.get_config().vocab_size;
    assert(device == "GPU" && "Only GPU final out prefill is supported");
    auto ir = final_out_gpu_model_.create_infer_request();
    ir.set_input_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{1, dim},
                      prefill_buf[buf_idx].prompt_embedding->at(job->prompt_tokens.size() - 1)));
    ir.set_output_tensor(0, ov::Tensor(logits_dtype_ov_, ov::Shape{1, vocab_size},
                                       prefill_buf[buf_idx].final_out->at(0)));
    ir.infer();

    job->last_finished_op = op_t::OV_FINAL_OUT;
}

void ContextOV::proceed_prefill_hetero_async(InferJob job, float prefill_gpu_ratio) {
    size_t prompt_len = job->prompt_tokens.size();
    size_t n_chunks = prompt_len / CHUNK_SIZE_;
    size_t remainder_prompt_len = prompt_len % CHUNK_SIZE_;
    size_t n_npu_chunks = n_chunks - n_chunks * prefill_gpu_ratio;
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();

    int buf_idx = job->priority == JobPriority::reactive ? 1 : 0;

    if (prefill_gpu_ratio > 0.99) {
        if (is_gpu_chunked_prefill_) {
            n_npu_chunks = 0;
        } else {
            for (int l = 0; l < model_.get_config().n_layers; l++) {
                proceed_pre_attn_prefill(job, "GPU", 0, prompt_len, buf_idx);
                continue_or_preempt(job);
                proceed_attn_prefill(job, "GPU", buf_idx);
                continue_or_preempt(job);
                proceed_post_attn_prefill(job, "GPU", 0, prompt_len, buf_idx);
                continue_or_preempt(job);
            }
            proceed_final_out_prefill(job, "GPU", buf_idx);
            return;
        }
    }

    for (int l = 0; l < model_.get_config().n_layers; l++) {
        std::vector<ov::InferRequest> npu_infer_requests;
        std::vector<ov::InferRequest> gpu_infer_requests;

        for (size_t i = 0; i < n_npu_chunks; i++) {
            auto ir = pre_attn_npu_chunked_models_[l].create_infer_request();
            auto chunk_start_idx = i * CHUNK_SIZE_;
            ir.set_input_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].prompt_embedding->at(chunk_start_idx)));
            ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                               prefill_buf[buf_idx].Q_proj->at(chunk_start_idx)));
            ir.set_output_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, kv_dim},
                                               prefill_buf[buf_idx].K_proj->at(chunk_start_idx)));
            ir.set_output_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, kv_dim},
                                               job->v_cache->at(chunk_start_idx)));
            npu_infer_requests.push_back(std::move(ir));
        }
        for (size_t i = n_npu_chunks; i < n_chunks; i++) {
            auto ir = pre_attn_gpu_dyn_models_[l].create_infer_request();
            auto chunk_start_idx = i * CHUNK_SIZE_;
            ir.set_input_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].prompt_embedding->at(chunk_start_idx)));
            ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                               prefill_buf[buf_idx].Q_proj->at(chunk_start_idx)));
            ir.set_output_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, kv_dim},
                                               prefill_buf[buf_idx].K_proj->at(chunk_start_idx)));
            ir.set_output_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, kv_dim},
                                               job->v_cache->at(chunk_start_idx)));
            gpu_infer_requests.push_back(std::move(ir));
        }
        auto remainder_chunk_start_idx = n_chunks * CHUNK_SIZE_;
        if (prefill_gpu_ratio > 0.01 || remainder_chunk_start_idx + CHUNK_SIZE_ >= CTX_LEN_) {
            auto ir = pre_attn_gpu_dyn_models_[l].create_infer_request();
            ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, dim},
                                              prefill_buf[buf_idx].prompt_embedding->at(
                                                  remainder_chunk_start_idx)));
            ir.set_output_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, dim},
                              prefill_buf[buf_idx].Q_proj->at(remainder_chunk_start_idx)));
            ir.set_output_tensor(
                1, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, kv_dim},
                              prefill_buf[buf_idx].K_proj->at(remainder_chunk_start_idx)));
            ir.set_output_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, kv_dim},
                                               job->v_cache->at(remainder_chunk_start_idx)));
            gpu_infer_requests.push_back(std::move(ir));
        } else {
            auto ir = pre_attn_npu_chunked_models_[l].create_infer_request();
            ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                              prefill_buf[buf_idx].prompt_embedding->at(
                                                  remainder_chunk_start_idx)));
            ir.set_output_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].Q_proj->at(remainder_chunk_start_idx)));
            ir.set_output_tensor(
                1, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, kv_dim},
                              prefill_buf[buf_idx].K_proj->at(remainder_chunk_start_idx)));
            ir.set_output_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, kv_dim},
                                               job->v_cache->at(remainder_chunk_start_idx)));
            npu_infer_requests.push_back(std::move(ir));
        }

        for (auto& ir : npu_infer_requests) {
            ir.start_async();
        }
        for (auto& ir : gpu_infer_requests) {
            ir.start_async();
        }

        for (auto& ir : npu_infer_requests) {
            ir.wait();
        }
        for (auto& ir : gpu_infer_requests) {
            ir.wait();
        }
        job->last_finished_op = op_t::OV_PRE_ATTN;
        npu_infer_requests.clear();
        gpu_infer_requests.clear();
        continue_or_preempt(job);

        // proceed attn prefill
        proceed_attn_prefill(job, "GPU", buf_idx);
        continue_or_preempt(job);

        // chunked post attn prefill
        for (size_t i = 0; i < n_npu_chunks; i++) {
            auto ir = post_attn_npu_chunked_models_[l].create_infer_request();
            auto chunk_start_idx = i * CHUNK_SIZE_;
            ir.set_input_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].prompt_embedding->at(chunk_start_idx)));
            ir.set_input_tensor(1,
                                ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                           prefill_buf[buf_idx].weighted_V->at(chunk_start_idx)));
            ir.set_output_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].prompt_embedding->at(chunk_start_idx)));
            npu_infer_requests.push_back(std::move(ir));
        }
        for (size_t i = n_npu_chunks; i < n_chunks; i++) {
            auto ir = post_attn_gpu_dyn_models_[l].create_infer_request();
            auto chunk_start_idx = i * CHUNK_SIZE_;
            ir.set_input_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].prompt_embedding->at(chunk_start_idx)));
            ir.set_input_tensor(1,
                                ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                           prefill_buf[buf_idx].weighted_V->at(chunk_start_idx)));
            ir.set_output_tensor(
                0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].prompt_embedding->at(chunk_start_idx)));
            gpu_infer_requests.push_back(std::move(ir));
        }
        remainder_chunk_start_idx = n_chunks * CHUNK_SIZE_;
        if (prefill_gpu_ratio > 0.01 || remainder_chunk_start_idx + CHUNK_SIZE_ >= CTX_LEN_) {
            auto ir = post_attn_gpu_dyn_models_[l].create_infer_request();
            ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, dim},
                                              prefill_buf[buf_idx].prompt_embedding->at(
                                                  remainder_chunk_start_idx)));
            ir.set_input_tensor(
                1, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, dim},
                              prefill_buf[buf_idx].weighted_V->at(remainder_chunk_start_idx)));
            ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{remainder_prompt_len, dim},
                                               prefill_buf[buf_idx].prompt_embedding->at(
                                                   remainder_chunk_start_idx)));
            gpu_infer_requests.push_back(std::move(ir));
        } else {
            auto ir = post_attn_npu_chunked_models_[l].create_infer_request();
            ir.set_input_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                              prefill_buf[buf_idx].prompt_embedding->at(
                                                  remainder_chunk_start_idx)));
            ir.set_input_tensor(
                1, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                              prefill_buf[buf_idx].weighted_V->at(remainder_chunk_start_idx)));
            ir.set_output_tensor(0, ov::Tensor(a_dtype_ov_, ov::Shape{CHUNK_SIZE_, dim},
                                               prefill_buf[buf_idx].prompt_embedding->at(
                                                   remainder_chunk_start_idx)));
            npu_infer_requests.push_back(std::move(ir));
        }

        for (auto& ir : npu_infer_requests) {
            ir.start_async();
        }
        for (auto& ir : gpu_infer_requests) {
            ir.start_async();
        }

        for (auto& ir : npu_infer_requests) {
            ir.wait();
        }
        for (auto& ir : gpu_infer_requests) {
            ir.wait();
        }
        job->last_finished_op = op_t::OV_POST_ATTN;
        if (l < model_.get_config().n_layers - 1) {
            job->current_layer++;
        }
        continue_or_preempt(job);
    }

    proceed_final_out_prefill(job, "GPU", buf_idx);
}

void ContextOV::proceed_pre_attn_decode(std::vector<InferJob>& jobs, std::string device) {
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();
    size_t batch_size = jobs.size();
    int cur_layer = jobs[0]->current_layer; // all jobs have the same current layer
    size_t a_dtype_size = dtype_size(model_.get_activation_dtype());
    assert(device == "GPU" && "Only GPU pre attn decode is supported");

    auto ir = pre_attn_gpu_dyn_models_[cur_layer].create_infer_request();
    ir.set_input_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, dim}, decode_buf.prompt_embedding->at(0)));
    ir.set_output_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, dim}, decode_buf.Q_proj->at(0)));
    ir.set_output_tensor(
        1, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, kv_dim}, decode_buf.K_proj->at(0)));
    ir.set_output_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, kv_dim},
                                       decode_buf.v_cache_decode->at(0)));
    ir.infer();

    // dispatch v_cache to each job
    for (size_t i = 0; i < batch_size; i++) {
        memcpy(jobs[i]->v_cache->at(jobs[i]->tok_pos), decode_buf.v_cache_decode->at(i),
               kv_dim * a_dtype_size);
        jobs[i]->last_finished_op = op_t::OV_PRE_ATTN;
    }
}

void ContextOV::proceed_attn_decode(std::vector<InferJob>& jobs, std::string device) {
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();
    size_t batch_size = jobs.size();
    size_t head_size = model_.get_config().head_size();
    assert(device == "GPU" && "Only GPU attn decode is supported");

    std::vector<ov::InferRequest> irs;
    for (size_t i = 0; i < batch_size; i++) {
        ov::InferRequest ir;
        if (i < (size_t)(batch_size * attn_cpu_offload_ratio_)) {
            ir = attn_cpu_model_.create_infer_request();
        } else {
            ir = attn_gpu_model_.create_infer_request();
        }
        ir.set_input_tensor(0,
                            ov::Tensor(a_dtype_ov_, ov::Shape{1, dim}, decode_buf.Q_proj->at(i)));
        ir.set_input_tensor(
            1, ov::Tensor(a_dtype_ov_, ov::Shape{1, kv_dim}, decode_buf.K_proj->at(i)));
        ir.set_input_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{(size_t)jobs[i]->tok_pos, kv_dim},
                                          jobs[i]->k_cache->at(0)));
        ir.set_input_tensor(3,
                            ov::Tensor(a_dtype_ov_, ov::Shape{(size_t)jobs[i]->tok_pos + 1, kv_dim},
                                       jobs[i]->v_cache->at(0)));
        ir.set_input_tensor(4, ov::Tensor(a_dtype_ov_, ov::Shape{1, 1, head_size / 2, 2},
                                          model_.get_freqs_cis()->at(jobs[i]->tok_pos)));
        bool is_decode = true;
        ir.set_input_tensor(5, ov::Tensor(ov::element::boolean, ov::Shape{}, &is_decode));
        ir.set_output_tensor(
            0, ov::Tensor(a_dtype_ov_, ov::Shape{1, dim}, decode_buf.weighted_V->at(i)));
        ir.set_output_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{1, kv_dim},
                                           jobs[i]->k_cache->at(jobs[i]->tok_pos)));
        irs.push_back(std::move(ir));
    }
    for (auto& ir : irs) {
        ir.start_async();
    }
    for (auto& ir : irs) {
        ir.wait();
    }
    for (size_t i = 0; i < batch_size; i++) {
        jobs[i]->last_finished_op = op_t::OV_ATTN;
    }
}

void ContextOV::proceed_post_attn_decode(std::vector<InferJob>& jobs, std::string device) {
    size_t dim = model_.get_config().dim;
    size_t batch_size = jobs.size();
    int cur_layer = jobs[0]->current_layer; // all jobs have the same current layer
    assert(device == "GPU" && "Only GPU post attn decode is supported");

    auto ir = post_attn_gpu_dyn_models_[cur_layer].create_infer_request();
    ir.set_input_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, dim}, decode_buf.prompt_embedding->at(0)));
    ir.set_input_tensor(
        1, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, dim}, decode_buf.weighted_V->at(0)));
    ir.set_output_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, dim}, decode_buf.prompt_embedding->at(0)));
    ir.infer();

    // wrap up this layer's decode
    for (size_t i = 0; i < batch_size; i++) {
        jobs[i]->last_finished_op = op_t::OV_POST_ATTN;
        if (cur_layer < model_.get_config().n_layers - 1) {
            jobs[i]->current_layer++;
        }
    }
}

void ContextOV::proceed_layer_decode(std::vector<InferJob>& jobs, std::string device) {
    assert(device == "GPU" && "Only GPU layer decode is supported");
    size_t dim = model_.get_config().dim;
    size_t kv_dim = model_.get_config().kv_dim();
    size_t head_dim = dim / model_.get_config().n_heads;
    bool is_decode = true;
    std::vector<ov::InferRequest> irs;

    for (size_t i = 0; i < jobs.size(); i++) {
        auto ir = layer_gpu_models_[jobs[i]->current_layer].create_infer_request();
        ir.set_input_tensor(
            0, ov::Tensor(a_dtype_ov_, ov::Shape{1, dim}, decode_buf.prompt_embedding->at(i)));
        ir.set_input_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{1, 1, head_dim / 2, 2},
                                          model_.get_freqs_cis()->at(jobs[i]->tok_pos)));
        ir.set_input_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{jobs[i]->tok_pos, kv_dim},
                                          jobs[i]->k_cache->at(0)));
        ir.set_input_tensor(3, ov::Tensor(a_dtype_ov_, ov::Shape{jobs[i]->tok_pos, kv_dim},
                                          jobs[i]->v_cache->at(0)));
        ir.set_input_tensor(4, ov::Tensor(ov::element::boolean, ov::Shape{}, &is_decode));
        ir.set_output_tensor(
            0, ov::Tensor(a_dtype_ov_, ov::Shape{1, dim}, decode_buf.prompt_embedding->at(i)));
        ir.set_output_tensor(1, ov::Tensor(a_dtype_ov_, ov::Shape{1, kv_dim},
                                           jobs[i]->k_cache->at(jobs[i]->tok_pos)));
        ir.set_output_tensor(2, ov::Tensor(a_dtype_ov_, ov::Shape{1, kv_dim},
                                           jobs[i]->v_cache->at(jobs[i]->tok_pos)));
        irs.push_back(std::move(ir));
    }

    for (auto& ir : irs) {
        ir.start_async();
    }
    for (auto& ir : irs) {
        ir.wait();
    }

    // wrap up this layer's decode
    for (size_t i = 0; i < jobs.size(); i++) {
        jobs[i]->last_finished_op = op_t::OV_LLAMA_LAYER;
        if (jobs[i]->current_layer < model_.get_config().n_layers - 1) {
            jobs[i]->current_layer++;
        }
    }
}

void ContextOV::proceed_final_out_decode(std::vector<InferJob>& jobs, std::string device) {
    size_t dim = model_.get_config().dim;
    size_t vocab_size = model_.get_config().vocab_size;
    size_t batch_size = jobs.size();
    assert(device == "GPU" && "Only GPU final out decode is supported");

    auto ir = final_out_gpu_model_.create_infer_request();
    ir.set_input_tensor(
        0, ov::Tensor(a_dtype_ov_, ov::Shape{batch_size, dim}, decode_buf.prompt_embedding->at(0)));
    ir.set_output_tensor(0, ov::Tensor(logits_dtype_ov_, ov::Shape{batch_size, vocab_size},
                                       decode_buf.final_out->at(0)));
    ir.infer();
}

void ContextOV::decode_job_batch_swapout(std::vector<InferJob>& jobs) {
    for (size_t i = 0; i < jobs.size(); i++) {
        // wrap up this decode iteration
        jobs[i]->last_finished_op = op_t::OV_FINAL_OUT;
        jobs[i]->tok_pos++;
        jobs[i]->current_layer = 0;
        int next_token = sampler_.sample(decode_buf.final_out->at(i), jobs[i]->temperature,
                                         jobs[i]->top_p, jobs[i]->seed);
        jobs[i]->generated_tokens.push_back(next_token);
    }
}

void ContextOV::parse_prompt_from_file(InferJob job, const char* prompt_path) {
    std::ifstream file(prompt_path);
    if (!file.is_open()) {
        logging::error() << "Couldn't open file " << prompt_path;
        return;
    }

    std::vector<std::string> all_lines;
    std::string line;
    while (std::getline(file, line)) {
        all_lines.push_back(line);
    }

    if (all_lines.size() != 1) {
        logging::error() << "File must have one line of tokens: " << prompt_path;
        return;
    }

    std::istringstream iss(all_lines[0]);
    job->prompt_tokens.clear();
    int token;
    while (iss >> token) {
        tokenizer_.check_token_index(token);
        job->prompt_tokens.push_back(token);
    }

    // decode the prompt tokens to string
    job->prompt_text = "";
    size_t i = 0;
    while (i < job->prompt_tokens.size()) {
        std::string token_str = tokenizer_.decode(job->prompt_tokens[i]);
        if (token_str == "<|start_header_id|>") {
            i++;
            continue;
        } else if (token_str == "<|end_header_id|>") {
            token_str = ": ";
            if (i + 1 < job->prompt_tokens.size()) {
                std::string next_token_str = tokenizer_.decode(job->prompt_tokens[i + 1]);
                if (next_token_str == "\n" || next_token_str == "\n\n" ||
                    next_token_str == "\n\n\n" || next_token_str == "\n\n\n\n") {
                    i++;
                }
            }
        } else if (token_str == "<|eot_id|>") {
            token_str = "\n\n";
        }
        job->prompt_text += token_str;
        i++;
    }
}

void ContextOV::run_individual_infer(const char* prompt_path, int steps, float temperature,
                                     float top_p, int seed) {
    auto decode_and_print = [this](int next_tok) {
        const char* piece = tokenizer_.decode(next_tok);
        std::cout << piece << std::flush;
    };

    InferJob job = create_infer_job("individual_infer");
    job->alloc_kv_cache(CTX_LEN_, model_.get_config().kv_dim(), model_.get_activation_dtype());
    parse_prompt_from_file(job, prompt_path);
    logging::info() << "Prompt length: " << job->prompt_tokens.size();
    std::cout << job->prompt_text << std::flush;
    job->temperature = temperature;
    job->top_p = top_p;
    job->seed = seed;
    job->priority = JobPriority::reactive;

    // prefill
    prefill_job_swapin(job);
    auto begin = get_time();
    proceed_prefill_hetero_async(job, prefill_gpu_ratio_);
    prefill_job_swapout(job);
    auto active_prefill_time = elapsed_time(begin);
    int next_token = job->generated_tokens.back();
    decode_and_print(next_token);

    // decode
    std::vector<InferJob> jobs_decode = {job};
    std::signal(SIGINT, signal_handler);
    begin = get_time();
    while (job->generated_tokens.size() < (size_t)steps && (size_t)job->tok_pos < CTX_LEN_) {
        if (interrupted.load()) {
            std::cout << std::endl;
            logging::warn() << "Interrupted by user";
            break;
        }

        decode_job_batch_swapin(jobs_decode);
        for (int l = 0; l < model_.get_config().n_layers; l++) {
            if (enable_layer_gpu_infer_) {
                proceed_layer_decode(jobs_decode, "GPU");
            } else {
                proceed_pre_attn_decode(jobs_decode, "GPU");
                proceed_attn_decode(jobs_decode, "GPU");
                proceed_post_attn_decode(jobs_decode, "GPU");
            }
        }
        proceed_final_out_decode(jobs_decode, "GPU");
        decode_job_batch_swapout(jobs_decode);

        next_token = job->generated_tokens.back();
        if (model_.is_end_of_generation(next_token)) {
            break;
        }
        decode_and_print(next_token);
    }
    auto active_decode_time = elapsed_time(begin);
    std::cout << std::endl;

    logging::info() << "Prefill " << job->prompt_tokens.size() << " tokens at "
                    << job->prompt_tokens.size() / active_prefill_time << " tok/s";
    logging::info() << "Decode " << job->generated_tokens.size() - 1 << " tokens at "
                    << (job->generated_tokens.size() - 1) / active_decode_time << " tok/s";
}

void ContextOV::run_individual_infer(InferJob job, InferDevice device) {
    assert(device == InferDevice::IntelGPU || device == InferDevice::IntelNPU);
    job->alloc_kv_cache(CTX_LEN_, model_.get_config().kv_dim(), model_.get_activation_dtype());

    // prefill
    float prefill_gpu_ratio = device == InferDevice::IntelGPU ? 1.0 : 0.0;
    auto begin = get_time();
    int buf_idx = job->priority == JobPriority::reactive ? 1 : 0;
    prefill_job_swapin(job, buf_idx);
    proceed_prefill_hetero_async(job, prefill_gpu_ratio);
    prefill_job_swapout(job, buf_idx);
    job->active_prefill_time = elapsed_time(begin);

    // decode
    begin = get_time();
    std::vector<InferJob> jobs_decode = {job};
    while (job->generated_tokens.size() < (size_t)job->max_steps &&
           (size_t)job->tok_pos < CTX_LEN_) {
        decode_job_batch_swapin(jobs_decode);
        for (int l = 0; l < model_.get_config().n_layers; l++) {
            proceed_pre_attn_decode(jobs_decode, "GPU");
            proceed_attn_decode(jobs_decode, "GPU");
            proceed_post_attn_decode(jobs_decode, "GPU");
        }
        proceed_final_out_decode(jobs_decode, "GPU");
        decode_job_batch_swapout(jobs_decode);
    }
    job->active_decode_time = elapsed_time(begin);
}

void ContextOV::start_async_processing() {
    if (async_running_.load()) {
        logging::warn() << "Async processing is already running";
        return;
    }

    async_running_.store(true);

    // Start event loop threads
    prefill_thread_ = std::thread(&ContextOV::prefill_event_loop, this);
    decode_thread_ = std::thread(&ContextOV::decode_event_loop, this);
    gc_thread_ = std::thread(&ContextOV::gc_event_loop, this);

    logging::info()
        << "Started async processing with prefill, decode, and garbage collection event loops";
}

void ContextOV::stop_async_processing() {
    if (!async_running_.load()) {
        logging::warn() << "Async processing is not running";
        return;
    }

    async_running_.store(false);

    // Wake up all waiting threads
    prefill_cv_.notify_all();
    decode_cv_.notify_all();
    gc_cv_.notify_all();
    if (is_pd_blocking_) {
        pd_sync_cv_.notify_all();
    }

    // Wait for threads to finish
    if (prefill_thread_.joinable()) {
        prefill_thread_.join();
    }
    if (decode_thread_.joinable()) {
        decode_thread_.join();
    }
    if (gc_thread_.joinable()) {
        gc_thread_.join();
    }

    logging::info() << "Stopped async processing";
}

void ContextOV::submit_job(InferJob job) {
    if (!async_running_.load()) {
        logging::error() << "Cannot submit job: async processing is not running";
        return;
    }
    alive_jobs_count_.fetch_add(1);

    // Record submission time for elapsed time tracking
    job->submit_time = get_time();

    // Allocate KV cache for the job
    job->alloc_kv_cache(CTX_LEN_, model_.get_config().kv_dim(), model_.get_activation_dtype());

    // Add job to prefill queue
    {
        std::lock_guard<std::mutex> lock(prefill_mutex_);
        if (job->priority == JobPriority::reactive) {
            prefill_queue_high_priority_.emplace(job);
        } else {
            prefill_queue_.emplace(job);
        }
    }
    prefill_cv_.notify_one();

    logging::info() << "Submitted job " << job->uuid << " (priority: " << job->priority << ")";
}

void ContextOV::move_job_to_decode(InferJob job) {
    // Calculate elapsed prefill time
    job->elapsed_prefill_time = elapsed_time(job->submit_time);

    // Record decode start time
    job->decode_start_time = get_time();

    {
        std::lock_guard<std::mutex> lock(decode_mutex_);
        if (job->priority == JobPriority::reactive) {
            decode_queue_high_priority_.push(job);
        } else {
            decode_queue_.push_back(job);
        }
    }
    decode_cv_.notify_one();
}

void ContextOV::complete_job(InferJob job) {
    // Calculate elapsed decode time
    job->elapsed_decode_time = elapsed_time(job->decode_start_time);
    job->elapsed_time = elapsed_time(job->submit_time);

    // Log timing statistics for the completed job
    logging::info() << "Job " << job->uuid << " (priority: " << job->priority << ") completed\n"
                    << "\t  - Prefill: " << job->prompt_tokens.size() << " tokens in "
                    << job->active_prefill_time << "s ("
                    << job->prompt_tokens.size() / job->active_prefill_time
                    << " tok/s) [pending: " << job->elapsed_prefill_time - job->active_prefill_time
                    << "s]\n"
                    << "\t  - Decode: " << job->generated_tokens.size() << " tokens in "
                    << job->active_decode_time << "s ("
                    << job->generated_tokens.size() / job->active_decode_time
                    << " tok/s) [pending: " << job->elapsed_decode_time - job->active_decode_time
                    << "s]";

    if (job->on_complete) {
        job->on_complete(job);
    }

    // Add job to garbage collection queue for asynchronous cleanup
    {
        std::lock_guard<std::mutex> lock(gc_mutex_);
        gc_queue_.push(job);
    }
    gc_cv_.notify_one();
}

void ContextOV::continue_or_preempt(InferJob current_job) {
    if (current_job->priority == JobPriority::reactive) {
        return; // reactive jobs cannot be preempted
    }
    InferJob new_job = nullptr;
    {
        std::lock_guard<std::mutex> lock(prefill_mutex_);
        if (prefill_queue_high_priority_.empty()) {
            return;
        }
        new_job = prefill_queue_high_priority_.front();
        prefill_queue_high_priority_.pop();
    }
    if (new_job) {
        logging::debug() << "Job " << current_job->uuid << " preempted by " << new_job->uuid;
        try {
            auto begin = get_time();
            prefill_job_swapin(new_job);
            proceed_prefill_hetero_async(new_job, prefill_gpu_ratio_);
            prefill_job_swapout(new_job);
            new_job->active_prefill_time = elapsed_time(begin);
            move_job_to_decode(new_job);
        } catch (const std::exception& e) {
            logging::error() << "Error in prefill for job " << new_job->uuid << ": " << e.what();
            // Calculate elapsed prefill time before completing the job
            new_job->elapsed_prefill_time = elapsed_time(new_job->submit_time);
            // Complete the job with error
            complete_job(new_job);
        }
    }
}

void ContextOV::prefill_event_loop() {
    while (async_running_.load()) {
        InferJob job;

        // Wait for a job in the prefill queue
        {
            std::unique_lock<std::mutex> lock(prefill_mutex_);
            prefill_cv_.wait(lock, [this] {
                return !prefill_queue_.empty() || !prefill_queue_high_priority_.empty() ||
                       !async_running_.load();
            });

            if (!async_running_.load()) {
                break;
            }

            if (!prefill_queue_high_priority_.empty()) {
                job = prefill_queue_high_priority_.front();
                prefill_queue_high_priority_.pop();
            } else if (!prefill_queue_.empty()) {
                job = prefill_queue_.front();
                prefill_queue_.pop();
            } else {
                continue;
            }
        }
        is_prefill_running_.store(true);

        logging::debug() << "Processing prefill for job " << job->uuid
                         << " (priority: " << job->priority << ") with "
                         << job->prompt_tokens.size() << " tokens";

        try {
            auto begin = get_time();

            // Swapin job
            prefill_job_swapin(job);

            // Process through all layers
            proceed_prefill_hetero_async(job, prefill_gpu_ratio_);

            // Swapout and transition to decode stage
            prefill_job_swapout(job);

            // Store prefill timing in the job
            job->active_prefill_time = elapsed_time(begin);
            // logging::info() << "Prefill completed for job " << job->uuid
            //                << " (" << job->prompt_tokens.size() << " tokens at "
            //                << job->prompt_tokens.size() / job->active_prefill_time << " tok/s)";

            // Move job to decode queue
            is_prefill_running_.store(false);
            if (is_pd_blocking_) {
                pd_sync_cv_.notify_one();
            }
            move_job_to_decode(job);

        } catch (const std::exception& e) {
            logging::error() << "Error in prefill for job " << job->uuid << ": " << e.what();
            // Calculate elapsed prefill time before completing the job
            job->elapsed_prefill_time = elapsed_time(job->submit_time);
            // Complete the job with error
            complete_job(job);
        }
    }
}

void ContextOV::decode_event_loop() {
    std::vector<InferJob> current_batch;
    double pre_attn_time = 0;
    double attn_time = 0;
    double post_attn_time = 0;
    double final_out_time = 0;
    int profiled_iters = 0;
    int active_reactive_jobs = 0;

    while (async_running_.load()) {
        if (is_pd_blocking_) {
            std::unique_lock<std::mutex> lock(pd_sync_mutex_);
            pd_sync_cv_.wait(
                lock, [this] { return !is_prefill_running_.load() || !async_running_.load(); });
        }
        // Step 1: Add newly arrived jobs to current batch at the beginning of each iteration
        {
            std::lock_guard<std::mutex> lock(decode_mutex_);
            // case 1: pure reactive batch, add all existing reactive jobs to the batch
            if (decode_queue_high_priority_.size() + active_reactive_jobs >=
                max_reactive_decode_batch_size_) {
                // first, swap out proactive jobs in the current batch
                for (auto it = current_batch.begin(); it != current_batch.end(); ++it) {
                    if ((*it)->priority != JobPriority::reactive) {
                        decode_queue_.push_front(*it);
                        current_batch.erase(it);
                        it--;
                    }
                }
                while (!decode_queue_high_priority_.empty()) {
                    InferJob new_job = decode_queue_high_priority_.front();
                    decode_queue_high_priority_.pop();
                    current_batch.push_back(new_job);
                    logging::debug()
                        << "Added job " << new_job->uuid << " (priority: " << new_job->priority
                        << ") to decode batch, current batch size: " << current_batch.size();
                    active_reactive_jobs++;
                }
            } else if (!decode_queue_high_priority_.empty() ||
                       active_reactive_jobs > 0) { // reactive job exists
                // case 2: reactive-proactive hybrid batch, under a moderate batch size
                while (!decode_queue_high_priority_.empty()) {
                    InferJob new_job = decode_queue_high_priority_.front();
                    decode_queue_high_priority_.pop();
                    current_batch.push_back(new_job);
                    logging::debug()
                        << "Added job " << new_job->uuid << " (priority: " << new_job->priority
                        << ") to decode batch, current batch size: " << current_batch.size();
                    active_reactive_jobs++;
                }
                while (!decode_queue_.empty() &&
                       current_batch.size() < max_reactive_decode_batch_size_) {
                    InferJob new_job = decode_queue_.front();
                    decode_queue_.pop_front();
                    current_batch.push_back(new_job);
                    logging::debug()
                        << "Added job " << new_job->uuid << " (priority: " << new_job->priority
                        << ") to decode batch, current batch size: " << current_batch.size();
                }
                while (current_batch.size() > max_reactive_decode_batch_size_) {
                    // remove residual proactive jobs
                    for (auto it = current_batch.begin(); it != current_batch.end(); ++it) {
                        if ((*it)->priority != JobPriority::reactive) {
                            decode_queue_.push_front(*it);
                            current_batch.erase(it);
                            break;
                        }
                    }
                }
            } else {
                // case 3: pure proactive batch, add all existing proactive jobs to the batch
                while (!decode_queue_.empty() && current_batch.size() < MAX_DECODE_BATCH_SIZE_) {
                    InferJob new_job = decode_queue_.front();
                    decode_queue_.pop_front();
                    current_batch.push_back(new_job);
                    logging::debug()
                        << "Added job " << new_job->uuid << " (priority: " << new_job->priority
                        << ") to decode batch, current batch size: " << current_batch.size();
                }
            }
        }

        // If no jobs available, wait for new jobs
        if (current_batch.empty()) {
            std::unique_lock<std::mutex> lock(decode_mutex_);
            decode_cv_.wait(lock, [this] {
                return !decode_queue_.empty() || !decode_queue_high_priority_.empty() ||
                       !async_running_.load();
            });

            if (!async_running_.load()) {
                break;
            }
            continue;
        }

        try {
            // Step 2: Process one decode iteration for all jobs in current batch
            auto decode_begin = get_time();

            // Swapin current batch
            decode_job_batch_swapin(current_batch);

            // Process through all layers for one iteration
            if (enable_decode_profiling_) {
                for (int l = 0; l < model_.get_config().n_layers; l++) {
                    auto pre_attn_begin = get_time();
                    proceed_pre_attn_decode(current_batch, "GPU");
                    pre_attn_time += elapsed_time(pre_attn_begin);
                    auto attn_begin = get_time();
                    proceed_attn_decode(current_batch, "GPU");
                    attn_time += elapsed_time(attn_begin);
                    auto post_attn_begin = get_time();
                    proceed_post_attn_decode(current_batch, "GPU");
                    post_attn_time += elapsed_time(post_attn_begin);
                }
                auto final_out_begin = get_time();
                proceed_final_out_decode(current_batch, "GPU");
                final_out_time += elapsed_time(final_out_begin);
                profiled_iters++;
            } else {
                if (enable_layer_gpu_infer_ && current_batch.size() == 1) {
                    for (int l = 0; l < model_.get_config().n_layers; l++) {
                        proceed_layer_decode(current_batch, "GPU");
                    }
                } else {
                    for (int l = 0; l < model_.get_config().n_layers; l++) {
                        proceed_pre_attn_decode(current_batch, "GPU");
                        proceed_attn_decode(current_batch, "GPU");
                        proceed_post_attn_decode(current_batch, "GPU");
                    }
                }
                proceed_final_out_decode(current_batch, "GPU");
            }

            decode_job_batch_swapout(current_batch);

            // Calculate decode time for this iteration and distribute among jobs
            double iteration_time = elapsed_time(decode_begin);
            for (auto& job : current_batch) {
                job->active_decode_time += iteration_time;
            }

            // Step 3: Remove finished jobs at the end of each iteration
            auto batch_iter = current_batch.begin();
            while (batch_iter != current_batch.end()) {
                InferJob job = *batch_iter;
                bool should_complete = false;

                // Check completion conditions
                if (job->generated_tokens.size() >= job->max_steps) {
                    // Reached max steps limit
                    should_complete = true;
                    logging::warn() << "Job " << job->uuid << " reached max steps limit";
                } else if ((size_t)job->tok_pos >= CTX_LEN_) {
                    // Reached absolute token position limit
                    should_complete = true;
                    logging::warn() << "Job " << job->uuid << " reached context length limit";
                } else if (!job->generated_tokens.empty() &&
                           model_.is_end_of_generation(job->generated_tokens.back())) {
                    // Generated end-of-generation token
                    should_complete = true;
                    logging::info() << "Job " << job->uuid << " generated end token";
                }

                if (should_complete) {
                    // Complete and remove this job
                    complete_job(job);
                    if (job->priority == JobPriority::reactive) {
                        active_reactive_jobs--;
                    }
                    batch_iter = current_batch.erase(batch_iter);
                    if (enable_decode_profiling_) {
                        std::cout << "(" << profiled_iters << " iters) " << std::fixed
                                  << std::setprecision(3)
                                  << "Pre Attn: " << pre_attn_time / profiled_iters << "s, "
                                  << "Attn: " << attn_time / profiled_iters << "s, "
                                  << "Post Attn: " << post_attn_time / profiled_iters << "s, "
                                  << "Final Out: " << final_out_time / profiled_iters << "s\n";
                        pre_attn_time = 0;
                        attn_time = 0;
                        post_attn_time = 0;
                        final_out_time = 0;
                        profiled_iters = 0;
                    }
                } else {
                    ++batch_iter;
                }
            }

            // if (!current_batch.empty()) {
            //     logging::info() << "Decode iteration completed for " << current_batch.size()
            //                    << " jobs in " << iteration_time << "s";
            // }

        } catch (const std::exception& e) {
            logging::error() << "Error in decode iteration: " << e.what();
            // Complete all jobs in current batch with error
            for (const auto& job : current_batch) {
                complete_job(job);
            }
            current_batch.clear();
        }
    }

    // Complete any remaining jobs when shutting down
    for (const auto& job : current_batch) {
        complete_job(job);
    }
}

void ContextOV::gc_event_loop() {
    while (async_running_.load()) {
        InferJob job;

        // Wait for a job in the GC queue
        {
            std::unique_lock<std::mutex> lock(gc_mutex_);
            gc_cv_.wait(lock, [this] { return !gc_queue_.empty() || !async_running_.load(); });

            if (!async_running_.load()) {
                break;
            }

            if (!gc_queue_.empty()) {
                job = gc_queue_.front();
                gc_queue_.pop();
            } else {
                continue;
            }
        }
        try {
            // Explicitly release memory before resetting the shared_ptr
            job->release_memory();
            job.reset();
            alive_jobs_count_.fetch_sub(1);
            // Notify completion condition variable after job is fully processed
            completion_cv_.notify_one();
        } catch (const std::exception& e) {
            logging::error() << "Exception during garbage collection of job " << job->uuid << ": "
                             << e.what();
            alive_jobs_count_.fetch_sub(1);
            completion_cv_.notify_one();
        } catch (...) {
            logging::error() << "Unknown exception during garbage collection of job " << job->uuid;
            alive_jobs_count_.fetch_sub(1);
            completion_cv_.notify_one();
        }
    }

    // Process any remaining jobs when shutting down
    while (!gc_queue_.empty()) {
        auto job = gc_queue_.front();
        gc_queue_.pop();

        try {
            job->release_memory();
            job.reset();
            alive_jobs_count_.fetch_sub(1);
            completion_cv_.notify_one();
        } catch (...) {
            // Ignore exceptions during shutdown, but still notify completion
            alive_jobs_count_.fetch_sub(1);
            completion_cv_.notify_one();
        }
    }
}

void ContextOV::wait_all_jobs_to_complete() {
    if (!async_running_.load()) {
        logging::warn() << "Async processing is not running, no jobs to wait for";
        return;
    }

    logging::info() << "Waiting for all jobs to complete...";

    // Wait until all jobs are completed
    std::unique_lock<std::mutex> lock(completion_mutex_);
    completion_cv_.wait(lock, [this] { return alive_jobs_count_.load() == 0; });

    logging::info() << "All jobs completed";
}

} // namespace hllm