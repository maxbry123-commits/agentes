//! Config template substitution.
//!
//! Resolves `{env:VAR}` and `{file:path}` tokens in config text
//! before JSON parsing.

use std::path::Path;

use tracing::debug;

use super::ConfigLoader;

impl ConfigLoader {
    /// Substitute `{env:VAR}` and `{file:path}` templates in config text.
    ///
    /// This runs before JSON parsing, replacing template tokens with their
    /// resolved values. Follows the same pattern as OpenCode's `substitute()`.
    pub(super) fn substitute_templates(text: &str, config_dir: &Path) -> String {
        let mut result = text.to_string();

        // Process {env:VAR_NAME} tokens
        while let Some(start) = result.find("{env:") {
            let rest = &result[start + 5..];
            if let Some(end) = rest.find('}') {
                let var_name = &rest[..end];
                let replacement = std::env::var(var_name).unwrap_or_else(|_| {
                    debug!(
                        "Config template {{env:{var_name}}}: variable not set, using empty string"
                    );
                    String::new()
                });
                result.replace_range(start..start + 5 + end + 1, &replacement);
            } else {
                break; // Malformed token, stop processing
            }
        }

        // Process {file:path} tokens
        while let Some(start) = result.find("{file:") {
            let rest = &result[start + 6..];
            if let Some(end) = rest.find('}') {
                let file_path = rest[..end].trim();

                let resolved = if file_path.starts_with("~/") {
                    dirs::home_dir()
                        .map(|h| h.join(&file_path[2..]))
                        .unwrap_or_else(|| std::path::PathBuf::from(file_path))
                } else if Path::new(file_path).is_absolute() {
                    std::path::PathBuf::from(file_path)
                } else {
                    config_dir.join(file_path)
                };

                let replacement = match std::fs::read_to_string(&resolved) {
                    Ok(content) => {
                        let trimmed = content.trim();
                        // JSON-escape the content since it's inside a JSON string
                        serde_json::to_string(trimmed)
                            .map(|s| s[1..s.len() - 1].to_string())
                            .unwrap_or_else(|_| trimmed.to_string())
                    }
                    Err(e) => {
                        debug!(
                            "Config template {{file:{file_path}}}: could not read {}: {e}",
                            resolved.display()
                        );
                        String::new()
                    }
                };

                result.replace_range(start..start + 6 + end + 1, &replacement);
            } else {
                break;
            }
        }

        result
    }
}
