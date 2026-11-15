# Claude Code Hook Bridge

Make Cognithor's Gatekeeper and Observer supervise every tool call Claude Code
runs in VS Code (or any Claude Code host).

Claude Code ships with native [HTTP hooks](https://code.claude.com/docs/en/hooks).
We point those hooks at Cognithor's running gateway (`http://localhost:8741`
by default) and the bridge does the rest: every `PreToolUse` is gated by the
Gatekeeper, every `PostToolUse` gets a step-level check, and on `Stop` the
Observer audits the whole turn and can force a retry.

## Prerequisites

1. **Cognithor is running.** `python -m jarvis --no-cli` or the usual launcher.
   Confirm: `curl http://localhost:8741/api/claude-hooks/health` should return
   `{"ok": true, "gatekeeper": true, ...}`.
2. **Claude Code 1.x** with HTTP hook support (any build from 2026-01 onward).
3. Python 3.10+ on PATH (only needed if you prefer the command-hook fallback).

## Setup (HTTP hooks, recommended)

Run the installer once:

```bash
python contrib/claude-code-bridge/install.py
```

It:
- Backs up `~/.claude/settings.json` to `settings.json.bak-<timestamp>`.
- Merges a `hooks` block into it (existing hooks are preserved).
- Prints the diff so you can see exactly what changed.

Re-run with `--uninstall` to remove the Cognithor hooks.

## What the installer writes

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8741/api/claude-hooks/pre-tool-use",
        "timeout": 30
      }]
    }],
    "PostToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8741/api/claude-hooks/post-tool-use",
        "timeout": 30
      }]
    }],
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8741/api/claude-hooks/stop",
        "timeout": 60
      }]
    }],
    "SessionStart": [{
      "matcher": "startup|resume",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8741/api/claude-hooks/session-start",
        "timeout": 10
      }]
    }],
    "SessionEnd": [{
      "matcher": "",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8741/api/claude-hooks/session-end",
        "timeout": 10
      }]
    }]
  }
}
```

## Authenticated bridge (multi-user machines)

If you expose the gateway to non-loopback addresses, add a header and an env
var to `settings.json`:

```json
{
  "type": "http",
  "url": "https://cognithor.lan/api/claude-hooks/pre-tool-use",
  "headers": { "Authorization": "Bearer $COGNITHOR_HOOK_TOKEN" },
  "allowedEnvVars": ["COGNITHOR_HOOK_TOKEN"]
}
```

Set `COGNITHOR_HOOK_TOKEN` in your shell/environment. The token must match
the one Cognithor's gateway expects (see `CONFIG_REFERENCE.md` for the API
auth setting).

## Fallback: command-type hook

If your deployment forbids HTTP hooks, use the `cognithor_bridge.py` script
instead -- it reads the hook JSON from stdin, POSTs it to Cognithor, and
echoes the response to stdout:

```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python /ABSOLUTE/PATH/TO/cognithor_bridge.py pre-tool-use",
        "timeout": 30
      }]
    }]
  }
}
```

The command variant has identical semantics to the HTTP variant -- it just
adds a subprocess spawn per hook call.

## Diagnostics

- `curl http://localhost:8741/api/claude-hooks/health` -- liveness + what's wired.
- Cognithor logs: the bridge writes structured log lines starting with
  `claude_code_pre_tool_use`, `claude_code_post_tool_use`, etc.
- Claude Code transcript shows `<hook> error` on HTTP failures; the request
  is treated as a non-blocking error (execution continues).

## What Cognithor does on each event

| Hook          | Cognithor path                                            |
|---------------|-----------------------------------------------------------|
| PreToolUse    | `Gatekeeper.evaluate(PlannedAction)` → allow/deny/ask      |
| PostToolUse   | ToolHookRunner (secret redact, audit log) + step heuristic |
| Stop          | `Observer.audit(...)` over the turn; blocks Stop if failed |
| SessionStart  | Bookkeeping + context hint injected into Claude's session  |
| SessionEnd    | Clean up tracked session state                             |

Fail-open: if the Gatekeeper raises or the Observer times out, the bridge
returns `allow` / no-op so a stuck Cognithor can never deadlock your editor.
