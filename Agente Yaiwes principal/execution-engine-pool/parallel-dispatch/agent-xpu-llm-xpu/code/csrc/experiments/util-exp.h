// Utility helpers
// Note: Keep this header minimal; implementation details live in util.cc

#pragma once

#include "end2end/infer-job.h"

#include <string>
#include <vector>

// Parses a stats file where each non-empty line contains three integers:
//   [index] [prompt_len] [max_step]
// The first integer is the zero-based line index; the last integer is the max_step.
// Returns a vector containing the max_step value for each parsed line in order.
//
// Throws std::runtime_error if the file cannot be opened or a non-empty line
// does not contain at least three integers.
std::vector<int> parse_max_steps(const std::string& file_path);

// Parses a timing file where each non-empty line contains a single floating-point
// number. Returns a vector of the parsed values in the same order as the file.
//
// Throws std::runtime_error if the file cannot be opened or a non-empty line
// cannot be parsed as a floating-point number.
std::vector<double> parse_timing(const std::string& file_path, double max_time);

void parse_prompt(hllm::InferJob job, std::string prompt_path);

std::string get_exp_dir();
