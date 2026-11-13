//! File type processors: text, large files, directories, PDFs, and images.

use base64::Engine as _;
use std::fs;
use std::path::Path;

use super::constants::*;
use super::{FileContentInjector, ImageBlock};

impl FileContentInjector {
    /// Process a single `@` reference, dispatching on file type.
    pub(super) fn process_ref(
        &self,
        ref_str: &str,
        path: &Path,
    ) -> Result<(String, Option<ImageBlock>), String> {
        if !path.exists() {
            return Err("File not found".to_string());
        }

        if path.is_dir() {
            return Ok((self.process_directory(path, ref_str), None));
        }

        let ext = ext_lower(path);

        if ext == ".pdf" {
            return Ok((Self::process_pdf(path, ref_str), None));
        }

        if IMAGE_EXTENSIONS.contains(&ext.as_str()) {
            let (tag, block) = Self::process_image(path, ref_str);
            return Ok((tag, block));
        }

        if Self::is_text_file(path) {
            return Ok((Self::process_text_file(path, ref_str)?, None));
        }

        Err("Unsupported file type".to_string())
    }

    /// Process a text file: read content, optionally truncate.
    pub fn process_text_file(path: &Path, ref_str: &str) -> Result<String, String> {
        let content = fs::read_to_string(path).map_err(|e| format!("Read error: {}", e))?;
        let lines: Vec<&str> = content.lines().collect();
        let line_count = lines.len();
        let size = content.len() as u64;

        if size > MAX_FILE_SIZE || line_count > MAX_LINES {
            return Ok(Self::process_large_file(path, ref_str, &content, &lines));
        }

        let language = Self::get_language(path);
        let lang_attr = if language.is_empty() {
            String::new()
        } else {
            format!(" language=\"{}\"", language)
        };

        let abs_path = path.to_string_lossy();

        Ok(format!(
            "<file_content path=\"{}\" absolute_path=\"{}\" exists=\"true\"{}>\n{}\n</file_content>",
            ref_str, abs_path, lang_attr, content
        ))
    }

    /// Process a large file with head/tail truncation.
    pub fn process_large_file(
        path: &Path,
        ref_str: &str,
        _content: &str,
        lines: &[&str],
    ) -> String {
        let total_lines = lines.len();
        let head: Vec<&str> = lines.iter().take(HEAD_LINES).copied().collect();
        let tail_start = total_lines.saturating_sub(TAIL_LINES);
        let tail: Vec<&str> = lines.iter().skip(tail_start).copied().collect();
        let omitted = if total_lines > HEAD_LINES + TAIL_LINES {
            total_lines - HEAD_LINES - TAIL_LINES
        } else {
            0
        };

        let language = Self::get_language(path);
        let lang_attr = if language.is_empty() {
            String::new()
        } else {
            format!(" language=\"{}\"", language)
        };

        let abs_path = path.to_string_lossy();
        let head_content = head.join("\n");
        let tail_content = tail.join("\n");

        format!(
            "<file_truncated path=\"{}\" absolute_path=\"{}\" exists=\"true\" total_lines=\"{}\"{}>\n\
             === HEAD (lines 1-{}) ===\n\
             {}\n\n\
             === TRUNCATED ({} lines omitted) ===\n\n\
             === TAIL (lines {}-{}) ===\n\
             {}\n\
             </file_truncated>",
            ref_str,
            abs_path,
            total_lines,
            lang_attr,
            HEAD_LINES,
            head_content,
            omitted,
            total_lines - TAIL_LINES + 1,
            total_lines,
            tail_content,
        )
    }

    /// Process a directory: recursive tree listing.
    pub fn process_directory(&self, path: &Path, ref_str: &str) -> String {
        let tree = self.build_tree(path, "", 0);
        let item_count = tree.iter().filter(|l| !l.ends_with("...")).count();
        let dir_name = path
            .file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_else(|| path.to_string_lossy().to_string());

        format!(
            "<directory_listing path=\"{}\" count=\"{}\">\n{}/\n{}\n</directory_listing>",
            ref_str,
            item_count,
            dir_name,
            tree.join("\n"),
        )
    }

    /// Recursively build a tree listing for a directory.
    pub(super) fn build_tree(&self, dir_path: &Path, prefix: &str, depth: usize) -> Vec<String> {
        if depth > MAX_DIR_DEPTH {
            return vec![format!("{}...", prefix)]; // mirrors Python "└── ..."
        }

        let entries = match fs::read_dir(dir_path) {
            Ok(rd) => rd,
            Err(_) => return vec![format!("{}[permission denied]", prefix)],
        };

        let mut items: Vec<std::path::PathBuf> = entries
            .filter_map(|e| {
                e.ok()
                    .map(|e| e.path().canonicalize().unwrap_or_else(|_| e.path()))
            })
            .collect();

        // Sort: directories first, then by lowercase name
        items.sort_by(|a, b| {
            let a_dir = a.is_dir();
            let b_dir = b.is_dir();
            match (a_dir, b_dir) {
                (true, false) => std::cmp::Ordering::Less,
                (false, true) => std::cmp::Ordering::Greater,
                _ => {
                    let a_name = a
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .to_lowercase();
                    let b_name = b
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .to_lowercase();
                    a_name.cmp(&b_name)
                }
            }
        });

        // Filter ignored entries using GitIgnoreParser (respects .gitignore + always-ignored dirs)
        let items: Vec<std::path::PathBuf> = items
            .into_iter()
            .filter(|p| !self.gitignore.is_ignored(p))
            .take(MAX_DIR_ITEMS)
            .collect();

        let mut lines: Vec<String> = Vec::new();
        let count = items.len();

        for (i, item) in items.iter().enumerate() {
            let is_last = i == count - 1;
            let connector = if is_last {
                "\u{2514}\u{2500}\u{2500} "
            } else {
                "\u{251C}\u{2500}\u{2500} "
            };
            let new_prefix = if is_last {
                format!("{}    ", prefix)
            } else {
                format!("{}\u{2502}   ", prefix)
            };

            let name = item
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string();

            if item.is_dir() {
                lines.push(format!("{}{}{}/", prefix, connector, name));
                lines.extend(self.build_tree(item, &new_prefix, depth + 1));
            } else {
                let size_str = item
                    .metadata()
                    .map(|m| format!(" ({})", Self::format_size(m.len())))
                    .unwrap_or_default();
                lines.push(format!("{}{}{}{}", prefix, connector, name, size_str));
            }
        }

        lines
    }

    /// Process a PDF file (placeholder -- real extraction needs an external crate).
    pub fn process_pdf(path: &Path, ref_str: &str) -> String {
        // NOTE: Full PDF text extraction requires a crate like `lopdf` or `pdf-extract`.
        // For now we emit a placeholder tag.
        let abs_path = path.to_string_lossy();
        format!(
            "<pdf_content path=\"{}\" absolute_path=\"{}\" pages=\"?\">\n\
             [PDF text extraction not yet implemented. Add a PDF crate for full support.]\n\
             </pdf_content>",
            ref_str, abs_path,
        )
    }

    /// Process an image: base64 encode and emit an XML tag plus an [`ImageBlock`].
    pub fn process_image(path: &Path, ref_str: &str) -> (String, Option<ImageBlock>) {
        let data = match fs::read(path) {
            Ok(d) => d,
            Err(e) => {
                return (
                    format!(
                        "<file_error path=\"{}\" reason=\"Failed to read image file: {}\" />",
                        ref_str, e
                    ),
                    None,
                );
            }
        };

        let ext = ext_lower(path);
        let mime_type = match ext.as_str() {
            ".png" => "image/png",
            ".jpg" | ".jpeg" => "image/jpeg",
            ".gif" => "image/gif",
            ".webp" => "image/webp",
            ".bmp" => "image/bmp",
            _ => "image/png",
        };

        let b64 = base64::engine::general_purpose::STANDARD.encode(&data);

        let tag = format!(
            "<image path=\"{}\" type=\"{}\">\n[Image attached as multimodal content]\n</image>",
            ref_str, mime_type,
        );

        let block = ImageBlock {
            media_type: mime_type.to_string(),
            data: b64,
        };

        (tag, Some(block))
    }
}
