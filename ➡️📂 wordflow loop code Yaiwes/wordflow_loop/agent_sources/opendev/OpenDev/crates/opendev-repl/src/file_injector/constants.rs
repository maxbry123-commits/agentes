//! Constants, extension mappings, and utility helpers for file injection.

use std::path::Path;

/// Safe text extensions to auto-inject.
pub(super) const SAFE_TEXT_EXTENSIONS: &[&str] = &[
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
    ".css",
    ".scss",
    ".less",
    ".sh",
    ".bash",
    ".zsh",
    ".gitignore",
    ".dockerignore",
    ".env.example",
];

/// Special filenames that are text despite having no extension.
pub(super) const SAFE_FILENAMES: &[&str] = &[
    "Dockerfile",
    "Makefile",
    "Rakefile",
    "Gemfile",
    "Procfile",
    "README",
    "LICENSE",
    "CHANGELOG",
    "CONTRIBUTING",
    "AUTHORS",
];

/// Image extensions for multimodal injection.
pub(super) const IMAGE_EXTENSIONS: &[&str] = &[".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"];

/// Known binary extensions -- skip text-detection heuristic.
pub(super) const BINARY_EXTENSIONS: &[&str] = &[
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".rar", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg", ".mp3", ".mp4",
    ".avi", ".mov", ".wav", ".flac", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pyc", ".pyo", ".class", ".o", ".obj", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".sqlite",
    ".db", ".sqlite3",
];

/// Maximum file size before truncation (50 KB).
pub(super) const MAX_FILE_SIZE: u64 = 50 * 1024;

/// Maximum line count before truncation.
pub(super) const MAX_LINES: usize = 1000;

/// Number of lines to keep from the head when truncating.
pub(super) const HEAD_LINES: usize = 100;

/// Number of lines to keep from the tail when truncating.
pub(super) const TAIL_LINES: usize = 50;

/// Maximum directory recursion depth.
pub(super) const MAX_DIR_DEPTH: usize = 3;

/// Maximum items shown per directory level.
pub(super) const MAX_DIR_ITEMS: usize = 50;

/// Return the syntax-highlighting language name for a file extension.
pub(super) fn lang_for_ext(ext: &str) -> &'static str {
    match ext {
        ".py" => "python",
        ".js" => "javascript",
        ".ts" => "typescript",
        ".jsx" => "jsx",
        ".tsx" => "tsx",
        ".java" => "java",
        ".go" => "go",
        ".rs" => "rust",
        ".c" | ".h" => "c",
        ".cpp" | ".hpp" => "cpp",
        ".cs" => "csharp",
        ".rb" => "ruby",
        ".php" => "php",
        ".swift" => "swift",
        ".md" => "markdown",
        ".json" => "json",
        ".yaml" | ".yml" => "yaml",
        ".toml" => "toml",
        ".xml" => "xml",
        ".html" => "html",
        ".css" => "css",
        ".scss" => "scss",
        ".less" => "less",
        ".sh" | ".bash" => "bash",
        ".zsh" => "zsh",
        ".sql" => "sql",
        ".graphql" => "graphql",
        _ => "",
    }
}

/// Get the lowercased extension (including the leading dot) of a path.
pub(super) fn ext_lower(path: &Path) -> String {
    path.extension()
        .map(|e| format!(".{}", e.to_string_lossy().to_lowercase()))
        .unwrap_or_default()
}
