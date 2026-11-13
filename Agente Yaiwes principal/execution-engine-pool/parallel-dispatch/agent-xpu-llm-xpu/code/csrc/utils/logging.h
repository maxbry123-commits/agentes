#ifndef __LOGGING_H__
#define __LOGGING_H__

#include <sstream>
#include <string>
enum class log_level { DEBUG, INFO, WARN, ERROR };

namespace logging {
void __log(log_level level, std::string message);

// Stream-like logger class that supports << operator chaining
class logger_stream {
  private:
    std::ostringstream oss_;
    log_level level_;
    bool should_log_;

  public:
    explicit logger_stream(log_level level, bool should_log = true)
        : level_(level), should_log_(should_log) {}

    // Destructor automatically logs the accumulated message
    ~logger_stream() {
        if (should_log_) {
            __log(level_, oss_.str());
        }
    }

    // Move constructor for efficiency
    logger_stream(logger_stream&& other) noexcept
        : oss_(std::move(other.oss_)), level_(other.level_), should_log_(other.should_log_) {
        other.should_log_ = false; // Prevent double logging
    }

    // Delete copy constructor and assignment to prevent issues
    logger_stream(const logger_stream&) = delete;
    logger_stream& operator=(const logger_stream&) = delete;
    logger_stream& operator=(logger_stream&&) = delete;

    // Template operator<< for any streamable type
    template <typename T> logger_stream&& operator<<(T&& value) && {
        oss_ << std::forward<T>(value);
        return std::move(*this);
    }

    template <typename T> logger_stream& operator<<(T&& value) & {
        oss_ << std::forward<T>(value);
        return *this;
    }
};

// Factory functions that return logger_stream objects
inline logger_stream warn() { return logger_stream(log_level::WARN); }

inline logger_stream info() { return logger_stream(log_level::INFO); }

/**
 * @note Debug Message will be printed only if CMAKE_BUILD_TYPE is set to Debug
 */
inline logger_stream debug() {
#if !DEBUG_MODE
    return logger_stream(log_level::DEBUG, false); // Don't log in release mode
#else
    return logger_stream(log_level::DEBUG, true);
#endif
}

inline logger_stream error() { return logger_stream(log_level::ERROR); }
} // namespace logging

#endif