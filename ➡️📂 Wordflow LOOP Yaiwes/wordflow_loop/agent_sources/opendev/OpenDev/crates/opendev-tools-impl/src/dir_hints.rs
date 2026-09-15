//! Directory hint utilities for tool error messages.
//!
//! When a tool references a non-existent directory, these helpers list
//! what directories actually exist so the LLM can self-correct.

use std::path::Path;

use crate::file_search::DEFAULT_SEARCH_EXCLUDES;

/// List user-visible directories in `dir`, excluding common noise directories.
/// Returns a newline-separated string with each directory indented and suffixed with `/`.
pub fn list_available_dirs(dir: &Path) -> String {
    let mut dirs: Vec<String> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().map(|ft| ft.is_dir()).unwrap_or(false))
        .map(|e| e.file_name().to_string_lossy().to_string())
        .filter(|name| !name.starts_with('.') && !DEFAULT_SEARCH_EXCLUDES.contains(&name.as_str()))
        .collect();
    dirs.sort();
    dirs.iter()
        .map(|d| format!("  {d}/"))
        .collect::<Vec<_>>()
        .join("\n")
}
