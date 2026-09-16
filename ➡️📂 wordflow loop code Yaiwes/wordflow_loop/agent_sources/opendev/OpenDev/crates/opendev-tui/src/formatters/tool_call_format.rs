//! Tool call display formatting functions.
//!
//! Converts tool names and argument maps into human-readable display strings.

use std::collections::HashMap;

use ratatui::style::Color;

use super::path_shortener::PathShortener;
use super::tool_entries::lookup_tool;

/// Extract a meaningful argument summary from args using the given keys.
fn extract_arg_from_keys(
    keys: &[&str],
    args: &HashMap<String, serde_json::Value>,
) -> Option<String> {
    if args.is_empty() {
        return None;
    }

    for key in keys {
        if let Some(val) = args.get(*key)
            && let Some(s) = val.as_str()
        {
            return Some(s.replace('\n', " "));
        }
    }

    None
}

/// Format a tool call with arguments for display.
///
/// Returns a string like `Read /path/to/file.rs` or `Bash ls -la`.
pub fn format_tool_call_display(
    tool_name: &str,
    args: &HashMap<String, serde_json::Value>,
) -> String {
    let (verb, arg) = format_tool_call_parts(tool_name, args);
    if arg.is_empty() {
        verb
    } else {
        format!("{verb} {arg}")
    }
}

/// Format a tool call into separate verb and arg parts.
///
/// Returns `(verb, arg_summary)` — e.g. `("Read", "src/main.rs")` or `("Bash", "ls -la")`.
/// Uses a default `PathShortener` (home dir only, no working dir).
pub fn format_tool_call_parts(
    tool_name: &str,
    args: &HashMap<String, serde_json::Value>,
) -> (String, String) {
    let shortener = PathShortener::default();
    format_tool_call_parts_short(tool_name, args, &shortener)
}

/// Format a tool call into separate verb and arg parts, with optional working directory
/// for displaying relative paths. Convenience wrapper that constructs a temporary
/// `PathShortener` — prefer `format_tool_call_parts_short` with a cached shortener.
pub fn format_tool_call_parts_with_wd(
    tool_name: &str,
    args: &HashMap<String, serde_json::Value>,
    working_dir: Option<&str>,
) -> (String, String) {
    let shortener = PathShortener::new(working_dir);
    format_tool_call_parts_short(tool_name, args, &shortener)
}

/// Format a tool call into separate verb and arg parts using a cached `PathShortener`.
///
/// This is the preferred entry point — avoids repeated `dirs::home_dir()` syscalls.
pub fn format_tool_call_parts_short(
    tool_name: &str,
    args: &HashMap<String, serde_json::Value>,
    shortener: &PathShortener,
) -> (String, String) {
    let (verb, arg) = format_parts_inner(tool_name, args, shortener);
    let shortened = shortener.shorten_text(&arg);
    let truncated = if shortened.len() > 80 {
        format!("{}...", &shortened[..shortened.floor_char_boundary(77)])
    } else {
        shortened
    };
    (verb, truncated)
}

/// Inner implementation of tool call formatting (before universal path replacement).
fn format_parts_inner(
    tool_name: &str,
    args: &HashMap<String, serde_json::Value>,
    shortener: &PathShortener,
) -> (String, String) {
    let entry = lookup_tool(tool_name);

    // Special case: spawn_subagent shows "AgentType(task_summary)" instead of "Spawn(subagent)"
    if matches!(tool_name, "Agent" | "spawn_subagent") {
        let verb = args
            .get("agent_type")
            .and_then(|v| v.as_str())
            .map(|s| {
                // Prettify agent_type names for display
                match s {
                    "Explore" | "Code-Explorer" | "code_explorer" => "Explore".to_string(),
                    "Planner" | "planner" => "Plan".to_string(),
                    "ask-user" | "ask_user" => "AskUser".to_string(),
                    other => other.to_string(),
                }
            })
            .unwrap_or_else(|| "Agent".to_string());
        let task = extract_arg_from_keys(&["description", "task"], args)
            .unwrap_or_else(|| "working...".to_string());
        return (verb, task);
    }

    // Special case: past_sessions shows action-specific verbs
    if tool_name == "past_sessions" {
        let action = args
            .get("action")
            .and_then(|v| v.as_str())
            .unwrap_or("list");
        return match action {
            "list" => ("List Sessions".to_string(), String::new()),
            "read" => {
                let id = args
                    .get("session_id")
                    .and_then(|v| v.as_str())
                    .unwrap_or("...");
                ("Read Session".to_string(), id.to_string())
            }
            "search" => {
                let q = args.get("query").and_then(|v| v.as_str()).unwrap_or("...");
                ("Search Sessions".to_string(), format!("\"{q}\""))
            }
            "info" => {
                let id = args
                    .get("session_id")
                    .and_then(|v| v.as_str())
                    .unwrap_or("...");
                ("Session Info".to_string(), id.to_string())
            }
            other => ("Sessions".to_string(), other.to_string()),
        };
    }

    // Special case: grep tools show "pattern" in path
    if matches!(tool_name, "grep" | "search" | "Grep") {
        let pattern = args
            .get("pattern")
            .or_else(|| args.get("query"))
            .and_then(|v| v.as_str())
            .unwrap_or("...");
        let pattern_display = if pattern.len() > 40 {
            format!("\"{}...\"", &pattern[..pattern.floor_char_boundary(37)])
        } else {
            format!("\"{pattern}\"")
        };
        if let Some(path) = args.get("path").and_then(|v| v.as_str()) {
            let rel = shortener.shorten(path);
            return ("Grep".to_string(), format!("{pattern_display} in {rel}"));
        }
        return ("Grep".to_string(), pattern_display);
    }

    // Special case: ast_grep tools show "pattern" [lang]
    if matches!(tool_name, "ast_grep" | "AstGrep") {
        let pattern = args
            .get("pattern")
            .and_then(|v| v.as_str())
            .unwrap_or("...");
        let pattern_display = if pattern.len() > 40 {
            format!("\"{}...\"", &pattern[..pattern.floor_char_boundary(37)])
        } else {
            format!("\"{pattern}\"")
        };
        if let Some(lang) = args.get("lang").and_then(|v| v.as_str()) {
            return (
                "AST-Grep".to_string(),
                format!("{pattern_display} [{lang}]"),
            );
        }
        return ("AST-Grep".to_string(), pattern_display);
    }

    // Special case: list_files/Glob shows pattern, optionally with path
    if matches!(tool_name, "list_files" | "Glob") {
        let pattern = args.get("pattern").and_then(|v| v.as_str()).unwrap_or("*");
        let pattern_display = if pattern.len() > 40 {
            format!("{}...", &pattern[..pattern.floor_char_boundary(37)])
        } else {
            pattern.to_string()
        };
        if let Some(path) = args.get("path").and_then(|v| v.as_str())
            && path != "."
            && !path.is_empty()
        {
            let rel = shortener.shorten(path);
            return ("List".to_string(), format!("{pattern_display} in {rel}"));
        }
        return ("List".to_string(), pattern_display);
    }

    // Unknown tools: derive pretty display name from tool_name itself
    // e.g. "some_fancy_tool" → "Some Fancy Tool", "git" → "Git"
    // Must be before generic arg extraction so we use the pretty name, not "Call"
    if entry.verb == "Call" {
        let pretty_name = tool_name
            .replace('_', " ")
            .split_whitespace()
            .map(|w| {
                let mut c = w.chars();
                match c.next() {
                    Some(ch) => format!("{}{}", ch.to_uppercase(), c.as_str()),
                    None => String::new(),
                }
            })
            .collect::<Vec<_>>()
            .join(" ");

        if let Some(arg) = extract_arg_from_keys(entry.primary_arg_keys, args) {
            return (pretty_name, arg);
        }

        return (pretty_name, String::new());
    }

    // Try to extract a meaningful summary from args
    if let Some(summary) = extract_arg_from_keys(entry.primary_arg_keys, args) {
        // Strip working dir prefix from file path args
        let is_path_arg = entry
            .primary_arg_keys
            .first()
            .is_some_and(|k| *k == "file_path" || *k == "path");
        let summary = if is_path_arg {
            shortener.shorten(&summary)
        } else {
            summary
        };
        return (entry.verb.to_string(), summary);
    }

    // MCP tool: show server/tool format
    if tool_name.starts_with("mcp__") {
        let parts: Vec<&str> = tool_name.splitn(3, "__").collect();
        if parts.len() == 3 {
            return ("MCP".to_string(), format!("{}/{}", parts[1], parts[2]));
        }
    }

    // Known tool with no arg extracted: verb(label)
    (entry.verb.to_string(), entry.label.to_string())
}

/// Green gradient colors for nested tool spinner animation.
pub const GREEN_GRADIENT: &[Color] = &[
    Color::Rgb(0, 200, 80),
    Color::Rgb(0, 220, 100),
    Color::Rgb(0, 240, 120),
    Color::Rgb(0, 255, 140),
    Color::Rgb(0, 240, 120),
    Color::Rgb(0, 220, 100),
];
