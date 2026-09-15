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

struct MixedJob {
    double arrival_time;
    int orig_idx;
    JobPriority priority;
    int max_steps;
};

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cout << "Usage: " << argv[0]
                  << " <model_path> <proact_freq> <react_freq> <max_time (s)>" << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    std::string proact_freq_str = argv[2];
    std::string react_freq_str = argv[3];
    double max_time = std::atof(argv[4]);

    ContextOV context(model_path);
    context.set_prefill_gpu_ratio(0.6);
    context.start_async_processing();

    std::string exp_dir = get_exp_dir();
    std::string proact_dir = exp_dir + "/data/mixed/proactive/";
    std::string react_dir = exp_dir + "/data/mixed/reactive/";
    std::string proact_stats_file = proact_dir + "_stats.txt";
    std::string react_stats_file = react_dir + "_stats.txt";
    std::string proact_timing_file =
        exp_dir + "/data/timing/" + proact_freq_str + "_req_per_min.txt";
    std::string react_timing_file = exp_dir + "/data/timing/" + react_freq_str + "_req_per_min.txt";

    std::vector<double> proact_timing = parse_timing(proact_timing_file, max_time);
    std::vector<double> react_timing = parse_timing(react_timing_file, max_time);
    std::vector<int> proact_max_steps = parse_max_steps(proact_stats_file);
    std::vector<int> react_max_steps = parse_max_steps(react_stats_file);
    assert(proact_max_steps.size() >= proact_timing.size() && "The actual jobs are not enough");
    assert(react_max_steps.size() >= react_timing.size() && "The actual jobs are not enough");

    // Merge two workloads
    std::vector<MixedJob> mixed_jobs;
    for (int i = 0; i < proact_timing.size(); i++) {
        mixed_jobs.push_back({proact_timing[i], i, JobPriority::proactive, proact_max_steps[i]});
    }
    for (int i = 0; i < react_timing.size(); i++) {
        mixed_jobs.push_back({react_timing[i], i, JobPriority::reactive, react_max_steps[i]});
    }
    std::sort(mixed_jobs.begin(), mixed_jobs.end(),
              [](const MixedJob& a, const MixedJob& b) { return a.arrival_time < b.arrival_time; });

    // start async loop
    double skew = 0;
    for (int i = 0; i < mixed_jobs.size(); i++) {
        double interval = std::max(0.0, mixed_jobs[i].arrival_time -
                                            (i == 0 ? 0 : mixed_jobs[i - 1].arrival_time) - skew);
        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval * 1000)));
        auto job_begin = get_time();
        int orig_idx = mixed_jobs[i].orig_idx;
        std::string job_uuid;
        if (mixed_jobs[i].priority == JobPriority::proactive) {
            job_uuid = "proactive_" + std::to_string(orig_idx);
        } else {
            job_uuid = "reactive_" + std::to_string(orig_idx);
        }
        InferJob job = create_infer_job(job_uuid, mixed_jobs[i].priority);
        if (mixed_jobs[i].priority == JobPriority::proactive) {
            parse_prompt(job, proact_dir + std::to_string(orig_idx) + "_tokens.txt");
        } else {
            parse_prompt(job, react_dir + std::to_string(orig_idx) + "_tokens.txt");
        }
        job->max_steps = mixed_jobs[i].max_steps;
        job->temperature = 0;
        job->on_complete = [](InferJob job) { print_stats(job); };

        context.submit_job(job);
        skew = elapsed_time(job_begin);
    }
    context.wait_all_jobs_to_complete();
    context.stop_async_processing();

    return 0;
}