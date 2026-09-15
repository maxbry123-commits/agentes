#include "util.h"

int64_t elapsed_time_us(std::chrono::steady_clock::time_point start) {
  auto end = std::chrono::steady_clock::now();
  return std::chrono::duration_cast<std::chrono::microseconds>(end - start)
      .count();
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