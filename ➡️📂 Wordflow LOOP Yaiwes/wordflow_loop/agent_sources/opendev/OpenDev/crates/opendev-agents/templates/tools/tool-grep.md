<!--
name: 'Tool Description: Grep'
description: Search file contents using regex patterns via ripgrep
version: 1.0.0
-->

Search file contents using regex patterns (ripgrep).

- Full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
- Literal braces need escaping (use `interface\\{\\}` for `interface{}` in Go)
- Filter by glob ("*.rs"), file_type ("py", "rs"), or path
- Case insensitive: set `-i=true`
- Multiline: set `multiline=true` for cross-line patterns
- Fixed string: set `fixed_string=true` for literal (non-regex) matching
- Output modes: "content" (default), "files_with_matches", "count"
- Results in files_with_matches mode sorted by modification time (newest first)

## Usage notes

- ALWAYS use Grep for content searching. NEVER use Bash with grep or rg — the Grep tool has been optimized for correct permissions and access
- For simple, directed searches (specific class/function name), use Grep directly. For broader codebase exploration requiring multiple rounds, consider a subagent
- When to use Grep vs find_symbol: use Grep for text/regex matching across files; use find_symbol for structured code navigation via LSP (finds definitions, understands symbol hierarchy)
