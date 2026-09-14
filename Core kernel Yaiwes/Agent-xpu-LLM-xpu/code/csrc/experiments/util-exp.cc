#include "util-exp.h"

#include <cctype>
#include <cstdio>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
bool is_line_comment_or_empty(const std::string& line) {
    for (char ch : line) {
        if (ch == '#') return true;
        if (!std::isspace(static_cast<unsigned char>(ch))) return false;
    }
    return true; // empty or only spaces
}
} // namespace

std::vector<int> parse_max_steps(const std::string& file_path) {
    std::ifstream input(file_path);
    if (!input.is_open()) {
        throw std::runtime_error("Failed to open file: " + file_path);
    }

    std::vector<int> max_steps;
    std::string line;
    while (std::getline(input, line)) {
        if (is_line_comment_or_empty(line)) {
            continue;
        }

        std::istringstream iss(line);
        long long idx_ll = 0;
        long long second_ll = 0;
        long long max_step_ll = 0;

        if (!(iss >> idx_ll >> second_ll >> max_step_ll)) {
            throw std::runtime_error("Malformed line (expected at least 3 integers): " + line);
        }

        (void)idx_ll;    // index is not used for output
        (void)second_ll; // middle value is not used

        // Clamp to int range if necessary
        if (max_step_ll < std::numeric_limits<int>::min() ||
            max_step_ll > std::numeric_limits<int>::max()) {
            throw std::runtime_error("max_step out of int range");
        }

        max_steps.push_back(static_cast<int>(max_step_ll));
    }

    return max_steps;
}

std::vector<double> parse_timing(const std::string& file_path, double max_time) {
    std::ifstream input(file_path);
    if (!input.is_open()) {
        throw std::runtime_error("Failed to open file: " + file_path);
    }

    std::vector<double> timings;
    std::string line;
    while (std::getline(input, line)) {
        if (is_line_comment_or_empty(line)) {
            continue;
        }

        std::istringstream iss(line);
        double value = 0.0;
        if (!(iss >> value)) {
            throw std::runtime_error("Malformed line (expected a floating-point number): " + line);
        }
        if (value > max_time) {
            break;
        }
        timings.push_back(value);
    }

    return timings;
}

void parse_prompt(hllm::InferJob job, std::string prompt_path) {
    std::ifstream file(prompt_path);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + prompt_path);
    }

    std::vector<std::string> all_lines;
    std::string line;
    while (std::getline(file, line)) {
        all_lines.push_back(line);
    }

    if (all_lines.size() != 1) {
        throw std::runtime_error("File must have one line of tokens: " + prompt_path);
    }

    std::istringstream iss(all_lines[0]);
    job->prompt_tokens.clear();
    int token;
    while (iss >> token) {
        job->prompt_tokens.push_back(token);
    }
}

std::string get_exp_dir() {
    const char* _exp_dir = getenv("AGENT_EXP_DIR");
    if (_exp_dir == nullptr) {
        std::cout << "AGENT_EXP_DIR is not set, using default exp dir" << std::endl;
        return std::string(".");
    }
    return _exp_dir;
}