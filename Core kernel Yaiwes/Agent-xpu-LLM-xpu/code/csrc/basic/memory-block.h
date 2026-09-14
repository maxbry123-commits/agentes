#pragma once

#include <cstring>

/**
 * @brief This manages a block of memory as a unique pointer.
 */
class MemoryBlock {
    char* data_;
    size_t size_;

  public:
    MemoryBlock();

    MemoryBlock(char const* data, size_t size);

    explicit MemoryBlock(size_t size, bool initialize_zero = false);

    MemoryBlock(const MemoryBlock&) = delete;
    MemoryBlock& operator=(const MemoryBlock&) = delete;

    MemoryBlock(MemoryBlock&& other) noexcept;

    MemoryBlock& operator=(MemoryBlock&& other) noexcept;

    ~MemoryBlock();

    /**
     * @warning The caller should never delete the data
     */
    char* get_ptr() const;
    char* get_ptr();
    size_t get_size() const;
};