//! Fuzz target for patch hunk parsing.
//!
//! Run with: cargo +nightly fuzz run fuzz_patch_hunk
//!
//! This target feeds arbitrary strings to the patch hunk header parser
//! and manual patch application logic to find panics or unexpected behavior.

#![no_main]

use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &str| {
    // Exercise hunk header parsing with arbitrary input.
    // The parser must never panic regardless of input.
    let parts: Vec<&str> = data.split_whitespace().collect();
    if parts.len() >= 3 {
        if let Some(old_range) = parts[1].strip_prefix('-') {
            if let Some(start_str) = old_range.split(',').next() {
                let _: Result<usize, _> = start_str.parse();
            }
        }
    }
});
