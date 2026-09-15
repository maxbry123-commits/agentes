//! 9-pass fuzzy matching strategies, from strictest to most flexible.
//!
//! Each pass function takes `(original, old_content)` and returns `Some(actual)`
//! if it finds a match in the original text.

use regex::Regex;
use std::sync::LazyLock;

// ---------------------------------------------------------------------------
// Pass 1: Simple (exact match)
// ---------------------------------------------------------------------------

pub(super) fn simple_find(original: &str, old_content: &str) -> Option<String> {
    if original.contains(old_content) {
        Some(old_content.to_string())
    } else {
        None
    }
}

// ---------------------------------------------------------------------------
// Pass 2: LineTrimmed — trim each line before comparing
// ---------------------------------------------------------------------------

pub(super) fn line_trimmed_find(original: &str, old_content: &str) -> Option<String> {
    let old_lines: Vec<&str> = old_content.split('\n').collect();
    let old_trimmed: Vec<&str> = old_lines.iter().map(|l| l.trim()).collect();

    if old_trimmed.is_empty() || old_trimmed.iter().all(|l| l.is_empty()) {
        return None;
    }

    let original_lines: Vec<&str> = original.split('\n').collect();

    for i in 0..original_lines.len() {
        if original_lines[i].trim() != old_trimmed[0] {
            continue;
        }
        if i + old_trimmed.len() > original_lines.len() {
            continue;
        }
        let all_match = old_trimmed
            .iter()
            .enumerate()
            .all(|(j, old_ln)| original_lines[i + j].trim() == *old_ln);
        if all_match {
            let actual = original_lines[i..i + old_trimmed.len()].join("\n");
            if original.contains(&actual) {
                return Some(actual);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Pass 3: BlockAnchor — first/last lines anchor, middle uses similarity
// ---------------------------------------------------------------------------

pub(super) fn block_anchor_find(original: &str, old_content: &str) -> Option<String> {
    let old_lines: Vec<&str> = old_content.split('\n').collect();
    if old_lines.len() < 3 {
        return None;
    }

    let first_trimmed = old_lines[0].trim();
    let last_trimmed = old_lines[old_lines.len() - 1].trim();
    let middle_old: Vec<&str> = old_lines[1..old_lines.len() - 1]
        .iter()
        .map(|l| l.trim())
        .collect();

    let original_lines: Vec<&str> = original.split('\n').collect();
    let mut candidates: Vec<(usize, usize, f64)> = Vec::new(); // (start, end_inclusive, similarity)

    for i in 0..original_lines.len() {
        if original_lines[i].trim() != first_trimmed {
            continue;
        }
        let window_end = (i + old_lines.len() * 2).min(original_lines.len());
        for end_idx in (i + old_lines.len() - 1)..window_end {
            if end_idx >= original_lines.len() {
                break;
            }
            if original_lines[end_idx].trim() != last_trimmed {
                continue;
            }
            let middle_orig: Vec<&str> = original_lines[i + 1..end_idx]
                .iter()
                .map(|l| l.trim())
                .collect();

            let sim = if middle_old.is_empty() && middle_orig.is_empty() {
                1.0
            } else if middle_old.is_empty() || middle_orig.is_empty() {
                continue;
            } else {
                similarity(&middle_old.join("\n"), &middle_orig.join("\n"))
            };
            candidates.push((i, end_idx, sim));
        }
    }

    if candidates.is_empty() {
        return None;
    }

    let threshold = if candidates.len() == 1 { 0.0 } else { 0.3 };
    let best = candidates
        .iter()
        .max_by(|a, b| a.2.partial_cmp(&b.2).unwrap())?;
    if best.2 < threshold {
        return None;
    }

    let actual = original_lines[best.0..=best.1].join("\n");
    if original.contains(&actual) {
        Some(actual)
    } else {
        None
    }
}

// ---------------------------------------------------------------------------
// Pass 4: WhitespaceNormalized — collapse whitespace runs
// ---------------------------------------------------------------------------

static WS_RE: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\s+").unwrap());

fn ws_normalize(s: &str) -> String {
    s.split('\n')
        .map(|ln| WS_RE.replace_all(ln, " ").trim().to_string())
        .collect::<Vec<_>>()
        .join("\n")
}

pub(super) fn whitespace_normalized_find(original: &str, old_content: &str) -> Option<String> {
    let norm_old = ws_normalize(old_content);
    let original_lines: Vec<&str> = original.split('\n').collect();
    let old_line_count = old_content.split('\n').count();

    for i in 0..original_lines.len() {
        let end_max = (i + old_line_count + 2).min(original_lines.len());
        for j in (i + old_line_count.saturating_sub(1))..=end_max {
            if j > original_lines.len() {
                break;
            }
            let candidate = original_lines[i..j].join("\n");
            if ws_normalize(&candidate) == norm_old && original.contains(&candidate) {
                return Some(candidate);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Pass 5: IndentationFlexible — ignore indentation entirely
// ---------------------------------------------------------------------------

pub(super) fn indentation_flexible_find(original: &str, old_content: &str) -> Option<String> {
    let old_stripped: Vec<&str> = old_content
        .split('\n')
        .map(|l| l.trim())
        .filter(|l| !l.is_empty())
        .collect();

    if old_stripped.is_empty() {
        return None;
    }

    let original_lines: Vec<&str> = original.split('\n').collect();

    for i in 0..original_lines.len() {
        if original_lines[i].trim() != old_stripped[0] {
            continue;
        }
        let mut matched_indices: Vec<usize> = Vec::new();
        let mut j = 0;
        let search_end = (i + old_stripped.len() * 3).min(original_lines.len());
        for (k, orig_line) in original_lines[i..search_end].iter().enumerate() {
            let k = k + i;
            if j >= old_stripped.len() {
                break;
            }
            if orig_line.trim().is_empty() {
                continue; // skip blank lines
            }
            if orig_line.trim() == old_stripped[j] {
                matched_indices.push(k);
                j += 1;
            } else {
                break;
            }
        }

        if j == old_stripped.len() && !matched_indices.is_empty() {
            let start = matched_indices[0];
            let end = matched_indices[matched_indices.len() - 1] + 1;
            let actual = original_lines[start..end].join("\n");
            if original.contains(&actual) {
                return Some(actual);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Pass 6: EscapeNormalized — unescape common escape sequences
// ---------------------------------------------------------------------------

fn unescape(s: &str) -> String {
    s.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\\\", "\\")
        .replace("\\\"", "\"")
        .replace("\\'", "'")
}

pub(super) fn escape_normalized_find(original: &str, old_content: &str) -> Option<String> {
    let unescaped = unescape(old_content);
    if unescaped == old_content {
        return None; // no escapes to normalize
    }
    if original.contains(&unescaped) {
        Some(unescaped)
    } else {
        None
    }
}

// ---------------------------------------------------------------------------
// Pass 7: TrimmedBoundary — trim first/last lines, expand to full lines
// ---------------------------------------------------------------------------

pub(super) fn trimmed_boundary_find(original: &str, old_content: &str) -> Option<String> {
    let trimmed = old_content.trim();
    if trimmed == old_content {
        return None; // nothing to trim
    }

    if original.contains(trimmed) {
        return Some(trimmed.to_string());
    }

    // Try line-level boundary expansion
    let old_lines: Vec<&str> = old_content.split('\n').collect();
    let first_content = old_lines[0].trim();
    let last_content = old_lines[old_lines.len() - 1].trim();

    if first_content.is_empty() || last_content.is_empty() {
        return None;
    }

    let original_lines: Vec<&str> = original.split('\n').collect();
    for i in 0..original_lines.len() {
        if !original_lines[i].contains(first_content) {
            continue;
        }
        let end = (i + old_lines.len() + 2).min(original_lines.len());
        for j in (i + 1)..end {
            if j >= original_lines.len() {
                break;
            }
            if !original_lines[j].contains(last_content) {
                continue;
            }
            let candidate = original_lines[i..=j].join("\n");
            if original.contains(&candidate) {
                return Some(candidate);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Pass 8: ContextAware — use surrounding context to locate position
// ---------------------------------------------------------------------------

pub(super) fn context_aware_find(original: &str, old_content: &str) -> Option<String> {
    let old_lines: Vec<&str> = old_content.split('\n').collect();
    if old_lines.len() < 2 {
        return None;
    }

    let original_lines: Vec<&str> = original.split('\n').collect();

    let first_ctx = old_lines
        .iter()
        .find(|l| !l.trim().is_empty())
        .map(|l| l.trim())?;
    let last_ctx = old_lines
        .iter()
        .rev()
        .find(|l| !l.trim().is_empty())
        .map(|l| l.trim())?;

    // Find all positions of first anchor
    let starts: Vec<usize> = original_lines
        .iter()
        .enumerate()
        .filter(|(_, l)| l.trim().contains(first_ctx))
        .map(|(i, _)| i)
        .collect();

    if starts.is_empty() {
        return None;
    }

    let mut best_match: Option<String> = None;
    let mut best_sim: f64 = 0.0;

    for start in starts {
        let search_end = (start + old_lines.len() * 2).min(original_lines.len());
        for end in (start + 1)..search_end {
            if original_lines[end].trim().contains(last_ctx) {
                let candidate = original_lines[start..=end].join("\n");
                let sim = similarity(old_content.trim(), candidate.trim());
                if sim > best_sim && sim > 0.5 {
                    best_sim = sim;
                    best_match = Some(candidate);
                }
                break; // only check first end anchor per start
            }
        }
    }

    match best_match {
        Some(ref m) if original.contains(m) => best_match,
        _ => None,
    }
}

// ---------------------------------------------------------------------------
// Pass 9: MultiOccurrence — trimmed line-by-line match as last resort
// ---------------------------------------------------------------------------

pub(super) fn multi_occurrence_find(original: &str, old_content: &str) -> Option<String> {
    let trimmed = old_content.trim();
    if trimmed.is_empty() {
        return None;
    }

    let original_lines: Vec<&str> = original.split('\n').collect();
    let trimmed_lines: Vec<&str> = trimmed.split('\n').collect();

    if trimmed_lines.len() > original_lines.len() {
        return None;
    }

    for i in 0..=(original_lines.len() - trimmed_lines.len()) {
        let candidate_lines = &original_lines[i..i + trimmed_lines.len()];
        let all_match = candidate_lines
            .iter()
            .zip(trimmed_lines.iter())
            .all(|(a, b)| a.trim() == b.trim());
        if all_match {
            let candidate = candidate_lines.join("\n");
            if original.contains(&candidate) {
                return Some(candidate);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Similarity helper (SequenceMatcher-like)
// ---------------------------------------------------------------------------

/// Compute a similarity ratio between two strings (0.0 to 1.0).
/// Uses a simple longest-common-subsequence approach similar to Python's
/// `difflib.SequenceMatcher.ratio()`.
pub(super) fn similarity(a: &str, b: &str) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 1.0;
    }
    if a.is_empty() || b.is_empty() {
        return 0.0;
    }

    let a_bytes = a.as_bytes();
    let b_bytes = b.as_bytes();
    let lcs_len = lcs_length(a_bytes, b_bytes);
    (2.0 * lcs_len as f64) / (a_bytes.len() + b_bytes.len()) as f64
}

/// Length of the longest common subsequence (space-optimized).
fn lcs_length(a: &[u8], b: &[u8]) -> usize {
    let m = a.len();
    let n = b.len();
    let mut prev = vec![0usize; n + 1];
    let mut curr = vec![0usize; n + 1];

    for i in 1..=m {
        for j in 1..=n {
            if a[i - 1] == b[j - 1] {
                curr[j] = prev[j - 1] + 1;
            } else {
                curr[j] = curr[j - 1].max(prev[j]);
            }
        }
        std::mem::swap(&mut prev, &mut curr);
        curr.iter_mut().for_each(|v| *v = 0);
    }
    *prev.iter().max().unwrap_or(&0)
}
