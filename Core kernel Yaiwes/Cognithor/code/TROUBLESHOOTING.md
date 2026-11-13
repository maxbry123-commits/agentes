# Cognithor Troubleshooting

> Common problems and their solutions.
> For deployment-specific issues, see [deploy/README.md](deploy/README.md).

## Table of Contents

- [Startup Issues](#startup-issues)
- [LLM / Ollama](#llm--ollama)
- [WebUI / WebSocket](#webui--websocket)
- [Flutter UI](#flutter-ui)
- [Tools & Gatekeeper](#tools--gatekeeper)
- [Memory System](#memory-system)
- [GEPA Self-Improvement](#gepa-self-improvement)
- [Channels](#channels)
- [Configuration](#configuration)
- [Performance](#performance)
- [Windows-Specific](#windows-specific)

---

## Startup Issues

### ImportError on launch

```
ModuleNotFoundError: No module named 'cognithor'
```

Install in editable mode:
```bash
pip install -e ".[dev]"
```

### Missing optional dependencies

```
Optional feature 'telegram' not available: No module named 'telegram'
```

Install the required extra:
```bash
pip install -e ".[telegram]"
```

Available extras: `search`, `documents`, `telegram`, `discord`, `slack`,
`matrix`, `web`, `cron`, `vector`, `postgresql`, `irc`, `twitch`, `mcp`.

### Port already in use

```
[ERROR] Address already in use: 0.0.0.0:8741
```

Find and stop the conflicting process:
```bash
# Linux/macOS
lsof -i :8741
kill <PID>

# Windows
netstat -ano | findstr :8741
taskkill /PID <PID> /F
```

Or use a different port:
```bash
python -m cognithor --api-port 8742
```

### Preflight check fails

Run the diagnostics script:
```bash
python scripts/preflight_check.py
```

It validates Python version, Ollama connectivity, model availability, and
package imports. Use `--fix` to auto-resolve model issues:
```bash
python scripts/first_boot.py --fix
```

---

## LLM / Ollama

### Ollama not reachable

```
[ERROR] Connection refused: http://localhost:11434
```

1. Check if Ollama is running: `ollama list`
2. Start it: `ollama serve`
3. If using a remote Ollama, set the URL:
   ```bash
   export OLLAMA_HOST=http://192.168.1.100:11434
   # or in config.yaml:
   # ollama:
   #   base_url: "http://192.168.1.100:11434"
   ```

### Model not found

```
[ERROR] Model 'qwen3:32b' not found
```

Pull the model:
```bash
ollama pull qwen3:32b
```

### Out of VRAM

```
[ERROR] CUDA out of memory
```

Use smaller models:
```yaml
# ~/.cognithor/config.yaml
models:
  planner:
    name: qwen3:14b    # Instead of 32b
  executor:
    name: qwen3:8b
```

VRAM guide:

| GPU VRAM | Planner | Executor |
|----------|---------|----------|
| 32 GB | qwen3:32b | qwen3:8b |
| 24 GB | qwen3:32b | qwen3:8b |
| 12 GB | qwen3:14b | qwen3:8b |
| 8 GB | qwen3:8b | qwen3:8b |

### LLM ignores search results

The Planner (qwen3:32b) sometimes overrides web search results with training
data. This is mitigated by aggressive prompting in `formulate_response()` and
`REPLAN_PROMPT`. If it persists:

1. Use `search_and_read` instead of `web_search` (fetches full pages)
2. Increase `planner.response_token_budget` in config
3. Check that the search results are actually being injected into Working Memory

---

## WebUI / WebSocket

### WebSocket reconnect loop

```
[WS] Reconnecting in 3000ms (attempt 1/10)
[WS] Reconnecting in 6000ms (attempt 2/10)
```

**After server restart:** The browser caches a stale auth token. Hard refresh
(`Ctrl+Shift+R`) clears the cache. The code invalidates `_wsTokenCache` on
close code 4001, so reconnect should auto-fix.

**Server not running:** Check that the backend is running on the expected port:
```bash
curl http://localhost:8741/api/v1/health
```

### WebSocket auth failure (403/4001)

The WebSocket requires authentication. On connect, the client must send:
```json
{"type": "auth", "token": "<bearer-token>"}
```

Common causes:
1. **Token not fetched:** The frontend fetches the token from `GET /api/v1/bootstrap`. If this fails (e.g., CORS, network), the WS auth will also fail.
2. **Token expired/stale:** After a server restart, the session token changes. Hard-refresh the browser.
3. **`from __future__ import annotations` issue:** PEP 563 stores annotations as strings. If `WebSocket` is imported inside a nested function, `get_type_hints()` cannot resolve it, causing a 403. Ensure WebSocket and similar types used in FastAPI signatures are imported at module level.

### WebUI returns 503

The WebUI's `create_app()` factory runs standalone without a Gateway.
`POST /api/v1/message` returns 503 -- this is expected. WebSocket communication
requires the Gateway to be running and connected.

### Canvas not displaying

Check the browser console for Content Security Policy errors. The canvas uses
an iframe with `srcdoc` -- some CSP headers may block inline scripts.

---

## Flutter UI

### BackdropFilter renders black on Android

`BackdropFilter` with `ImageFilter.blur` can render as a black rectangle on
some Android devices with older GPU drivers.

**Fix:** Replace `BackdropFilter` with a semi-transparent `Container`:
```dart
// Instead of BackdropFilter:
Container(
  color: Colors.black.withValues(alpha: 0.3),
  child: content,
)
```

Or check for hardware support and fall back gracefully.

### Chat state loss on navigation

If navigating away from the chat page and back causes message history to
disappear, the state is being held in a local `StatefulWidget` instead of a
persistent provider.

**Fix:** Move chat state to a `ChangeNotifier` or `Riverpod` provider that
outlives the widget tree. Store messages in the provider, not the widget.

### Service Worker cache serving stale assets

After a Flutter web deployment update, the browser may continue serving old
assets due to the service worker cache.

**Symptoms:** UI shows old version, API calls fail with schema mismatches.

**Fix:**
1. Hard refresh: `Ctrl+Shift+R`
2. Clear service worker: DevTools -> Application -> Service Workers -> Unregister
3. Add cache-busting to `flutter_service_worker.js`:
   ```
   const CACHE_NAME = 'flutter-app-cache-v2';  // Increment version
   ```
4. For production, configure your web server to set `Cache-Control: no-cache` for `flutter_service_worker.js` and `main.dart.js`.

### WebSocket connection fails in Flutter

The Flutter WebSocket client uses `web_socket_channel`. If connecting to `ws://localhost:8741/ws` fails:

1. **Android emulator:** Use `10.0.2.2` instead of `localhost`
2. **iOS simulator:** `localhost` works, but real devices need the machine's IP
3. **Auth:** Send the auth message immediately after connect:
   ```dart
   channel.sink.add(jsonEncode({"type": "auth", "token": token}));
   ```

---

## Tools & Gatekeeper

### Tool blocked (ORANGE/RED)

```
[GATEKEEPER] BLOCKED: exec_command -- risk level RED
```

**Unknown tools** default to ORANGE. If you added a new tool:
1. Register it in `core/gatekeeper.py` -> `_classify_risk()`
2. Add to the appropriate risk set (`_GREEN_TOOLS`, `_YELLOW_TOOLS`, etc.)

**Destructive commands** (`rm -rf`, `sudo`, `dd`) are always RED.

### Path validation error

```
[ERROR] Path traversal blocked: /etc/passwd
```

File operations are restricted to `allowed_paths` in config:
```yaml
security:
  allowed_paths:
    - ~/.cognithor
    - ~/Documents
    - /path/to/project
```

### Tool timeout

Default timeout is 30s. Media tools have higher limits (120-180s). Override:
```yaml
executor:
  default_timeout_seconds: 60
```

---

## Memory System

### Memory search returns no results

1. Check if memory has data:
   ```
   User > Show memory statistics
   ```
2. Verify embeddings model is loaded:
   ```bash
   ollama list | grep nomic-embed
   ```
3. Re-index if needed (memory is stored in `~/.cognithor/memory/`)

### Episodic memory growing too large

The `EpisodicCompressor` summarizes old entries. If it's not running:
```yaml
memory:
  compressor_enabled: true
  compressor_age_days: 30
```

### Knowledge graph inconsistencies

Run memory hygiene scan via API:
```bash
curl -X POST http://localhost:8741/api/v1/memory/hygiene/scan \
  -H "Authorization: Bearer <token>"
```

---

## GEPA Self-Improvement

### GEPA not enabled

```json
{"enabled": false, "message": "GEPA not enabled"}
```

Enable in config:
```yaml
gepa:
  enabled: true
  evolution_interval_hours: 6
```

Restart Cognithor after changing the config.

### Evolution cycle skipped (insufficient traces)

```
evolution_cycle_skipped_insufficient_traces traces=3 required=10
```

GEPA requires at least `min_traces_for_proposal` traces (default: 10) before
analyzing patterns. Use the system more, or lower the threshold:
```yaml
gepa:
  min_traces_for_proposal: 5
```

### Proposal auto-apply blocked

```
evolution_auto_apply_blocked reason=max_active_reached
```

Only `max_active_optimizations` (default: 1) proposals can be applied at once.
Either rollback the current proposal or increase the limit:
```yaml
gepa:
  max_active_optimizations: 2
```

### Auto-rollback triggered

```
evolution_auto_rollback pre_success=0.85 post_success=0.72 delta=-0.13
```

A proposal was rolled back because the success rate dropped more than the
`auto_rollback_threshold` (default: 10%). This is expected safety behavior.
Review the proposal details to understand why it degraded performance:
```bash
curl http://localhost:8741/api/v1/evolution/proposals/<proposal_id> \
  -H "Authorization: Bearer <token>"
```

### Manual cycle trigger

To run an evolution cycle on demand:
```bash
curl -X POST http://localhost:8741/api/v1/evolution/run \
  -H "Authorization: Bearer <token>"
```

---

## Channels

### Telegram bot not responding

1. Check token: `echo $COGNITHOR_TELEGRAM_TOKEN`
2. Verify bot is started in config:
   ```yaml
   channels:
     telegram:
       enabled: true
   ```
3. Check allowed users: `COGNITHOR_TELEGRAM_ALLOWED_USERS=123456,789012`
4. Review logs: `tail -f ~/.cognithor/logs/cognithor.log | grep telegram`

### Discord/Slack connection fails

Most channel-specific issues are dependency problems. Install the right extra:
```bash
pip install -e ".[discord]"   # discord.py
pip install -e ".[slack]"     # slack-sdk
```

---

## Configuration

### Config validation errors

Cognithor uses Pydantic models for configuration. Common validation failures:

**discord_channel_id type mismatch:**
```
Input should be a valid string [type=string_type]
```

Discord channel IDs are large integers that may overflow in some languages. In
`config.yaml`, always quote them as strings:
```yaml
channels:
  discord:
    channel_id: "1234567890123456789"   # String, not int
```

**Invalid enum values:**
```
Input should be 'green', 'yellow', 'orange' or 'red'
```

Check that config values match the expected Literal types. See `config.py` for
the valid values for each field.

**Extra fields rejected:**
```
Extra inputs are not permitted
```

Pydantic strict mode rejects unknown keys. Check for typos in config field names.

### Environment variable override not working

Environment variables must be prefixed with `COGNITHOR_`:
```bash
export COGNITHOR_LOG_LEVEL=DEBUG
export COGNITHOR_LANGUAGE=en
export COGNITHOR_API_TOKEN=my-secret-token
```

The 3-layer cascade is: defaults -> `config.yaml` -> `COGNITHOR_*` env vars.
Env vars always win.

---

## Performance

### Slow response times

1. **Model too large** -- Use a smaller executor model (qwen3:8b)
2. **Too many PGE iterations** -- Reduce `planner.max_iterations`:
   ```yaml
   planner:
     max_iterations: 15    # Default: 25
   ```
3. **Memory search slow** -- Check FAISS index size, consider reducing `top_k`
4. **Web search slow** -- Set up SearXNG locally for faster results

### High memory usage

1. **Ollama context** -- Reduce `models.planner.context_window`
2. **Session history** -- Reduce session storage limit
3. **Vector index** -- FAISS HNSW uses ~1 GB per 500K entries

---

## Windows-Specific

### Unicode output errors

```
UnicodeEncodeError: 'charmap' codec can't encode character
```

Windows console uses cp1252 by default. The codebase uses ASCII-safe symbols
(`[OK]`/`[FAIL]` instead of checkmarks/arrows). If you see this in your own
code, set UTF-8 mode:
```bash
set PYTHONIOENCODING=utf-8
```

### `connect_read_pipe` not supported

```
NotImplementedError: connect_read_pipe
```

Windows ProactorEventLoop doesn't support `connect_read_pipe`. The MCP server
uses `loop.run_in_executor()` with a threading reader as fallback.

### Sandbox level

Windows uses Job Objects (`jobobject` sandbox level) instead of Linux
namespaces (`bwrap`). This provides resource limits but less isolation than
Linux containers.

### Long path issues

Enable long paths in Windows:
```
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1
```

Or use a shorter `COGNITHOR_HOME`:
```bash
set COGNITHOR_HOME=C:\cognithor
```

### Python executable portability

Always use `sys.executable` instead of hardcoding `"python"` or `"python3"`.
On Windows, the Python path varies depending on the installation method
(Microsoft Store, official installer, conda, pyenv-win).
