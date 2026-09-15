#pragma once

#include "basic/device.h"
#include "basic/tensor.h"
#include "end2end/infer-job.h"
#include "frontend/sampler.h"
#include "frontend/tokenizer.h"
#include "models/llama.h"

#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <mutex>
#include <openvino/openvino.hpp>
#include <openvino/runtime/compiled_model.hpp>
#include <openvino/runtime/infer_request.hpp>
#include <queue>
#include <thread>

namespace hllm {

class ContextOV {
  public:
    ContextOV(const char* model_path, bool enable_layer_decode = false,
              bool enable_ov_cache = true);
    ~ContextOV();

    Llama& model() { return model_; }
    ov::Core& ov_core() { return ov_core_; }

    // for single-batch inference
    void run_individual_infer(const char* prompt_path, int steps, float temperature, float top_p,
                              int seed);
    // for experiment usage
    void run_individual_infer(InferJob job, InferDevice device);

    // Asynchronous job processing
    void start_async_processing();
    void stop_async_processing();
    void submit_job(InferJob job);
    bool is_async_running() const { return async_running_.load(); }
    void wait_all_jobs_to_complete();

    // Inference options
    void set_prefill_gpu_ratio(float prefill_gpu_ratio) { prefill_gpu_ratio_ = prefill_gpu_ratio; }
    void set_layer_decode_gpu_infer(bool enable) { enable_layer_gpu_infer_ = enable; }
    void set_decode_profiling(bool enable) { enable_decode_profiling_ = enable; }
    void set_pd_blocking(bool enable) { is_pd_blocking_ = enable; }
    void set_decode_attn_cpu_offload_ratio(float ratio) { attn_cpu_offload_ratio_ = ratio; }
    void set_chunk_size(size_t chunk_size) { CHUNK_SIZE_ = chunk_size; }
    void set_max_decode_batch_size(size_t max_decode_batch_size) {
        MAX_DECODE_BATCH_SIZE_ = max_decode_batch_size;
    }
    void set_gpu_chunked_prefill(bool enable) { is_gpu_chunked_prefill_ = enable; }

  private:
    // single-batch (probably chunked) prefill, doing once for each job
    void prefill_job_swapin(InferJob job, int buf_idx = 0);
    void proceed_pre_attn_prefill(InferJob job, std::string device, size_t start_idx, size_t len,
                                  int buf_idx = 0);
    void proceed_attn_prefill(InferJob job, std::string device = "GPU", int buf_idx = 0);
    void proceed_post_attn_prefill(InferJob job, std::string device, size_t start_idx, size_t len,
                                   int buf_idx = 0);
    void proceed_final_out_prefill(InferJob job, std::string device = "GPU", int buf_idx = 0);
    void proceed_prefill_hetero_async(InferJob job, float prefill_gpu_ratio);
    void prefill_job_swapout(InferJob job, int buf_idx = 0);

    // batched decode, doing each decode iteration for each job
    void decode_job_batch_swapin(std::vector<InferJob>& jobs);
    void proceed_pre_attn_decode(std::vector<InferJob>& jobs, std::string device = "GPU");
    void proceed_attn_decode(std::vector<InferJob>& jobs, std::string device = "GPU");
    void proceed_post_attn_decode(std::vector<InferJob>& jobs, std::string device = "GPU");
    void proceed_final_out_decode(std::vector<InferJob>& jobs, std::string device = "GPU");
    void decode_job_batch_swapout(std::vector<InferJob>& jobs);
    void proceed_layer_decode(std::vector<InferJob>& jobs, std::string device = "GPU");

    // job context switching
    void continue_or_preempt(InferJob current_job);

    // model (llama)
    Llama model_;
    // frontend
    Sampler sampler_;
    LlamaTokenizer tokenizer_;
    // ov runtime
    ov::Core ov_core_;
    std::string cache_dir_;
    ov::element::Type a_dtype_ov_;
    ov::element::Type logits_dtype_ov_ = ov::element::f32;
    // Inference params
    size_t MAX_DECODE_BATCH_SIZE_ = 16;
    size_t CTX_LEN_ = 4096;
    size_t CHUNK_SIZE_ = 256;
    float prefill_gpu_ratio_ = 0;
    bool enable_layer_gpu_infer_ = false;
    size_t max_reactive_decode_batch_size_ = 3; // max decode batch size with reactive jobs inside
    bool enable_decode_profiling_ = false;
    bool is_pd_blocking_ = false;
    float attn_cpu_offload_ratio_ = 0.7;
    bool is_gpu_chunked_prefill_ = false;

    // gpu for dynamic shape prefill or decode, npu for chunked prefill
    // same ir cannot be reused for different chunks or stages in the async mode
    std::vector<ov::CompiledModel> pre_attn_gpu_dyn_models_, pre_attn_npu_chunked_models_;
    std::vector<ov::CompiledModel> post_attn_gpu_dyn_models_, post_attn_npu_chunked_models_;
    ov::CompiledModel attn_gpu_model_;
    ov::CompiledModel attn_cpu_model_; // for decode
    ov::CompiledModel final_out_gpu_model_;
    std::vector<ov::CompiledModel> layer_gpu_models_;

    // Pre-compile XPU kernels and set input/output tensors
    void warmup_q8_kernels();
    void warmup_f16_kernels();

    // Recurrent activation buffers shared by layers
    struct ActivationBuffer {
        // prompt embedding, input to pre_attn
        // - prefill shape: [max_seq_len, dim]
        // - decode shape: [max_decode_batch_size, dim]
        Tensor prompt_embedding;
        // Q projection, output of pre_attn
        // - prefill shape: [max_seq_len, dim]
        // - decode shape: [max_decode_batch_size, dim]
        Tensor Q_proj;
        // K projection, output of pre_attn
        // - prefill shape: [max_seq_len, kv_dim]
        // - decode shape: [max_decode_batch_size, kv_dim]
        Tensor K_proj;
        // v cache of decode batch for dispatching to each job
        // - shape: [max_decode_batch_size, kv_dim]
        Tensor v_cache_decode;
        // weighted V, output of attn
        // - prefill shape: [max_seq_len, dim]
        // - decode shape: [max_decode_batch_size, dim]
        Tensor weighted_V;
        // final out, not shared by the layers
        // - prefill shape: [1, vocab_size]
        // - decode shape: [max_decode_batch_size, vocab_size]
        Tensor final_out;
    };
    ActivationBuffer prefill_buf[2], decode_buf;

    // Allocate activation buffers
    void alloc_activation_buffer();

    void parse_prompt_from_file(InferJob job, const char* prompt_path);

    // Job queues and synchronization
    std::queue<InferJob> prefill_queue_;
    std::queue<InferJob> prefill_queue_high_priority_;
    std::deque<InferJob> decode_queue_;
    std::queue<InferJob> decode_queue_high_priority_;
    std::queue<InferJob> gc_queue_;
    std::mutex prefill_mutex_;
    std::mutex decode_mutex_;
    std::mutex gc_mutex_;
    std::mutex completion_mutex_;
    std::mutex pd_sync_mutex_;
    std::condition_variable prefill_cv_;
    std::condition_variable decode_cv_;
    std::condition_variable gc_cv_;
    std::condition_variable completion_cv_;
    std::condition_variable pd_sync_cv_;
    std::atomic<int> alive_jobs_count_{0};
    std::atomic<bool> is_prefill_running_{false};

    // Event loop control
    std::atomic<bool> async_running_{false};
    std::thread prefill_thread_;
    std::thread decode_thread_;
    std::thread gc_thread_;

    // Event loop functions
    void prefill_event_loop();
    void decode_event_loop();
    void gc_event_loop();
    void move_job_to_decode(InferJob job);
    void complete_job(InferJob job);
};

} // namespace hllm