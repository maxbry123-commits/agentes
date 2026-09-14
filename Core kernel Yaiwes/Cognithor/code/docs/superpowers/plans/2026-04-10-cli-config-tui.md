# CLI Config TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `cognithor config` interactive TUI + non-interactive get/set/list with dynamic model discovery from all LLM providers.

**Architecture:** 4 new files in `src/cognithor/cli/` (package init, config commands, model registry, interactive TUI) + 1 JSON registry + 2 test files + 1 CI workflow. Wired into existing `__main__.py` via argparse subcommands. Config read/write uses existing `ConfigManager`.

**Tech Stack:** rich (tables, console), prompt_toolkit (interactive selection), httpx (model discovery), pyyaml (config write), argparse (CLI parsing)

---

### Task 1: Create `src/cognithor/cli/` Package + Model Registry JSON

**Files:**
- Create: `src/cognithor/cli/__init__.py`
- Create: `src/cognithor/cli/model_registry.json`
- Create: `src/cognithor/cli/model_registry.py`
- Test: `tests/unit/test_model_registry.py`

- [ ] **Step 1: Write failing tests for model registry**

```python
# tests/unit/test_model_registry.py
"""Tests for cognithor.cli.model_registry — dynamic model discovery."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from cognithor.cli.model_registry import ModelRegistry


class TestCachedModels:
    def test_load_cached_registry(self):
        registry = ModelRegistry()
        models = registry.get_cached_models("ollama")
        assert isinstance(models, list)

    def test_cached_registry_has_known_providers(self):
        registry = ModelRegistry()
        for provider in ("ollama", "openai", "anthropic", "gemini"):
            models = registry.get_cached_models(provider)
            assert isinstance(models, list)
            assert len(models) >= 1, f"No cached models for {provider}"

    def test_unknown_provider_returns_empty(self):
        registry = ModelRegistry()
        assert registry.get_cached_models("nonexistent") == []


class TestLiveDiscovery:
    @pytest.mark.asyncio
    async def test_ollama_live_discovery(self):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen3:32b"},
                {"name": "qwen3:8b"},
                {"name": "nomic-embed-text"},
            ]
        }
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            registry = ModelRegistry()
            models = await registry.discover_models("ollama")
            assert "qwen3:32b" in models
            assert "qwen3:8b" in models

    @pytest.mark.asyncio
    async def test_fallback_to_cached_on_error(self):
        with patch("httpx.AsyncClient", side_effect=Exception("connection refused")):
            registry = ModelRegistry()
            models = await registry.discover_models("ollama")
            # Falls back to cached
            assert isinstance(models, list)


class TestCustomModelOption:
    def test_models_list_ends_with_custom(self):
        registry = ModelRegistry()
        models = registry.get_cached_models("openai")
        assert models[-1] == "[ Custom... ]"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_model_registry.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create package init and model registry JSON**

```python
# src/cognithor/cli/__init__.py
"""Cognithor CLI tools — config TUI, model registry."""
```

```json
// src/cognithor/cli/model_registry.json
{
  "updated": "2026-04-10",
  "providers": {
    "ollama": {
      "discovery_url": "http://localhost:11434/api/tags",
      "models": ["qwen3:32b", "qwen3:8b", "qwen3:1.7b", "llama3.3:70b", "llama3.2:8b", "mistral:7b", "gemma2:9b", "phi-4:14b", "nomic-embed-text", "deepseek-r1:32b"]
    },
    "openai": {
      "discovery_url": "https://api.openai.com/v1/models",
      "api_key_env": "COGNITHOR_OPENAI_API_KEY",
      "models": ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini", "o3", "o3-mini", "o4-mini"]
    },
    "anthropic": {
      "discovery_url": null,
      "models": ["claude-sonnet-4-20250514", "claude-haiku-4-20250414", "claude-opus-4-20250514"]
    },
    "gemini": {
      "discovery_url": "https://generativelanguage.googleapis.com/v1/models",
      "api_key_env": "COGNITHOR_GEMINI_API_KEY",
      "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
    },
    "lmstudio": {
      "discovery_url": "http://localhost:1234/v1/models",
      "models": []
    },
    "claude-code": {
      "discovery_url": null,
      "models": ["claude-sonnet-4"]
    }
  }
}
```

- [ ] **Step 4: Implement ModelRegistry**

```python
# src/cognithor/cli/model_registry.py
"""Dynamic model discovery with cached fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_REGISTRY_PATH = Path(__file__).parent / "model_registry.json"
_CUSTOM_OPTION = "[ Custom... ]"


class ModelRegistry:
    """Discovers available models from LLM providers."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        try:
            self._cache = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            self._cache = {"providers": {}}

    def get_cached_models(self, provider: str) -> list[str]:
        """Return cached model list for a provider, ending with Custom option."""
        entry = self._cache.get("providers", {}).get(provider, {})
        models = list(entry.get("models", []))
        if not models or models[-1] != _CUSTOM_OPTION:
            models.append(_CUSTOM_OPTION)
        return models

    async def discover_models(self, provider: str) -> list[str]:
        """Try live discovery, fall back to cache."""
        entry = self._cache.get("providers", {}).get(provider, {})
        url = entry.get("discovery_url")
        if not url:
            return self.get_cached_models(provider)

        try:
            import httpx

            headers: dict[str, str] = {}
            api_key_env = entry.get("api_key_env", "")
            if api_key_env:
                key = os.environ.get(api_key_env, "")
                if not key:
                    return self.get_cached_models(provider)
                headers["Authorization"] = f"Bearer {key}"

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            # Parse response — different formats per provider
            if provider == "ollama":
                models = [m["name"] for m in data.get("models", [])]
            elif provider in ("openai", "lmstudio"):
                models = sorted(m["id"] for m in data.get("data", []))
            elif provider == "gemini":
                models = sorted(
                    m["name"].replace("models/", "")
                    for m in data.get("models", [])
                    if "generateContent" in str(m.get("supportedGenerationMethods", []))
                )
            else:
                models = []

            if models:
                models.append(_CUSTOM_OPTION)
                log.info("model_registry_live_discovery", provider=provider, count=len(models) - 1)
                return models
        except Exception:
            log.debug("model_registry_live_failed", provider=provider, exc_info=True)

        return self.get_cached_models(provider)

    def discover_models_sync(self, provider: str) -> list[str]:
        """Synchronous wrapper for discover_models."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already in async context — use cached
            return self.get_cached_models(provider)
        return asyncio.run(self.discover_models(provider))


async def update_registry() -> None:
    """Fetch latest models from all providers and update the JSON file."""
    registry = ModelRegistry()
    cache = registry._cache

    for provider, entry in cache.get("providers", {}).items():
        if not entry.get("discovery_url"):
            continue
        try:
            models = await registry.discover_models(provider)
            # Remove Custom option before saving
            models = [m for m in models if m != _CUSTOM_OPTION]
            if models:
                entry["models"] = models
                print(f"  {provider}: {len(models)} models")
        except Exception as e:
            print(f"  {provider}: FAILED ({e})")

    from datetime import date
    cache["updated"] = date.today().isoformat()
    _REGISTRY_PATH.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Registry saved to {_REGISTRY_PATH}")


if __name__ == "__main__":
    import sys
    if "--update" in sys.argv:
        asyncio.run(update_registry())
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_model_registry.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/cognithor/cli/ tests/unit/test_model_registry.py
git commit -m "feat: add model registry with dynamic discovery + cached fallback"
```

---

### Task 2: Non-Interactive Config Commands (get/set/list)

**Files:**
- Create: `src/cognithor/cli/config_cmd.py`
- Test: `tests/unit/test_config_cmd.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_config_cmd.py
"""Tests for cognithor.cli.config_cmd — get/set/list subcommands."""

from __future__ import annotations

import yaml
import pytest
from pathlib import Path

from cognithor.cli.config_cmd import cmd_get, cmd_set, cmd_list


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    cfg = {
        "llm_backend_type": "ollama",
        "language": "de",
        "operation_mode": "hybrid",
        "owner_name": "Test User",
        "models": {
            "planner": {"name": "qwen3:32b", "backend": "ollama"},
            "executor": {"name": "qwen3:8b", "backend": "ollama"},
        },
    }
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(cfg), encoding="utf-8")
    return p


class TestCmdGet:
    def test_get_top_level(self, tmp_config: Path, capsys):
        code = cmd_get("llm_backend_type", config_path=tmp_config)
        assert code == 0
        assert "ollama" in capsys.readouterr().out

    def test_get_nested(self, tmp_config: Path, capsys):
        code = cmd_get("models.planner.name", config_path=tmp_config)
        assert code == 0
        assert "qwen3:32b" in capsys.readouterr().out

    def test_get_missing_key(self, tmp_config: Path):
        code = cmd_get("nonexistent.key", config_path=tmp_config)
        assert code == 1


class TestCmdSet:
    def test_set_top_level(self, tmp_config: Path):
        code = cmd_set("language", "en", config_path=tmp_config)
        assert code == 0
        cfg = yaml.safe_load(tmp_config.read_text(encoding="utf-8"))
        assert cfg["language"] == "en"

    def test_set_nested(self, tmp_config: Path):
        code = cmd_set("models.planner.name", "llama3:8b", config_path=tmp_config)
        assert code == 0
        cfg = yaml.safe_load(tmp_config.read_text(encoding="utf-8"))
        assert cfg["models"]["planner"]["name"] == "llama3:8b"

    def test_set_integer(self, tmp_config: Path):
        code = cmd_set("api_port", "9000", config_path=tmp_config)
        assert code == 0
        cfg = yaml.safe_load(tmp_config.read_text(encoding="utf-8"))
        assert cfg["api_port"] == 9000


class TestCmdList:
    def test_list_shows_settings(self, tmp_config: Path, capsys):
        code = cmd_list(config_path=tmp_config)
        assert code == 0
        out = capsys.readouterr().out
        assert "ollama" in out
        assert "qwen3:32b" in out
        assert "de" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_config_cmd.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement config_cmd.py**

```python
# src/cognithor/cli/config_cmd.py
"""Non-interactive config commands: get, set, list."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

_console = Console()

# Fields displayed in list view
_DISPLAY_FIELDS = [
    ("LLM Backend", "llm_backend_type"),
    ("Planner Model", "models.planner.name"),
    ("Executor Model", "models.executor.name"),
    ("API Port", "api_port"),
    ("Language", "language"),
    ("Operation Mode", "operation_mode"),
    ("Owner Name", "owner_name"),
]

_DEFAULT_CONFIG = Path.home() / ".cognithor" / "config.yaml"


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


def _save_config(data: dict[str, Any], config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _get_nested(data: dict[str, Any], dot_path: str) -> Any:
    """Traverse a dict by dot-separated path. Returns _MISSING on failure."""
    parts = dot_path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


_MISSING = object()


def _set_nested(data: dict[str, Any], dot_path: str, value: Any) -> None:
    """Set a value in a nested dict by dot-separated path."""
    parts = dot_path.split(".")
    current = data
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    # Auto-convert numeric strings
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    elif isinstance(value, str) and value.replace(".", "", 1).isdigit():
        value = float(value)
    current[parts[-1]] = value


def cmd_get(key: str, *, config_path: Path = _DEFAULT_CONFIG) -> int:
    """Print config value for a dot-path key. Returns 0 on success, 1 if not found."""
    data = _load_config(config_path)
    value = _get_nested(data, key)
    if value is _MISSING:
        _console.print(f"[red]Key not found:[/red] {key}")
        return 1
    _console.print(str(value))
    return 0


def cmd_set(key: str, value: str, *, config_path: Path = _DEFAULT_CONFIG) -> int:
    """Set a config value by dot-path key. Returns 0 on success."""
    data = _load_config(config_path)
    _set_nested(data, key, value)
    _save_config(data, config_path)
    _console.print(f"[green]Set[/green] {key} = {value}")
    return 0


def cmd_list(*, config_path: Path = _DEFAULT_CONFIG) -> int:
    """Display all settings as a rich table. Returns 0."""
    data = _load_config(config_path)
    table = Table(title="Cognithor Configuration", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="cyan")
    table.add_column("Config Path", style="dim")

    for i, (label, path) in enumerate(_DISPLAY_FIELDS, 1):
        value = _get_nested(data, path)
        val_str = str(value) if value is not _MISSING else "[dim]not set[/dim]"
        table.add_row(str(i), label, val_str, path)

    _console.print(table)
    return 0
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_config_cmd.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/cognithor/cli/config_cmd.py tests/unit/test_config_cmd.py
git commit -m "feat: add cognithor config get/set/list commands"
```

---

### Task 3: Interactive Config TUI

**Files:**
- Create: `src/cognithor/cli/config_tui.py`

- [ ] **Step 1: Implement the interactive TUI**

```python
# src/cognithor/cli/config_tui.py
"""Interactive config TUI using rich + prompt_toolkit."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.table import Table

from cognithor.cli.config_cmd import (
    _DEFAULT_CONFIG,
    _DISPLAY_FIELDS,
    _MISSING,
    _get_nested,
    _load_config,
    _save_config,
    _set_nested,
)
from cognithor.cli.model_registry import ModelRegistry

_console = Console()

_SELECTION_OPTIONS: dict[str, list[str]] = {
    "llm_backend_type": ["ollama", "openai", "anthropic", "gemini", "lmstudio", "claude-code"],
    "language": ["de", "en", "zh", "ar"],
    "operation_mode": ["offline", "hybrid", "online"],
}

_CUSTOM_OPTION = "[ Custom... ]"


def _show_table(data: dict[str, Any]) -> None:
    """Display current config as a numbered table."""
    table = Table(title="Cognithor Configuration", show_lines=True, width=80)
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="green")

    for i, (label, path) in enumerate(_DISPLAY_FIELDS, 1):
        value = _get_nested(data, path)
        val_str = str(value) if value is not _MISSING else "[dim]not set[/dim]"
        table.add_row(str(i), label, val_str)

    _console.print(table)
    _console.print("\n[dim]Enter number to edit, q to quit[/dim]")


def _select_from_list(options: list[str], current: str, label: str) -> str:
    """Let user pick from a list using prompt_toolkit."""
    _console.print(f"\n[bold]{label}[/bold]  (current: [cyan]{current}[/cyan])")
    for i, opt in enumerate(options, 1):
        marker = " [green]*[/green]" if opt == current else ""
        _console.print(f"  {i}. {opt}{marker}")

    completer = WordCompleter([str(i) for i in range(1, len(options) + 1)])
    while True:
        try:
            choice = pt_prompt(f"Select [1-{len(options)}]: ", completer=completer).strip()
        except (EOFError, KeyboardInterrupt):
            return current
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            selected = options[int(choice) - 1]
            if selected == _CUSTOM_OPTION:
                custom = pt_prompt("Enter model name: ").strip()
                return custom if custom else current
            return selected
        _console.print("[red]Invalid choice[/red]")


def _edit_text(current: str, label: str) -> str:
    """Free-text input with current value as default."""
    _console.print(f"\n[bold]{label}[/bold]  (current: [cyan]{current}[/cyan])")
    try:
        value = pt_prompt("New value: ", default=current).strip()
        return value if value else current
    except (EOFError, KeyboardInterrupt):
        return current


def _edit_number(current: int, label: str, min_val: int = 1024, max_val: int = 65535) -> int:
    """Number input with range validation."""
    _console.print(f"\n[bold]{label}[/bold]  (current: [cyan]{current}[/cyan], range: {min_val}-{max_val})")
    try:
        value = pt_prompt("New value: ", default=str(current)).strip()
        num = int(value)
        if min_val <= num <= max_val:
            return num
        _console.print(f"[red]Must be between {min_val} and {max_val}[/red]")
        return current
    except (ValueError, EOFError, KeyboardInterrupt):
        return current


def launch(config_path: Path = _DEFAULT_CONFIG) -> None:
    """Main interactive config loop."""
    data = _load_config(config_path)
    original = str(data)  # Snapshot for change detection
    registry = ModelRegistry()

    _console.print("\n[bold]Cognithor Configuration[/bold]\n")

    while True:
        _show_table(data)
        try:
            choice = pt_prompt("\nEdit [1-7, q=quit]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

        if choice == "q":
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(_DISPLAY_FIELDS)):
            _console.print("[red]Invalid choice[/red]")
            continue

        idx = int(choice) - 1
        label, path = _DISPLAY_FIELDS[idx]
        current = _get_nested(data, path)
        current_str = str(current) if current is not _MISSING else ""

        if path in _SELECTION_OPTIONS:
            # Static selection list
            new_value = _select_from_list(_SELECTION_OPTIONS[path], current_str, label)
            _set_nested(data, path, new_value)

        elif path.startswith("models.") and path.endswith(".name"):
            # Dynamic model list
            backend = _get_nested(data, "llm_backend_type") or "ollama"
            models = registry.discover_models_sync(str(backend))
            new_value = _select_from_list(models, current_str, label)
            _set_nested(data, path, new_value)

        elif path == "api_port":
            new_value = _edit_number(int(current_str) if current_str.isdigit() else 8741, label)
            _set_nested(data, path, new_value)

        else:
            new_value = _edit_text(current_str, label)
            _set_nested(data, path, new_value)

        _console.print(f"[green]Updated:[/green] {label} = {new_value}")

    # Save if changed
    if str(data) != original:
        try:
            save = pt_prompt("\nSave changes? [Y/n]: ", default="Y").strip().lower()
        except (EOFError, KeyboardInterrupt):
            save = "n"
        if save != "n":
            _save_config(data, config_path)
            _console.print("[green]Configuration saved.[/green]")
        else:
            _console.print("[yellow]Changes discarded.[/yellow]")
    else:
        _console.print("[dim]No changes made.[/dim]")
```

- [ ] **Step 2: Manual smoke test**

Run: `python -c "from cognithor.cli.config_tui import launch; print('Import OK')"`
Expected: "Import OK"

- [ ] **Step 3: Commit**

```bash
git add src/cognithor/cli/config_tui.py
git commit -m "feat: add interactive config TUI with dynamic model discovery"
```

---

### Task 4: Wire into `__main__.py`

**Files:**
- Modify: `src/cognithor/__main__.py`

- [ ] **Step 1: Add subcommand parser to `parse_args()`**

In `src/cognithor/__main__.py`, find the `parse_args()` function (around line 85). Before `return parser.parse_args()` (around line 155), add:

```python
    # Subcommands
    sub = parser.add_subparsers(dest="command")
    config_parser = sub.add_parser("config", help="Configure Cognithor interactively")
    config_sub = config_parser.add_subparsers(dest="config_action")
    config_sub.add_parser("list", help="Show current settings")
    set_p = config_sub.add_parser("set", help="Set a config value")
    set_p.add_argument("key", help="Dot-path config key (e.g. models.planner.name)")
    set_p.add_argument("value", help="New value")
    get_p = config_sub.add_parser("get", help="Get a config value")
    get_p.add_argument("key", help="Dot-path config key")

    return parser.parse_args()
```

- [ ] **Step 2: Add dispatch in `main()`**

In the `main()` function (around line 247), after `args = parse_args()` and before the existing startup logic, add:

```python
    # Handle config subcommand before full startup
    if getattr(args, "command", None) == "config":
        from cognithor.cli import config_cmd, config_tui

        config_path = args.config or (Path.home() / ".cognithor" / "config.yaml")
        action = getattr(args, "config_action", None)
        if action == "set":
            sys.exit(config_cmd.cmd_set(args.key, args.value, config_path=config_path))
        elif action == "get":
            sys.exit(config_cmd.cmd_get(args.key, config_path=config_path))
        elif action == "list":
            sys.exit(config_cmd.cmd_list(config_path=config_path))
        else:
            config_tui.launch(config_path=config_path)
            sys.exit(0)
```

- [ ] **Step 3: Verify wiring works**

Run: `python -m cognithor config list`
Expected: Rich table with current config values (or "not set" if no config exists)

Run: `python -m cognithor config get language`
Expected: Prints the language value

Run: `python -m cognithor config set language en`
Expected: "Set language = en"

- [ ] **Step 4: Commit**

```bash
git add src/cognithor/__main__.py
git commit -m "feat: wire cognithor config subcommand into CLI"
```

---

### Task 5: CI Workflow for Model Registry Updates

**Files:**
- Create: `.github/workflows/update-model-registry.yml`

- [ ] **Step 1: Create the workflow**

```yaml
# .github/workflows/update-model-registry.yml
name: Update model registry

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 09:00 UTC
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  update:
    name: Refresh model lists
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install httpx pyyaml

      - name: Update registry
        run: python src/cognithor/cli/model_registry.py --update
        env:
          COGNITHOR_OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          COGNITHOR_GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

      - name: Check for changes
        id: diff
        run: |
          git diff --quiet src/cognithor/cli/model_registry.json || echo "changed=true" >> $GITHUB_OUTPUT

      - name: Create PR
        if: steps.diff.outputs.changed == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          title: 'chore: update model registry'
          branch: auto/model-registry-update
          commit-message: 'chore: update model registry [automated]'
          body: 'Automated weekly update of cached LLM model lists.'
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/update-model-registry.yml
git commit -m "ci: add weekly model registry update workflow"
```

---

### Task 6: Final Integration Test + Cleanup

**Files:**
- All files from Tasks 1-5

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/unit/test_model_registry.py tests/unit/test_config_cmd.py -v`
Expected: ALL PASS

- [ ] **Step 2: Ruff format + lint**

Run: `ruff format src/cognithor/cli/ tests/unit/test_config_cmd.py tests/unit/test_model_registry.py`
Run: `ruff check src/ tests/ --select=F821,F811 --no-fix`
Expected: All checks passed

- [ ] **Step 3: Verify all 3 CLI modes work**

```bash
# Interactive (just verify it launches without crash — Ctrl+C to exit)
python -m cognithor config

# Non-interactive
python -m cognithor config list
python -m cognithor config get language
python -m cognithor config set owner_name "Test"
python -m cognithor config get owner_name  # Should print "Test"
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete cognithor config CLI TUI (#95)

Interactive config menu with dynamic model discovery from Ollama,
OpenAI, Anthropic, Gemini, LM Studio. Non-interactive get/set/list.
Cached model registry with weekly CI updates.

Closes #95"
```
