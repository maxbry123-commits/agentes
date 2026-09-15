#include "logging.h"

#include <iostream>
static const char* log_level_to_string(log_level level) {
    switch (level) {
        case log_level::DEBUG:
            return "DEBUG";
        case log_level::INFO:
            return "INFO";
        case log_level::WARN:
            return "WARN";
        case log_level::ERROR:
            return "ERROR";
        default:
            return "UNKNOWN";
    }
}

static const char* get_color_code(log_level level) {
    switch (level) {
        case log_level::DEBUG:
            return "\033[36m"; // Cyan
        case log_level::INFO:
            return "\033[32m"; // Green
        case log_level::WARN:
            return "\033[33m"; // Yellow
        case log_level::ERROR:
            return "\033[31m"; // Red
        default:
            return "\033[0m"; // Reset
    }
}

void logging::__log(log_level level, std::string message) {
    const char* color_code = get_color_code(level);
    const char* level_str = log_level_to_string(level);
    std::cout << color_code << "[" << level_str << "] " << message << "\033[0m" << std::endl;
}
