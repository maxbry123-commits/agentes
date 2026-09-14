#include "basic/dtype.h"
#include "end2end/infer-job.h"
#include "end2end/ov/context.h"
#include "util-exp.h"
#include "utils/utils.h"

#include <cassert>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>

using namespace hllm;

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cout << "Usage: " << argv[0] << " <model_path> <benchmark_name> <freq> <max_time (s)>"
                  << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    std::string benchmark_name = argv[2];
    std::string freq_str = argv[3];
    double max_time = std::atof(argv[4]);

    ContextOV context(model_path);
    context.set_prefill_gpu_ratio(0.1);
    context.start_async_processing();

    std::string exp_dir = get_exp_dir();
    std::string benchmark_dir = exp_dir + "/data/proactive/" + benchmark_name + "/";
    std::string benchmark_stats_file = benchmark_dir + "_stats.txt";
    std::string timing_file = exp_dir + "/data/timing/" + freq_str + "_req_per_min.txt";

    std::vector<double> timing = parse_timing(timing_file, max_time);
    std::vector<int> max_steps = parse_max_steps(benchmark_stats_file);
    assert(max_steps.size() >= timing.size() && "The actual jobs are not enough");

    double skew = 0;
    for (int i = 0; i < timing.size(); i++) {
        double interval = std::max(0.0, timing[i] - (i == 0 ? 0 : timing[i - 1]) - skew);
        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval * 1000)));
        auto job_begin = get_time();
        InferJob job = create_infer_job("proactive_" + std::to_string(i), JobPriority::proactive);
        parse_prompt(job, benchmark_dir + std::to_string(i) + "_tokens.txt");
        job->max_steps = max_steps[i];
        job->temperature = 0;
        job->on_complete = [](InferJob job) { print_stats(job); };

        context.submit_job(job);
        skew = elapsed_time(job_begin);
    }
    context.wait_all_jobs_to_complete();
    context.stop_async_processing();

    return 0;
}
