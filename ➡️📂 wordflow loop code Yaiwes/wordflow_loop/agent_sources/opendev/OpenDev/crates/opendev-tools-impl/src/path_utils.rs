//! Shared path resolution utilities for tool implementations.
//!
//! Path resolution functions (`expand_home`, `strip_curdir`, `normalize_path`,
//! `resolve_file_path`, `resolve_dir_path`) are defined in `opendev-tools-core::path`
//! and re-exported here for backward compatibility. This module additionally provides
//! `is_external_path` (for external directory approval) and `is_sensitive_file`
//! (credential/key detection) as tool-level concerns.

use std::path::Path;

pub use opendev_tools_core::path::{
    expand_home, is_external_path, normalize_path, resolve_dir_path, resolve_file_path,
    strip_curdir,
};

/// Check if a file is likely to contain sensitive data (secrets, credentials, keys).
///
/// Matches patterns from `.gitignore` for Node.js (`.env` family) plus
/// common credential/key files. Returns a human-readable reason if sensitive.
pub fn is_sensitive_file(path: &Path) -> Option<&'static str> {
    let name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("")
        .to_lowercase();

    // .env files (matches .env, .env.local, .env.production, etc.)
    // but NOT .env.example or .env.sample
    if name == ".env"
        || (name.starts_with(".env.") && !name.ends_with(".example") && !name.ends_with(".sample"))
    {
        return Some("environment file (may contain secrets)");
    }

    // Private keys
    if name.ends_with(".pem")
        || name.ends_with(".key")
        || name == "id_rsa"
        || name == "id_ed25519"
        || name == "id_ecdsa"
    {
        return Some("private key file");
    }

    // Known credential files
    let credential_names = [
        "credentials",
        "credentials.json",
        "credentials.yaml",
        "credentials.yml",
        "service-account.json",
        ".npmrc",
        ".pypirc",
        ".netrc",
        ".htpasswd",
    ];
    if credential_names.contains(&name.as_str()) {
        return Some("credentials file");
    }

    // Token/secret files
    if name.contains("secret")
        && (name.ends_with(".json") || name.ends_with(".yaml") || name.ends_with(".yml"))
    {
        return Some("secrets file");
    }

    None
}

#[cfg(test)]
#[path = "path_utils_tests.rs"]
mod tests;
