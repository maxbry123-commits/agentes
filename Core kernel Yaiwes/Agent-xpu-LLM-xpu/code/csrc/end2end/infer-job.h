#pragma once
#include "basic/dtype.h"
#include "basic/tensor.h"

#include <chrono>
#include <functional>

namespace hllm {

struct __InferJob;
using InferJob = std::shared_ptr<__InferJob>;

struct __InferJob {
    __InferJob(std::string uuid, JobPriority priority);
    void alloc_kv_cache(size_t ctx_len, size_t kv_dim, Dtype dtype);
    void release_memory(); // explicitly release memory of the job

    // job uuid
    std::string uuid;
    // Inference meta info
    std::vector<int> prompt_tokens;
    std::string prompt_text;
    JobPriority priority;
    size_t max_steps = 1024;
    float temperature = 0.6;
    float top_p = 0.9;
    int seed = -1;

    // Intermediate states
    InferStage stage = InferStage::prefill;
    size_t tok_pos = 0;
    int current_layer = 0;
    op_t last_finished_op = op_t::NONE;
    std::vector<int> generated_tokens;
    size_t decode_batch_offset = 0;

    // KV cache
    Tensor k_cache;
    Tensor v_cache;

    // Callbacks
    std::function<void(InferJob)> on_complete;

    // Stats
    double elapsed_prefill_time = 0; // elapsed time of prefill stage
    double elapsed_decode_time = 0;  // elapsed time of decode stage
    double active_prefill_time = 0;  // active time of prefill stage
    double active_decode_time = 0;   // active time of decode stage
    double elapsed_time = 0;         // elapsed time of the job

    // Timestamps for elapsed time tracking
    std::chrono::steady_clock::time_point submit_time;
    std::chrono::steady_clock::time_point decode_start_time;
};

InferJob create_infer_job(std::string uuid, JobPriority priority = JobPriority::none);

void print_stats(InferJob job);

} // namespace hllm