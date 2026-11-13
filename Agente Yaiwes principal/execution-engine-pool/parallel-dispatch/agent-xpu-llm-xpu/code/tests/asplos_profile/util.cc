#include "util.h"
#include <thread>
#include <fstream>

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start) {
  auto end = std::chrono::steady_clock::now();
  return std::chrono::duration_cast<std::chrono::microseconds>(end - start)
      .count();
}

void sleep_seconds(int seconds) {
  std::this_thread::sleep_for(std::chrono::seconds(seconds));
}

uint16_t fp32_to_fp16(float value) {
  union {
    float f;
    uint32_t i;
  } u = {value};
  uint32_t bits = u.i;

  uint32_t sign = (bits >> 16) & 0x8000;
  int32_t exp = ((bits >> 23) & 0xff) - 127 + 15;
  uint32_t mantissa = bits & 0x7fffff;

  if (exp <= 0) {
    // Subnormal or zero
    if (exp < -10)
      return sign; // Too small, return zero
    mantissa = (mantissa | 0x800000) >> (1 - exp);
    return sign | (mantissa >> 13);
  } else if (exp >= 31) {
    // Infinity or NaN
    return sign | 0x7c00 | (mantissa ? 0x200 : 0);
  }

  return sign | (exp << 10) | (mantissa >> 13);
}

MemoryBlock::MemoryBlock() : data_(nullptr), size_(0) {}

MemoryBlock::MemoryBlock(char const *data, size_t size)
    : data_(new char[size]), size_(size) {
  memcpy(data_, data, size);
}

MemoryBlock::MemoryBlock(size_t size, bool initialize_zero)
    : data_(new char[size]), size_(size) {
  if (initialize_zero) {
    memset(data_, 0, size);
  }
}

MemoryBlock::MemoryBlock(MemoryBlock &&other) noexcept
    : data_(other.data_), size_(other.size_) {
  other.data_ = nullptr;
  other.size_ = 0;
}

MemoryBlock &MemoryBlock::operator=(MemoryBlock &&other) noexcept {
  if (this != &other) {
    delete[] data_;
    data_ = other.data_;
    size_ = other.size_;
    other.data_ = nullptr;
    other.size_ = 0;
  }
  return *this;
}

MemoryBlock::~MemoryBlock() { delete[] data_; }

char *MemoryBlock::get_ptr() const { return data_; }

char *MemoryBlock::get_ptr() { return data_; }

size_t MemoryBlock::get_size() const { return size_; }

static std::string get_status_string(ov::ProfilingInfo::Status status) {
  switch (status) {
  case ov::ProfilingInfo::Status::NOT_RUN:
    return "NOT_RUN";
  case ov::ProfilingInfo::Status::OPTIMIZED_OUT:
    return "OPTIMIZED_OUT";
  case ov::ProfilingInfo::Status::EXECUTED:
    return "EXECUTED";
  default:
    return "UNKNOWN";
  }
}

void write_kernel_profile_info(ov::InferRequest &infer_request) {
  if (!allow_profile)
    return;

  static std::fstream os("profile.csv", std::ios_base::app);
  std::vector<ov::ProfilingInfo> profiling_info =
      infer_request.get_profiling_info();

  // Get model name and device name from infer_request
  std::string model_name =
      infer_request.get_compiled_model().get_property(ov::model_name);
  auto devices =
      infer_request.get_compiled_model().get_property(ov::execution_devices);
  std::string device_name =
      devices.empty()
          ? "UNKNOWN"
          : std::accumulate(devices.begin(), devices.end(), std::string(),
                            [](const std::string &a, const std::string &b) {
                              return a.empty() ? b : a + "," + b;
                            });
  static bool header_written = false;
  if (!header_written) {
    os << "Model Name,Device Name,Node Name,Status,Real Time (us),CPU Time "
          "(us),Node Type,Execution Type\n";
    header_written = true;
  }
  for (const auto &info : profiling_info) {
    os << model_name << "," << device_name << "," << info.node_name << ","
       << get_status_string(info.status) << "," << info.real_time.count() << ","
       << info.cpu_time.count() << "," << info.node_type << ","
       << info.exec_type << "\n";
  }
  os << "\n";
  os.flush();
}

int64_t get_req_runtime_us(ov::InferRequest &infer_request) {
  if (!allow_profile)
    return 0;

  auto profiling_info = infer_request.get_profiling_info();
  if (profiling_info.empty()) {
    return 0;
  }
  // sum up real_time for all nodes
  int64_t total_time = 0;
  for (const auto &info : profiling_info) {
    total_time += info.real_time.count();
  }
  return total_time;
}