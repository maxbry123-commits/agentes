//! Title generation and forking helpers for sessions.

use opendev_models::Role;

/// Generate a short title from the first user message.
///
/// Takes the first 60 characters of the first user message, truncated at the
/// last word boundary so that words are not cut in half.  Returns `None` if
/// there are no user messages or the first user message is empty.
pub fn generate_title_from_messages(messages: &[opendev_models::ChatMessage]) -> Option<String> {
    let first_user = messages.iter().find(|m| m.role == Role::User)?;
    let text = first_user.content.trim();
    if text.is_empty() {
        return None;
    }
    Some(truncate_at_word_boundary(text, 60))
}

/// Generate a title for a forked session by appending `(fork #N)`.
///
/// If the title already ends with `(fork #N)`, the number is incremented.
/// Otherwise, `(fork #1)` is appended.
pub fn get_forked_title(title: &str) -> String {
    // Match trailing " (fork #N)" pattern
    if let Some(caps) = regex::Regex::new(r"^(.+) \(fork #(\d+)\)$")
        .ok()
        .and_then(|re| re.captures(title))
    {
        let base = caps.get(1).map_or("", |m| m.as_str());
        let num: u32 = caps.get(2).map_or(1, |m| m.as_str().parse().unwrap_or(1));
        return format!("{base} (fork #{})", num + 1);
    }
    format!("{title} (fork #1)")
}

/// Truncate a string to at most `max_chars` characters at a word boundary.
///
/// Counts by characters (not bytes) so multibyte input — e.g. a prompt with an
/// em-dash or CJK text — is never sliced mid-codepoint (which would panic).
pub(super) fn truncate_at_word_boundary(text: &str, max_chars: usize) -> String {
    if text.chars().count() <= max_chars {
        return text.to_string();
    }

    // Byte offset of the boundary after `max_chars` characters.
    let cut = text
        .char_indices()
        .nth(max_chars)
        .map_or(text.len(), |(i, _)| i);
    let truncated = &text[..cut];

    // Find the last space at or before the cut (spaces are ASCII → byte-safe).
    if let Some(last_space) = truncated.rfind(' ')
        && last_space > 0
    {
        return format!("{}...", &text[..last_space]);
    }

    // No word boundary found; hard-truncate at the char boundary.
    format!("{truncated}...")
}
