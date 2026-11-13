#include <iostream>
#include <chrono>
#include <string>
#include <algorithm>
#include <cctype>
#include <random>
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>
#include "../util.h"
#include <vector>

static const size_t DIM = 4096;
static const size_t N_HEADS = 32;
static const size_t HEAD_DIM = DIM / N_HEADS;
static const int NUM_RUNS = 6;

static std::vector<uint16_t> Q_buffer;
static std::vector<uint16_t> K_buffer;
static std::vector<uint16_t> V_buffer;
// output buffer unused

ov::Core core;

void prepare(size_t seq_len) {
    size_t buf_size = seq_len * HEAD_DIM * N_HEADS;
    Q_buffer = prepare_data<uint16_t>(ov::element::f16, buf_size);
    K_buffer = prepare_data<uint16_t>(ov::element::f16, buf_size);
    V_buffer = prepare_data<uint16_t>(ov::element::f16, buf_size);
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3) {
        std::cerr << "Usage: " << argv[0] << " <device> <seq_len>" << std::endl;
        return 1;
    }
    std::string device = argv[1];
    size_t seq_len = std::stoul(argv[argc-1]);
    std::transform(device.begin(), device.end(), device.begin(), ::toupper);
    // 使用半精度
    ov::element::Type dtype = ov::element::f16;

    // build attention model; for NPU use static seq_len shape, otherwise dynamic
    auto build_model = [&](ov::element::Type dtype, bool is_static) {
        ov::PartialShape shape = is_static
            ? ov::PartialShape{N_HEADS, seq_len, HEAD_DIM}
            : ov::PartialShape{N_HEADS, ov::Dimension::dynamic(), HEAD_DIM};
        auto Q = std::make_shared<ov::opset15::Parameter>(dtype, shape);
        auto K = std::make_shared<ov::opset15::Parameter>(dtype,
            shape);
        auto V = std::make_shared<ov::opset15::Parameter>(dtype,
            shape);
        auto sdpa = std::make_shared<ov::opset15::ScaledDotProductAttention>(Q, K, V, false);
        auto res = std::make_shared<ov::opset15::Result>(sdpa);
        return std::make_shared<ov::Model>(ov::ResultVector{res}, ov::ParameterVector{Q,K,V});
    };

    // struct to hold compile/runtime metrics
    struct RunMetrics { int64_t compile_us; int64_t runtime_us; double tops; };

    // run_device compiles and benchmarks, returns metrics
    auto run_device = [&](const std::string &dev) -> RunMetrics {
        // compile
        bool is_static = (dev == "NPU");
        auto model = build_model(dtype, is_static);
        auto t0 = std::chrono::steady_clock::now();
        auto cm = core.compile_model(model, dev, {});
        int64_t compile_us = elapsed_time_us(t0);
        // infer
        auto ir = cm.create_infer_request();
        int64_t total_rt = 0;
        for (int i = 0; i < NUM_RUNS; ++i) {
            if (i == 0) {
                prepare(seq_len);
                ir.set_input_tensor(0, ov::Tensor(dtype, {N_HEADS, seq_len, HEAD_DIM}, Q_buffer.data()));
                ir.set_input_tensor(1, ov::Tensor(dtype, {N_HEADS, seq_len, HEAD_DIM}, K_buffer.data()));
                ir.set_input_tensor(2, ov::Tensor(dtype, {N_HEADS, seq_len, HEAD_DIM}, V_buffer.data()));
            }
            auto t1 = std::chrono::steady_clock::now();
            ir.infer();
            if (i > 0) total_rt += elapsed_time_us(t1);
        }
        int64_t runtime_us = total_rt / (NUM_RUNS - 1);
        size_t ops = 4ULL * seq_len * seq_len * DIM;
        double tops = double(ops) / runtime_us / 1e6;
        return {compile_us, runtime_us, tops};
    };

    // run only specified device (GPU or NPU), other metrics set to -1
    RunMetrics gpu_metrics{-1, -1, -1.0}, npu_metrics{-1, -1, -1.0};
    if (device == "GPU") {
        gpu_metrics = run_device("GPU");
    } else if (device == "NPU") {
        npu_metrics = run_device("NPU");
    } else {
        // default: run both
        gpu_metrics = run_device("GPU");
        npu_metrics = run_device("NPU");
    }

    // compute arithmetic intensity: ops per memory bytes
    size_t ops_total = 4ULL * seq_len * seq_len * DIM;
    double mem_bytes = double((3ULL * N_HEADS * seq_len * HEAD_DIM)) * sizeof(uint16_t);
    double arith_intensity = double(ops_total) / mem_bytes;
    // print expected metrics
    std::cout << "Arithmetic intensity: " << arith_intensity << std::endl;
    std::cout << "GPU compile time (us): " << gpu_metrics.compile_us << std::endl;
    std::cout << "NPU compile time (us): " << npu_metrics.compile_us << std::endl;
    std::cout << "GPU runtime (us): " << gpu_metrics.runtime_us << std::endl;
    std::cout << "NPU runtime (us): " << npu_metrics.runtime_us << std::endl;
    std::cout << "GPU throughput (TOPS): " << gpu_metrics.tops << std::endl;
    std::cout << "NPU throughput (TOPS): " << npu_metrics.tops << std::endl;
    return 0;
}