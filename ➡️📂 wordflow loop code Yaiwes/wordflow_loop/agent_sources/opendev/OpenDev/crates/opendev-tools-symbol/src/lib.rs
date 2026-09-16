//! Symbol tools for OpenDev: find, references, rename, and replace body.
//!
//! These tools provide AST-based code navigation and refactoring capabilities,
//! delegating to an LSP server through `opendev-tools-lsp`.

pub mod error;
pub mod find_references;
pub mod find_symbol;
pub mod rename;
pub mod replace_body;
mod util;

pub use error::SymbolError;
pub use find_references::handle_find_references;
pub use find_symbol::handle_find_symbol;
pub use rename::handle_rename_symbol;
pub use replace_body::handle_replace_symbol_body;
