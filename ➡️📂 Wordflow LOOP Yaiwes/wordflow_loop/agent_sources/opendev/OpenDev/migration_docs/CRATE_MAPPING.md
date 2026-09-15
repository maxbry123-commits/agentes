# Python Dependency → Rust Crate Mapping

## Core Runtime

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `pydantic>=2.12.3` | `serde` + `serde_json` | Derive macros for serialize/deserialize |
| `typing`, `dataclasses` | Native Rust types | Structs, enums, traits |
| `asyncio` | `tokio` | Unified async runtime |
| `threading` | `tokio::task` / `std::thread` | Most concurrency via tokio tasks |
| `logging` | `tracing` + `tracing-subscriber` | Structured logging with spans |
| `pathlib` | `std::path::PathBuf` | Native path handling |
| `datetime` | `chrono` | DateTime, Duration, Utc |
| `uuid` | `uuid` | UUID generation (v4) |
| `re` (regex) | `regex` | Regex matching |
| `os.environ` | `std::env` | Environment variables |
| `json` | `serde_json` | JSON parsing |

## HTTP & Networking

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `httpx>=0.28.1` | `reqwest` | Async HTTP client with connection pooling |
| `httpx.Timeout` | `reqwest::ClientBuilder` | Per-request timeout config |
| `fastapi>=0.119.1` | `axum` | Web framework (tower-based) |
| `uvicorn>=0.38.0` | `hyper` (via axum) | HTTP server (embedded in axum) |
| `fastapi.WebSocket` | `axum::extract::ws` | WebSocket support |
| `fastapi.middleware.cors` | `tower-http::cors` | CORS middleware |
| `fastapi.staticfiles` | `tower-http::services::ServeDir` | Static file serving |
| `websockets` | `tokio-tungstenite` | WebSocket client |

## UI & Terminal

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `textual>=0.60.0` | `ratatui` + `crossterm` | Terminal UI framework |
| `rich>=14.2.0` | `termimad` or custom | Markdown terminal rendering |
| `prompt-toolkit>=3.0.52` | `crossterm` (raw mode) | Input handling, key events |
| `argparse` | `clap` | CLI argument parsing |

## AI & LLM

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `openai` | `reqwest` (direct API) | No official Rust SDK; use HTTP directly |
| `anthropic` | `reqwest` (direct API) | No official Rust SDK; use HTTP directly |
| `tiktoken>=0.12.0` | `tiktoken-rs` | Token counting |

## Web Scraping & Browser

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `playwright>=1.55.0` | `headless_chrome` or `fantoccini` | Browser automation via CDP |
| `crawl4ai>=0.7.6` | `reqwest` + `scraper` | Custom fetch + HTML parsing |
| `duckduckgo-search>=6.0.0` | `reqwest` + custom parser | DuckDuckGo API via HTTP |

## File & Git Operations

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `gitpython>=3.1.45` | `git2` | libgit2 bindings |
| `pathspec>=0.11.0` | `ignore` | .gitignore pattern matching |
| `psutil>=5.9.0` | `sysinfo` | Process info, system stats |
| `pypdf>=4.0.0` | `lopdf` or `pdf-extract` | PDF text extraction |
| `pillow>=10.0.0` | `image` | Image processing |

## Protocols

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `fastmcp>=3.0.1` | `rmcp` or custom | MCP client implementation |
| LSP (via solidlsp) | `tower-lsp` + `lsp-types` | LSP protocol (already Rust-native) |

## Testing & Dev

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `pytest>=8.4.2` | Built-in `#[cfg(test)]` | Native test framework |
| `pytest-asyncio>=1.2.0` | `tokio::test` | Async test support |
| `black>=25.9.0` | `rustfmt` | Code formatting |
| `ruff>=0.14.1` | `clippy` | Linting |
| `mypy>=1.18.2` | Rust compiler | Static type checking is built-in |

## Serialization & Data

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| `pydantic` | `serde` + `serde_json` | Serialization framework |
| `python-dotenv>=1.1.1` | `dotenvy` | .env file loading |
| `datasets>=2.0.0` | `reqwest` (API calls) | HuggingFace API for SWE-bench |

## Error Handling & Utilities

| Python Package | Rust Crate | Notes |
|---------------|------------|-------|
| Python exceptions | `thiserror` | Typed library errors |
| `traceback` | `anyhow` | Application error propagation |
| `enum` | `strum` | String conversion for enums |
| `abc.ABC` | Rust traits | Abstract base classes → traits |
| `overrides>=7.0.0` | Not needed | Rust traits enforce implementation |
| `functools.lru_cache` | `cached` or `moka` | Function-level caching |
| `tempfile` | `tempfile` | Temporary files/directories |

## Cargo.toml Dependencies (Workspace Root)

```toml
[workspace.dependencies]
# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1", features = ["v4", "serde"] }
strum = { version = "0.26", features = ["derive"] }

# Async
tokio = { version = "1", features = ["full"] }
tokio-util = { version = "0.7", features = ["sync"] }
async-trait = "0.1"

# HTTP
reqwest = { version = "0.12", features = ["json", "rustls-tls", "stream"] }

# Web
axum = { version = "0.7", features = ["ws"] }
tower-http = { version = "0.6", features = ["cors", "fs"] }
tokio-tungstenite = "0.24"

# Terminal
ratatui = "0.29"
crossterm = "0.28"
clap = { version = "4", features = ["derive"] }
termimad = "0.30"

# Data
tiktoken-rs = "0.6"
regex = "1"
glob = "0.3"
ignore = "0.4"

# Git
git2 = "0.19"

# System
sysinfo = "0.32"
tempfile = "3"
dotenvy = "0.15"
fd-lock = "4"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# Error handling
thiserror = "2"
anyhow = "1"

# Web scraping
scraper = "0.21"

# PDF
lopdf = "0.33"

# Image
image = "0.25"

# Testing
wiremock = "0.6"
proptest = "1"

# LSP
tower-lsp = "0.20"
lsp-types = "0.97"

# Caching
moka = { version = "0.12", features = ["future"] }
```
