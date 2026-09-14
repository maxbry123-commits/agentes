#include "memory-block.h"

MemoryBlock::MemoryBlock() : data_(nullptr), size_(0) {}

MemoryBlock::MemoryBlock(char const* data, size_t size) : data_(new char[size]), size_(size) {
    memcpy(data_, data, size);
}

MemoryBlock::MemoryBlock(size_t size, bool initialize_zero) : data_(new char[size]), size_(size) {
    if (initialize_zero) {
        memset(data_, 0, size);
    }
}

MemoryBlock::MemoryBlock(MemoryBlock&& other) noexcept : data_(other.data_), size_(other.size_) {
    other.data_ = nullptr;
    other.size_ = 0;
}

MemoryBlock& MemoryBlock::operator=(MemoryBlock&& other) noexcept {
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

char* MemoryBlock::get_ptr() const { return data_; }

char* MemoryBlock::get_ptr() { return data_; }

size_t MemoryBlock::get_size() const { return size_; }