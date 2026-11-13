#pragma once
#include <chrono>
#include <openvino/openvino.hpp>
#include <random>
#include <vector>
#include <cstring>

template <typename T>
std::vector<T> prepare_data(ov::element::Type ov_dtype, size_t size) {
  std::vector<T> input_data(size);
  static std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
  std::uniform_int_distribution<unsigned short> dist_uint16(0, 65535);
  std::uniform_int_distribution<int32_t> dist_int32(-127, 127);
  auto generate_input = [&]() {
    for (int i = 0; i < size; ++i) {
      if (ov_dtype == ov::element::f16 || ov_dtype == ov::element::f32) {
        input_data[i] = dist_fp32(generator);
      } else if (ov_dtype == ov::element::i8) {
        input_data[i] = static_cast<int8_t>(dist_uint16(generator));
      } else if (ov_dtype == ov::element::i32) {
        input_data[i] = dist_int32(generator);
      }
    }
  };
  generate_input();
  return input_data;
}

template <typename T>
void reset_data(std::vector<T> &input_data, ov::element::Type ov_dtype) {
  static std::default_random_engine generator;
  generator.seed(42);
  std::uniform_real_distribution<float> dist_fp32(-1.0, 1.0);
  std::uniform_int_distribution<unsigned short> dist_uint16(0, 65535);
  std::uniform_int_distribution<int32_t> dist_int32(-127, 127);
  auto generate_input = [&]() {
    for (int i = 0; i < input_data.size(); ++i) {
      if (ov_dtype == ov::element::f32 || ov_dtype == ov::element::f16) {
        input_data[i] = dist_fp32(generator);
      } else if (ov_dtype == ov::element::i8) {
        input_data[i] = static_cast<int8_t>(dist_uint16(generator));
      } else if (ov_dtype == ov::element::i32) {
        input_data[i] = dist_int32(generator);
      }
    }
  };
  generate_input();
}

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start);

constexpr bool allow_profile = true;
void write_kernel_profile_info(ov::InferRequest &infer_request);


/**
 * @brief This manages a block of memory as a unique pointer.
 */
class MemoryBlock {
  char *data_;
  size_t size_;

public:
  MemoryBlock();

  MemoryBlock(char const *data, size_t size);

  explicit MemoryBlock(size_t size, bool initialize_zero = false);

  MemoryBlock(const MemoryBlock &) = delete;
  MemoryBlock &operator=(const MemoryBlock &) = delete;

  MemoryBlock(MemoryBlock &&other) noexcept;

  MemoryBlock &operator=(MemoryBlock &&other) noexcept;

  ~MemoryBlock();

  /**
   * @warning The caller should never delete the data
   */
  char *get_ptr() const;
  char *get_ptr();
  size_t get_size() const;
};
