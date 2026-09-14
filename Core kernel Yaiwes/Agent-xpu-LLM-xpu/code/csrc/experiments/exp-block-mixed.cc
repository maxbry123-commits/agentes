#include "basic/dtype.h"
#include "end2end/infer-job.h"
#include "end2end/ov/context.h"
#include "util-exp.h"
#include "utils/utils.h"

#include <atomic>
#include <cassert>
#include <condition_variable>
#include <cstring>
#include <iostream>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

using namespace hllm;

std::thread async_job_thread;
std::queue<InferJob> job_queue;
std::mutex job_queue_mutex;
std::mutex completion_mutex;
std::condition_variable job_queue_cv;
std::condition_variable completion_cv;
std::atomic<bool> running(true);
std::atomic<int> job_count(0);

struct MixedJob {
    double arrival_time;
    int orig_idx;
    JobPriority priority;
    int max_steps;
};

void async_job_processing(ContextOV& context, InferDevice device) {
    InferJob job;
    while (running.load()) {
        {
            std::unique_lock<std::mutex> lock(job_queue_mutex);
            job_queue_cv.wait(lock, [] { return !job_queue.empty() || !running.load(); });
            if (!running.load()) {
                break;
            }
            job = job_queue.front();
            job_queue.pop();
        }
        context.run_individual_infer(job, device);
        job->elapsed_time = elapsed_time(job->submit_time);
        print_stats(job);
        job->release_memory();
        job.reset();
        job_count.fetch_sub(1);
        completion_cv.notify_one();
    }
}

void submit_job(InferJob job) {
    job->submit_time = get_time();
    job_count.fetch_add(1);
    {
        std::lock_guard<std::mutex> lock(job_queue_mutex);
        job_queue.push(job);
    }
    job_queue_cv.notify_one();
}

void wait_all_jobs_to_complete() {
    std::unique_lock<std::mutex> lock(completion_mutex);
    completion_cv.wait(lock, [] { return job_count.load() == 0; });
    std::cout << "All jobs completed" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc != 6) {
        std::cout << "Usage: " << argv[0]
                  << " <model_path> <device> <proact_freq> <react_freq> <max_time (s)>"
                  << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    std::string device_str = argv[2];
    std::string proact_freq_str = argv[3];
    std::string react_freq_str = argv[4];
    double max_time = std::atof(argv[5]);
    InferDevice device;
    if (device_str == "gpu") {
        device = InferDevice::IntelGPU;
    } else if (device_str == "npu") {
        device = InferDevice::IntelNPU;
    } else {
        std::cout << "Invalid device: " << device_str << std::endl;
        return 1;
    }

    ContextOV context(model_path);

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
    assert(proact_timing.size() <= proact_max_steps.size() && "The actual jobs are not enough");
    assert(react_timing.size() <= react_max_steps.size() && "The actual jobs are not enough");

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
    running.store(true);
    async_job_thread = std::thread(async_job_processing, std::ref(context), device);

    double skew = 0;
    auto begin = get_time();
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
        InferJob job = create_infer_job(job_uuid);
        if (mixed_jobs[i].priority == JobPriority::proactive) {
            parse_prompt(job, proact_dir + std::to_string(orig_idx) + "_tokens.txt");
        } else {
            parse_prompt(job, react_dir + std::to_string(orig_idx) + "_tokens.txt");
        }
        job->max_steps = mixed_jobs[i].max_steps;
        job->temperature = 0;
        job->priority = mixed_jobs[i].priority;

        submit_job(job);
        std::cout << "Submitted job " << i << " (" << mixed_jobs[i].priority << ") at "
                  << elapsed_time(begin) << "s" << std::endl;
        skew = elapsed_time(job_begin);
    }
    wait_all_jobs_to_complete();

    running.store(false);
    job_queue_cv.notify_all();
    async_job_thread.join();
}