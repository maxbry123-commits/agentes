#include "end2end/ov/context.h"

#include <cassert>
#include <cstring>
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cout << "Usage: " << argv[0] << " <model_path> <prompt_len> <max_steps> <gpu_ratio>"
                  << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    int prompt_len = atoi(argv[2]);
    int max_steps = atoi(argv[3]);
    float gpu_ratio = atof(argv[4]);
    hllm::ContextOV context(model_path);
    context.set_prefill_gpu_ratio(gpu_ratio);
    context.start_async_processing();

    std::string job_id = "job_0";
    hllm::InferJob job = hllm::create_infer_job(job_id);
    for (int j = 0; j < prompt_len; j++) {
        job->prompt_tokens.push_back(rand() % 126000 + 1);
    }
    job->max_steps = max_steps;
    context.submit_job(job);

    context.wait_all_jobs_to_complete();
    context.stop_async_processing();

    return 0;
}
