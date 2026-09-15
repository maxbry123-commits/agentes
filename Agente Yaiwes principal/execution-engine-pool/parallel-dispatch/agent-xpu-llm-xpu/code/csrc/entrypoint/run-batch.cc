// Comment the prefill part in context.cc to enable decode profiling

#include "end2end/ov/context.h"

#include <cassert>
#include <cstring>
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cout << "Usage: " << argv[0] << " <model_path> <batch_size> <seq_len>" << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    int batch_size = std::stoi(argv[2]);
    int seq_len = std::stoi(argv[3]);
    hllm::ContextOV context(model_path, false);
    context.set_prefill_gpu_ratio(0.6);
    context.set_decode_profiling(true);
    context.start_async_processing();

    std::vector<hllm::InferJob> jobs;
    for (int i = 0; i < batch_size; i++) {
        std::string job_id = "job_" + std::to_string(i);
        hllm::InferJob job = hllm::create_infer_job(job_id);
        for (int j = 0; j < seq_len; j++) {
            job->prompt_tokens.push_back(rand() % 128000);
        }
        job->max_steps = 64;
        jobs.push_back(job);
    }

    for (int i = 0; i < batch_size; i++) {
        context.submit_job(jobs[i]);
    }

    context.wait_all_jobs_to_complete();
    context.stop_async_processing();

    return 0;
}
