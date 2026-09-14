# CLI Config TUI — Design Spec

**Goal:** Interactive terminal config interface for Cognithor. Model/provider swapping with dynamic model discovery, port config, and quick settings.

**Issue:** GitHub #95

---

## Invocation

```bash
cognithor config                                        # Interactive menu
cognithor config set models.planner.name qwen3:14b      # Non-interactive set
cognithor config get models.planner.name                 # Read value
cognithor config list                                    # All settings as table
```

## Interactive Mode — Flow

1. Display current config as `rich.table` (7 fields, color-coded by status)
2. Numbered selection: "Which setting to change? [1-7, q=quit]"
3. Per field type:
   - **Backend/Language/Mode**: `prompt_toolkit` arrow-key selection
   - **Model**: Live list from active backend (Ollama /api/tags, Cloud /models, or cached registry)
   - **Port/Name**: Free-text input with validation
4. After each change: refresh table, return to selection
5. On quit: "Save changes? [Y/n]" -> writes `~/.cognithor/config.yaml`

## Settings (7 fields)

| # | Field | Config Path | Type | Options |
|---|-------|------------|------|---------|
| 1 | LLM Backend | `llm_backend_type` | Selection | ollama, openai, anthropic, gemini, lmstudio, claude-code |
| 2 | Planner Model | `models.planner.name` | Dynamic list | Live from backend + cached fallback |
| 3 | Executor Model | `models.executor.name` | Dynamic list | Live from backend + cached fallback |
| 4 | API Port | `api_port` (top-level) | Number | 1024-65535, default 8741 |
| 5 | Language | `language` | Selection | de, en, zh, ar |
| 6 | Operation Mode | `operation_mode` | Selection | offline, hybrid, online |
| 7 | Owner Name | `owner_name` | Free text | Any string |

## Dynamic Model Discovery

| Backend | Discovery Method | Fallback |
|---------|-----------------|----------|
| Ollama | `GET http://localhost:11434/api/tags` (live, local) | Empty list + manual input |
| OpenAI | `GET https://api.openai.com/v1/models` (live, needs key) | Cached registry |
| Anthropic | No public /models endpoint | Cached registry |
| Gemini | `GET generativelanguage.googleapis.com/v1/models` (live, needs key) | Cached registry |
| LM Studio | `GET http://localhost:1234/v1/models` (live, local) | Empty list + manual input |
| Claude Code | Single model (claude-sonnet-4) | Hardcoded |

**Cached Registry:** `src/cognithor/cli/model_registry.json` ships with the package. Updated weekly by CI workflow that queries each provider's API and commits changes. Always available as offline fallback.

**Custom model:** Every selection list ends with "[ Custom... ]" option for manual model name input. Handles new models not yet in registry.

## Non-Interactive Mode

- `cognithor config set KEY VALUE` — dot-path notation, writes directly to YAML, validates type
- `cognithor config get KEY` — prints value, exit 0 if found, exit 1 if not
- `cognithor config list` — `rich.table` of all 7 fields + current values, no interaction

## Files

```
src/cognithor/cli/config_tui.py       — Interactive menu (rich + prompt_toolkit)
src/cognithor/cli/config_cmd.py       — get/set/list subcommands
src/cognithor/cli/model_registry.py   — Dynamic model discovery + cached fallback
src/cognithor/cli/model_registry.json — Cached model list (CI-updated weekly)
tests/unit/test_config_cmd.py         — Tests for get/set/list
tests/unit/test_model_registry.py     — Tests for discovery + fallback
```

## Wiring

In `__main__.py`, add subcommand parser:

```python
sub = parser.add_subparsers(dest="command")
config_parser = sub.add_parser("config", help="Configure Cognithor")
config_sub = config_parser.add_subparsers(dest="config_action")
config_sub.add_parser("list", help="Show all settings")
set_parser = config_sub.add_parser("set", help="Set a config value")
set_parser.add_argument("key")
set_parser.add_argument("value")
get_parser = config_sub.add_parser("get", help="Get a config value")
get_parser.add_argument("key")
```

Dispatch:
```python
if args.command == "config":
    if args.config_action == "set":
        config_cmd.cmd_set(args.key, args.value)
    elif args.config_action == "get":
        config_cmd.cmd_get(args.key)
    elif args.config_action == "list":
        config_cmd.cmd_list()
    else:
        config_tui.launch()
    sys.exit(0)
```

## CI: Model Registry Freshness

```yaml
name: Update model registry
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 09:00 UTC
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install httpx
      - run: python src/cognithor/cli/model_registry.py --update
      - uses: peter-evans/create-pull-request@v6
        with:
          title: 'chore: update model registry'
          branch: auto/model-registry-update
```

## Testing

- `test_config_cmd.py`: set/get/list with temp config file
- `test_model_registry.py`: Ollama mock, OpenAI mock, fallback to cached JSON
- No tests for interactive TUI (prompt_toolkit testing is fragile) — tested manually

## Dependencies

No new dependencies. `rich` and `prompt_toolkit` are already in core requirements.
