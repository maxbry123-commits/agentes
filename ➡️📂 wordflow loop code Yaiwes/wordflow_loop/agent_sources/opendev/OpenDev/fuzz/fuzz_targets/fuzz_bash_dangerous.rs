//! Fuzz target for bash dangerous command detection.
//!
//! Run with: cargo +nightly fuzz run fuzz_bash_dangerous
//!
//! This target feeds arbitrary strings to the dangerous command
//! detection logic to find panics, hangs, or false negatives.

#![no_main]

use libfuzzer_sys::fuzz_target;

// Note: When the fuzz crate is wired up, this would import the detection
// function directly. For now this is a placeholder structure.
// The actual property-based tests live in the crate test modules
// using proptest (see opendev-tools-impl tests).

fuzz_target!(|data: &str| {
    // Exercise the regex patterns against arbitrary input.
    // The function must never panic regardless of input.
    let dangerous_patterns: &[&str] = &[
        r"rm\s+-rf\s+/",
        r"curl.*\|\s*(ba)?sh",
        r"wget.*\|\s*(ba)?sh",
        r"sudo\s+",
        r"mkfs",
        r"dd\s+.*of=",
        r"chmod\s+-R\s+777\s+/",
        r":\(\)\{.*:\|:&\s*\};:",
        r"mv\s+/",
        r">\s*/dev/sd[a-z]",
    ];
    for pattern in dangerous_patterns {
        if let Ok(re) = regex::Regex::new(pattern) {
            let _ = re.is_match(data);
        }
    }
});
