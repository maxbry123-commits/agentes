#pragma once
#include <chrono>

// Helper functions
std::chrono::steady_clock::time_point get_time();

double elapsed_time(std::chrono::steady_clock::time_point start);

double elapsed_time_ms(std::chrono::steady_clock::time_point start);

double elapsed_time(std::chrono::steady_clock::time_point start,
                    std::chrono::steady_clock::time_point end);

double elapsed_time_ms(std::chrono::steady_clock::time_point start,
                       std::chrono::steady_clock::time_point end);

uint16_t fp32_to_fp16(float value);
float fp16_to_fp32(uint16_t value);