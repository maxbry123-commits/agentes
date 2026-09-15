#include "basic/device.h"
#include "end2end/ov/backend.h"
#include "end2end/ov/context.h"

#include <cassert>
#include <cstring>
#include <iostream>

void print_usage(const char* bin_name) {
    std::cout << "Usage: " << bin_name << " [options] <model_path>\n"
              << "Options:\n"
              << "  --help           / -h             Print usage\n"
              << "  --prompt <path>  / -i <path>      Path to the prompt file "
                 "(default: "
                 "input.prompt)\n"
              << "  --temp <value>   / -t <value>     Temperature for sampling "
                 "(default: "
                 "0.6)\n"
              << "  --topp <value>   / -p <value>     Top-p value for sampling "
                 "(default: "
                 "0.9)\n"
              << "  --seed <value>   / -s <value>     Random seed (default: -1, random "
                 "device)\n"
              << "  --steps <value>  / -n <value>     Number of steps (default: 256)\n"
              << "  --device <value> / -d <value>     Device to run the model on "
                 "(default: intel-hetero. Can be intel-gpu, intel-hetero (NPU+GPU))\n"
              << "<model_path>: Path to the model file\n";
}

int main(int argc, char* argv[]) {
    // if (freopen("stderr", "w", stderr) == nullptr) {
    //     std::cerr << "Error redirecting stderr" << std::endl;
    //     return 1;
    // }
    const char* model_path = nullptr;
    const char* prompt_path = "input.prompt";
    hllm::InferDevice device = hllm::InferDevice::IntelHetero;
    float temperature = 0.6;
    float top_p = 0.9;
    int rand_seed = -1; // random device
    int steps = 256;

    int i;
    for (i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if ((strcmp(argv[i], "--model") == 0 || strcmp(argv[i], "-m") == 0) &&
                   i + 1 < argc) {
            model_path = argv[++i];
        } else if ((strcmp(argv[i], "--prompt") == 0 || strcmp(argv[i], "-i") == 0) &&
                   i + 1 < argc) {
            prompt_path = argv[++i];
        } else if ((strcmp(argv[i], "--temp") == 0 || strcmp(argv[i], "-t") == 0) && i + 1 < argc) {
            temperature = std::atof(argv[++i]);
        } else if ((strcmp(argv[i], "--topp") == 0 || strcmp(argv[i], "-p") == 0) && i + 1 < argc) {
            top_p = std::atof(argv[++i]);
        } else if ((strcmp(argv[i], "--seed") == 0 || strcmp(argv[i], "-s") == 0) && i + 1 < argc) {
            rand_seed = std::atoi(argv[++i]);
        } else if ((strcmp(argv[i], "--steps") == 0 || strcmp(argv[i], "-n") == 0) &&
                   i + 1 < argc) {
            steps = std::atoi(argv[++i]);
        } else if ((strcmp(argv[i], "--device") == 0 || strcmp(argv[i], "-d") == 0) &&
                   i + 1 < argc) {
            device = hllm::get_infer_device(argv[++i]);
            if (device != hllm::InferDevice::IntelHetero && device != hllm::InferDevice::IntelGPU &&
                device != hllm::InferDevice::IntelNPU) {
                std::cout << "Error: device " << argv[i] << " is not supported in intel inference"
                          << std::endl;
                print_usage(argv[0]);
                return 1;
            }
        } else if (argv[i][0] == '-') {
            print_usage(argv[0]);
            return 1;
        } else {
            // Not an option, should be the model path
            break;
        }
    }

    // Check if the last argument is the model path
    if (i < argc) {
        model_path = argv[i];
    } else {
        std::cout << "Error: Model path is required" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    // Check if there are too many arguments
    if (i + 1 < argc) {
        std::cout << "Error: Too many arguments" << std::endl;
        print_usage(argv[0]);
        return 1;
    }
    assert("Model path is not specified" && model_path != nullptr);

    hllm::ContextOV context(model_path, true);
    ov::Core& ov_core = context.ov_core();
    hllm::check_ov_infer_device(ov_core, device);
    hllm::print_ov_device_info(ov_core, device);
    if (device == hllm::InferDevice::IntelNPU) {
        context.set_prefill_gpu_ratio(0.0);
    } else if (device == hllm::InferDevice::IntelGPU) {
        context.set_prefill_gpu_ratio(1.0);
    } else {
        context.set_prefill_gpu_ratio(0.6);
    }
    context.run_individual_infer(prompt_path, steps, temperature, top_p, rand_seed);

    return 0;
}