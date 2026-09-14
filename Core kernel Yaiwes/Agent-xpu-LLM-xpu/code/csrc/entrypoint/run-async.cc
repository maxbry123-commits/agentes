#include "end2end/ov/context.h"

#include <cassert>
#include <cstring>
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cout << "Usage: " << argv[0] << " <model_path>" << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    hllm::ContextOV context(model_path, false);
    context.set_prefill_gpu_ratio(0.6);
    context.start_async_processing();

    for (int i = 0; i < 100; i++) {
        std::string job_id = "job_" + std::to_string(i);
        hllm::InferJob job = hllm::create_infer_job(job_id);
        // job->prompt_tokens = {128000, 128006, 9125,   128007, 271,  38766, 1303,  33025,  2696,
        //                       25,     6790,   220,    2366,   18,   198,   15724, 2696,   25,
        //                       220,    914,    10263,  220,    2366, 20,    271,   128009, 128006,
        //                       882,    128007, 271,    3923,   374,  279,   5133,  1990,   393,
        //                       59952,  3907,   323,    26132,  287,  92336, 3907,  30,     128009,
        //                       128006, 78191,  128007, 271};
        int prompt_len = rand() % 1280;
        for (int j = 0; j < prompt_len; j++) {
            job->prompt_tokens.push_back(rand() % 128000);
        }
        job->max_steps = rand() % 256;
        context.submit_job(job);
        std::this_thread::sleep_for(std::chrono::milliseconds(10000 + rand() % 10000));
    }

    context.wait_all_jobs_to_complete();
    context.stop_async_processing();

    return 0;
}
