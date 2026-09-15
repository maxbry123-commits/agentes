#include "infer-job.h"

namespace hllm {

__InferJob::__InferJob(std::string uuid, JobPriority priority) : uuid(uuid), priority(priority) {}

void __InferJob::alloc_kv_cache(size_t ctx_len, size_t kv_dim, Dtype dtype) {
    k_cache = create_param(dtype, {ctx_len, kv_dim}, ALLOC);
    v_cache = create_param(dtype, {ctx_len, kv_dim}, ALLOC);
}

void __InferJob::release_memory() {
    k_cache.reset();
    v_cache.reset();
}

InferJob create_infer_job(std::string uuid, JobPriority priority) {
    return std::make_shared<__InferJob>(uuid, priority);
}

void print_stats(InferJob job) {
    // use std::cerr for independent redirection
    std::cerr << "##### Job " << job->uuid << " (" << job->priority << ")" << std::endl;
    std::cerr << "  - Prompt tokens: " << job->prompt_tokens.size() << std::endl;
    std::cerr << "  - Generated tokens: " << job->generated_tokens.size() << std::endl;
    std::cerr << "  - Elapsed prefill time (s): " << job->elapsed_prefill_time << std::endl;
    std::cerr << "  - Elapsed decode time (s): " << job->elapsed_decode_time << std::endl;
    std::cerr << "  - Active prefill time (s): " << job->active_prefill_time << std::endl;
    std::cerr << "  - Active decode time (s): " << job->active_decode_time << std::endl;
    std::cerr << "  - Elapsed time (s): " << job->elapsed_time << std::endl;
}

} // namespace hllm