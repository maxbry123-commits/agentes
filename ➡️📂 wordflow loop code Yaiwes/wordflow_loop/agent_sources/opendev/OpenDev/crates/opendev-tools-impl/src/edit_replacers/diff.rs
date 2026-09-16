//! Unified diff generation (like `diff -u`).

/// Generate a unified diff between two strings (like `diff -u`).
pub fn unified_diff(
    file_path: &str,
    original: &str,
    modified: &str,
    context_lines: usize,
) -> String {
    let old_lines: Vec<&str> = original.split('\n').collect();
    let new_lines: Vec<&str> = modified.split('\n').collect();

    // Simple line-by-line diff using LCS on lines
    let matches = line_lcs(&old_lines, &new_lines);

    let mut old_idx = 0;
    let mut new_idx = 0;
    let mut changes: Vec<DiffLine> = Vec::new();

    for &(om, nm) in &matches {
        // Lines removed from old (before this match)
        while old_idx < om {
            changes.push(DiffLine::Remove(old_lines[old_idx]));
            old_idx += 1;
        }
        // Lines added in new (before this match)
        while new_idx < nm {
            changes.push(DiffLine::Add(new_lines[new_idx]));
            new_idx += 1;
        }
        // Context (matching line)
        changes.push(DiffLine::Context(old_lines[old_idx]));
        old_idx += 1;
        new_idx += 1;
    }
    // Remaining lines
    while old_idx < old_lines.len() {
        changes.push(DiffLine::Remove(old_lines[old_idx]));
        old_idx += 1;
    }
    while new_idx < new_lines.len() {
        changes.push(DiffLine::Add(new_lines[new_idx]));
        new_idx += 1;
    }

    // Group changes into hunks with context
    let change_positions: Vec<usize> = changes
        .iter()
        .enumerate()
        .filter(|(_, c)| !matches!(c, DiffLine::Context(_)))
        .map(|(i, _)| i)
        .collect();

    if change_positions.is_empty() {
        return String::new();
    }

    // Merge nearby changes into hunks
    let mut hunk_ranges: Vec<(usize, usize)> = Vec::new();
    let mut start = change_positions[0].saturating_sub(context_lines);
    let mut end = (change_positions[0] + context_lines + 1).min(changes.len());

    for &pos in &change_positions[1..] {
        let new_start = pos.saturating_sub(context_lines);
        let new_end = (pos + context_lines + 1).min(changes.len());
        if new_start <= end {
            end = new_end; // merge
        } else {
            hunk_ranges.push((start, end));
            start = new_start;
            end = new_end;
        }
    }
    hunk_ranges.push((start, end));

    // Build output
    let mut output = format!("--- a/{file_path}\n+++ b/{file_path}\n");

    for (hunk_start, hunk_end) in hunk_ranges {
        // Count old/new lines in hunk
        let mut old_start_line = 1;
        let mut new_start_line = 1;
        let mut old_count = 0;
        let mut new_count = 0;

        // Calculate starting line numbers
        let mut ol = 0;
        let mut nl = 0;
        for (i, change) in changes.iter().enumerate() {
            if i == hunk_start {
                old_start_line = ol + 1;
                new_start_line = nl + 1;
            }
            if i >= hunk_start && i < hunk_end {
                match change {
                    DiffLine::Context(_) => {
                        old_count += 1;
                        new_count += 1;
                    }
                    DiffLine::Remove(_) => {
                        old_count += 1;
                    }
                    DiffLine::Add(_) => {
                        new_count += 1;
                    }
                }
            }
            match change {
                DiffLine::Context(_) => {
                    ol += 1;
                    nl += 1;
                }
                DiffLine::Remove(_) => {
                    ol += 1;
                }
                DiffLine::Add(_) => {
                    nl += 1;
                }
            }
        }

        output.push_str(&format!(
            "@@ -{},{} +{},{} @@\n",
            old_start_line, old_count, new_start_line, new_count
        ));

        for change in &changes[hunk_start..hunk_end] {
            match change {
                DiffLine::Context(l) => output.push_str(&format!(" {l}\n")),
                DiffLine::Remove(l) => output.push_str(&format!("-{l}\n")),
                DiffLine::Add(l) => output.push_str(&format!("+{l}\n")),
            }
        }
    }

    output
}

#[derive(Debug)]
enum DiffLine<'a> {
    Context(&'a str),
    Remove(&'a str),
    Add(&'a str),
}

/// LCS on line sequences — returns pairs of (old_index, new_index) for matching lines.
fn line_lcs<'a>(old: &[&'a str], new: &[&'a str]) -> Vec<(usize, usize)> {
    let m = old.len();
    let n = new.len();

    // Build LCS table
    let mut dp = vec![vec![0u32; n + 1]; m + 1];
    for i in 1..=m {
        for j in 1..=n {
            if old[i - 1] == new[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }

    // Backtrack to find matching pairs
    let mut result = Vec::new();
    let mut i = m;
    let mut j = n;
    while i > 0 && j > 0 {
        if old[i - 1] == new[j - 1] {
            result.push((i - 1, j - 1));
            i -= 1;
            j -= 1;
        } else if dp[i - 1][j] >= dp[i][j - 1] {
            i -= 1;
        } else {
            j -= 1;
        }
    }
    result.reverse();
    result
}
