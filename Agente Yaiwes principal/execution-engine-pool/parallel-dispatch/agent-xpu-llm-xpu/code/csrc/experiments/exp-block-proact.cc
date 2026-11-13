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
                  << " <model_path> <benchmark_name> <device> <freq> <max_time (s)>" << std::endl;
        return 1;
    }
    const char* model_path = argv[1];
    std::string benchmark_name = argv[2];
    std::string device_str = argv[3];
    std::string freq_str = argv[4];
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
    std::string benchmark_dir = exp_dir + "/data/proactive/" + benchmark_name + "/";
    std::string benchmark_stats_file = benchmark_dir + "_stats.txt";
    std::string timing_file = exp_dir + "/data/timing/" + freq_str + "_req_per_min.txt";

    std::vector<double> timing = parse_timing(timing_file, max_time);
    std::vector<int> max_steps = parse_max_steps(benchmark_stats_file);
    assert(max_steps.size() >= timing.size() && "The actual jobs are not enough");

    // start async loop
    running.store(true);
    async_job_thread = std::thread(async_job_processing, std::ref(context), device);

    double skew = 0;
    auto begin = get_time();
    for (int i = 0; i < timing.size(); i++) {
        double interval = std::max(0.0, timing[i] - (i == 0 ? 0 : timing[i - 1]) - skew);
        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval * 1000)));
        auto job_begin = get_time();
        InferJob job = create_infer_job(std::to_string(i));
        parse_prompt(job, benchmark_dir + std::to_string(i) + "_tokens.txt");
        job->max_steps = max_steps[i];
        job->temperature = 0;
        job->priority = JobPriority::proactive;

        submit_job(job);
        std::cout << "Submitted job " << i << " at " << elapsed_time(begin) << "s" << std::endl;
        skew = elapsed_time(job_begin);
    }
    wait_all_jobs_to_complete();

    running.store(false);
    job_queue_cv.notify_all();
    async_job_thread.join();
}