# openswarm-gui MCP: a Playwright hand for a Claude Code tester

This is the "GUI hand" for the testing pyramid. The deterministic scripts in
`scripts/ci/` are the fast, free, binary CI gate (boot, signing, resilience,
network, agent turn). This MCP server covers the part scripts can't express:
**actual GUI behavior**, by letting a Claude Code instance you talk to drive the
real packaged app at Playwright (DOM) precision.

It is NOT a replacement for the scripts. A CC tester *runs the scripts* for the
mechanical 95% and uses these tools for the exploratory/judgment 5% (does the
screen render, does clicking actually do something, does it look right) and for
escalation when a script is stuck or a result looks fake.

## Setup (one-time, your call)

Registering an auto-connecting MCP server modifies CC's own config, so add it
yourself, either:

```bash
claude mcp add openswarm-gui -- node e2e/mcp/electron-mcp.js
```

or create `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "openswarm-gui": { "command": "node", "args": ["e2e/mcp/electron-mcp.js"] }
  }
}
```

Then `cd e2e && npm install` (pulls the MCP SDK + Playwright). Build the app first
so there's a packaged binary to drive (`electron/dist/win-unpacked` or the `.app`).

## Tools

| Tool | What it does |
| --- | --- |
| `app_launch` | launch the packaged app, wait for the main window, return backend port + build provenance |
| `app_close` | close the app |
| `screenshot` | PNG of the current window (the eyes) |
| `snapshot` | accessibility tree (structured "what's on screen", no pixels) |
| `click` / `fill` / `press` | drive inputs by Playwright selector (CSS, `text=`, `role=`) |
| `wait_for` | wait until a selector is visible |
| `eval` | run JS in the renderer and return JSON (inspect anything, incl. `window.openswarm`) |
| `read_log` | tail `backend.log` (provenance + `[perf]` marks + errors) |

## Verification rubric (the prompt a CC tester follows)

1. Run the deterministic gate first: `node scripts/ci/verify-all.js`. If anything
   there fails, stop and report; the GUI walk only matters once boot/serve pass.
2. `app_launch`. Confirm the returned `build.sha` matches `git rev-parse HEAD`.
3. Walk every surface from `frontend/src/app/Main.tsx`: open each screen/tab, take
   a `screenshot` + `snapshot`, and for each primary control `click` it and confirm
   the follow-on state changes (new view, dialog opens, list updates).
4. Drive the core flow: start a new session, `fill` the prompt, send, confirm a
   reply renders, then confirm `read_log` shows `[perf] first-agent-response`
   (this is the renderer-driven mark the API-only agent-turn check can't assert).
5. Flag anything that renders blank, throws in the console (`eval` on
   `window.__errors__` if present, or watch for empty `#root`), or looks visually
   broken. Capture a screenshot with every flag.
6. `app_close`.

A CC instance running this is the apex of the pyramid: interactive (you chat with
it), fully featured (it can also edit code, run the scripts, read any file), and
future-proof (any new CC capability is available the moment it ships).
