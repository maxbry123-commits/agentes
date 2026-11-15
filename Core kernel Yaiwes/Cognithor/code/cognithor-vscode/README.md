# Cognithor VS Code Extension

Local-first AI Coding Intelligence powered by [Cognithor Agent OS](https://github.com/Alex8791-cyber/cognithor).

## Features

- **Chat Sidebar** — Ask Cognithor anything from within VS Code
- **Code Lens** — "Explain", "Refactor", "Tests" buttons above functions
- **Context Aware** — Automatically sends selected code + surrounding context
- **Streaming** — Token-by-token response streaming via WebSocket
- **Diff View** — Review AI-suggested changes before applying

## Requirements

- [Cognithor](https://github.com/Alex8791-cyber/cognithor) running on `localhost:8741`
- VS Code 1.85+

## Quick Start

1. Install the extension
2. Start Cognithor: `python -m jarvis --no-cli`
3. Open the Cognithor sidebar (Activity Bar icon)
4. Start chatting!

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `cognithor.serverUrl` | `http://localhost:8741` | Cognithor server URL |
| `cognithor.streamingEnabled` | `true` | Token-by-token streaming |
| `cognithor.contextLines` | `100` | Lines of context around selection |
| `cognithor.codeLens` | `true` | Show Code Lens buttons |
| `cognithor.language` | `auto` | Response language (auto/de/en) |

## License

Apache 2.0
