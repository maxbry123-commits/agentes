#include "./utils.h"

std::chrono::steady_clock::time_point get_time() { return std::chrono::steady_clock::now(); }

double elapsed_time(std::chrono::steady_clock::time_point start) {
    auto end = std::chrono::steady_clock::now();
    return std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count() / 1000.0;
}

double elapsed_time_ms(std::chrono::steady_clock::time_point start) {
    auto end = std::chrono::steady_clock::now();
    return std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
}

double elapsed_time(std::chrono::steady_clock::time_point start,
                    std::chrono::steady_clock::time_point end) {
    return std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count() / 1000.0;
}

double elapsed_time_ms(std::chrono::steady_clock::time_point start,
                       std::chrono::steady_clock::time_point end) {
    return std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
}

uint16_t fp32_to_fp16(float value) {
    union {
        float f;
        uint32_t i;
    } u;
    u.f = value;

    uint32_t sign = (u.i >> 31) & 0x1;
    uint32_t exp = (u.i >> 23) & 0xFF;
    uint32_t mant = u.i & 0x7FFFFF;

    // Handle special cases
    if (exp == 0xFF) { // Infinity or NaN
        if (mant == 0) {
            // Infinity
            return (sign << 15) | 0x7C00;
        } else {
            // NaN - preserve sign and set mantissa to non-zero
            return (sign << 15) | 0x7C00 | (mant ? (mant >> 13) | 0x200 : 0x200);
        }
    }

    if (exp == 0 && mant == 0) { // Zero
        return (sign << 15);
    }

    // Convert exponent from fp32 bias (127) to fp16 bias (15)
    int32_t new_exp = exp - 127 + 15;

    // Handle overflow
    if (new_exp >= 31) {
        return (sign << 15) | 0x7C00; // Infinity
    }

    // Handle underflow
    if (new_exp <= 0) {
        // Subnormal or zero
        if (new_exp < -10) {
            return (sign << 15); // Zero
        }

        // Subnormal number
        mant |= 0x800000; // Add implicit leading 1
        mant >>= (1 - new_exp);
        new_exp = 0;
    }

    // Round to nearest even (banker's rounding)
    uint32_t round_bit = (mant >> 12) & 1;
    uint32_t sticky_bit = (mant & 0xFFF) != 0;
    mant >>= 13;

    if (round_bit && (sticky_bit || (mant & 1))) {
        mant++;
        if (mant > 0x3FF) { // Overflow in mantissa
            mant = 0;
            new_exp++;
            if (new_exp >= 31) {
                return (sign << 15) | 0x7C00; // Infinity
            }
        }
    }

    return (sign << 15) | (new_exp << 10) | mant;
}

float fp16_to_fp32(uint16_t value) {
    uint32_t sign = (value >> 15) & 0x1;
    uint32_t exp = (value >> 10) & 0x1F;
    uint32_t mant = value & 0x3FF;

    union {
        float f;
        uint32_t i;
    } u;

    // Handle special cases
    if (exp == 0x1F) { // Infinity or NaN
        if (mant == 0) {
            // Infinity
            u.i = (sign << 31) | 0x7F800000;
        } else {
            // NaN
            u.i = (sign << 31) | 0x7F800000 | (mant << 13);
        }
        return u.f;
    }

    if (exp == 0) { // Zero or subnormal
        if (mant == 0) {
            // Zero
            u.i = (sign << 31);
            return u.f;
        }

        // Subnormal - normalize
        exp = 1;
        while ((mant & 0x400) == 0) {
            mant <<= 1;
            exp--;
        }
        mant &= 0x3FF; // Remove implicit leading 1
    }

    // Convert exponent from fp16 bias (15) to fp32 bias (127)
    exp = exp - 15 + 127;

    u.i = (sign << 31) | (exp << 23) | (mant << 13);
    return u.f;
}
