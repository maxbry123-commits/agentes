# Port Setup Wizard UI from Python to Rust

## Overview

The Rust setup wizard (`opendev-rust/crates/opendev-cli/src/setup/`) is currently a bare-bones `println!`-based CLI with numbered menus. The Python version (`opendev/setup/`) has a rich interactive experience with railway/clack-style rendering, arrow-key navigation, search filtering, and a 9-step multi-slot model configuration flow. This document describes the plan to port the full Python wizard to Rust.

## Current State

### Python (source of truth)
- `wizard.py` — 9-step wizard flow: intro → provider → key → validate → model → thinking slot → critique slot → vision slot → compact slot → summary + save
- `wizard_ui.py` — Rail rendering primitives (`rail_intro`, `rail_step`, `rail_info_box`, `rail_confirm`, `rail_prompt`, `rail_summary_box`, etc.) using Rich console markup
- `interactive_menu.py` — `InteractiveMenu` class with arrow-key navigation, `/` search, scroll window, `❯` pointer, blue highlight on active row
- `providers.py` — Dynamic provider/model lookup via `ModelRegistry` (loaded from `~/.opendev/cache/providers/*.json`)

### Rust (current, to be rewritten)
- `mod.rs` — 5-step wizard (no thinking/critique/vision/compact slots), uses `println!` + numbered selection (`read_selection`)
- `providers.rs` — Hardcoded `all_providers()` with 5 providers and static model lists (does NOT use `ModelRegistry`)

## Files to Change

| Action | Path | Description |
|--------|------|-------------|
| Edit | `opendev-rust/crates/opendev-cli/Cargo.toml` | Add `crossterm = { workspace = true }` dep |
| New | `opendev-rust/crates/opendev-cli/src/setup/rail_ui.rs` | Rail rendering primitives |
| New | `opendev-rust/crates/opendev-cli/src/setup/interactive_menu.rs` | Arrow-key interactive menu |
| Rewrite | `opendev-rust/crates/opendev-cli/src/setup/providers.rs` | Use `ModelRegistry` instead of hardcoded list |
| Rewrite | `opendev-rust/crates/opendev-cli/src/setup/mod.rs` | Full 9-step wizard flow |

## Step-by-Step Plan

### Step 1: Add crossterm dependency

Add `crossterm = { workspace = true }` to `opendev-cli/Cargo.toml` under `[dependencies]`. Already in workspace `Cargo.toml` as `crossterm = { version = "0.28", features = ["event-stream"] }`.

### Step 2: Create `rail_ui.rs` — Rail rendering primitives

Port all functions from `wizard_ui.py` using crossterm for direct ANSI color output (no Rich dependency).

Constants to define:
- `ACCENT` = `#82a0ff` (RGB: 130, 160, 255)
- `SUCCESS` = green
- `ERROR` = red
- `WARNING` = yellow
- Box-drawing chars: `┌ │ ├ ◇ └ ─ ╮ ╯`

Functions to port (all write directly to stdout):

| Python function | Rust function | Behavior |
|----------------|---------------|----------|
| `rail_intro(title, lines)` | `rail_intro(title, lines)` | `┌  Title` + `│` lines |
| `rail_outro(message)` | `rail_outro(message)` | `└  Message` |
| `rail_step(title, step_label?)` | `rail_step(title, step_label)` | `◇  Title ── Step N of M` |
| `rail_info_box(title, lines, step_label?)` | `rail_info_box(title, lines, step_label)` | Box with `◇` top, `├───╯` bottom, `│` sides |
| `rail_answer(value)` | `rail_answer(value)` | `│  value` |
| `rail_success(msg)` | `rail_success(msg)` | `│  ✓ msg` in green |
| `rail_error(msg)` | `rail_error(msg)` | `│  ✖ msg` in red |
| `rail_warning(msg)` | `rail_warning(msg)` | `│  ⚠ msg` in yellow |
| `rail_separator()` | `rail_separator()` | `│` blank line |
| `rail_confirm(prompt, default)` | `rail_confirm(prompt, default) -> bool` | `◇  Prompt (Y/n)` + read line |
| `rail_prompt(text, password)` | `rail_prompt(text, password) -> String` | Text input, password hides chars |
| `rail_summary_box(title, rows, extra)` | `rail_summary_box(title, rows, extra)` | Delegates to `rail_info_box` with formatted rows |

Implementation approach:
- Use `crossterm::style::{SetForegroundColor, Color, ResetColor}` for coloring
- Write directly to `io::stdout()` with `write!`/`writeln!`
- For password input: use `crossterm::terminal::disable_raw_mode` / `enable_raw_mode` to suppress echo, or just read chars silently
- Terminal width: use `crossterm::terminal::size()` for `rail_info_box` width calculation

### Step 3: Create `interactive_menu.rs` — Arrow-key menu

Port `InteractiveMenu` from `interactive_menu.py`.

```
InteractiveMenu {
    all_items: Vec<(String, String, String)>,  // (id, name, description)
    filtered_items: Vec<(String, String, String)>,
    title: String,
    window_size: usize,
    selected_index: usize,
    search_query: String,
    search_mode: bool,
}
```

Key behaviors to port:
- **Arrow key navigation**: Up/Down arrows move selection (wraps around)
- **Search mode**: Press `/` to enter, Escape to exit; filters items by name/description
- **Scroll window**: Only `window_size` items visible at once, centered on selection
- **Visual styling**:
  - Active row: `❯` pointer + bold white on `#1f2d3a` background + hint text on same bg
  - Inactive row: white name, dim `#7a8691` description
  - Rail bar `│` prefix on every line (in ACCENT color)
  - `... (N more above/below)` scroll indicators
- **Footer**: Item count + "↑/↓ · / search" hint (only for large menus)
- **Key handling**: Enter = select, Escape = cancel, Ctrl+C = cancel

Implementation approach:
- Use `crossterm::terminal::{enable_raw_mode, disable_raw_mode}` for raw key reading
- Use `crossterm::event::{read, Event, KeyEvent, KeyCode}` for key events
- Use `crossterm::cursor::{Hide, Show, MoveUp}` + `crossterm::terminal::Clear` for re-rendering
- Return `Option<String>` (selected item ID or None)

### Step 4: Rewrite `providers.rs` — Use ModelRegistry

Replace the hardcoded `all_providers()` function with dynamic loading from `ModelRegistry`.

Current approach:
```rust
fn all_providers() -> Vec<ProviderConfig> { vec![...hardcoded...] }
```

New approach:
```rust
use opendev_config::{ModelRegistry, Paths};

impl ProviderSetup {
    pub fn provider_choices() -> Vec<(String, String, String)> {
        let paths = Paths::default();
        let registry = ModelRegistry::load_from_cache(&paths.cache_dir());
        registry.list_providers()
            .iter()
            .map(|p| (p.id.clone(), p.name.clone(), p.description.clone()))
            .collect()
    }

    pub fn get_provider_config(id: &str) -> Option<ProviderConfig> {
        let paths = Paths::default();
        let registry = ModelRegistry::load_from_cache(&paths.cache_dir());
        let provider = registry.get_provider(id)?;
        Some(ProviderConfig {
            id: provider.id.clone(),
            name: provider.name.clone(),
            description: provider.description.clone(),
            env_var: provider.api_key_env.clone(),
            api_base_url: provider.api_base_url.clone(),
            api_format: if id == "anthropic" { ApiFormat::Anthropic } else { ApiFormat::OpenAi },
            models: provider.list_models(None)
                .iter()
                .map(|m| (m.id.clone(), format!("{} — {}", m.name, m.format_pricing())))
                .collect(),
        })
    }
}
```

Keep:
- `ProviderConfig` struct (still useful for wizard's internal representation)
- `ApiFormat` enum
- `ValidationError` and `validate_api_key`, `validate_openai_key`, `validate_anthropic_key` functions (unchanged)
- All existing tests (update to work with dynamic data)

### Step 5: Rewrite `mod.rs` — Full 9-step wizard

Port the complete `wizard.py` flow. The current Rust wizard has 5 steps; the Python version has 9.

#### Flow (matching Python exactly):

1. **Intro** — `rail_intro("Welcome to OpenDev!", [...])`
2. **Step 1: Select Provider** — `select_provider()` using `InteractiveMenu`
3. **Step 2: API Key** — `get_api_key()` with env detection + `rail_prompt(password=true)`
4. **Step 3: Validate** — `rail_confirm("Validate API key?")` → `validate_api_key()`
5. **Step 4: Select Model** — `select_model()` using `InteractiveMenu` with "Custom Model" option
6. **Step 5: Vision Model** — `configure_slot("Vision", "image & screenshot analysis")`
7. **Step 6: Compact Model** — `configure_slot("Compact", "context summarization")` (stored in `agents.compact`)
8. **Step 7: Summary + Save** — `show_config_summary()` + `rail_confirm("Save?")` + `save_config()`

> **Note:** The Critique model slot was removed — it was dead code never consumed by any runtime path.

#### New function: `configure_slot_model()`

Port from Python. Shows a 2-item `InteractiveMenu`:
- "Use {model_name}" — reuse the normal model
- "Choose manually" — full provider → key → model flow

Returns `(provider_id, model_id)`.

Tracks `collected_keys: HashMap<String, String>` to avoid re-prompting for already-collected API keys (same as Python).

#### Config building

Build `AppConfig` with slot fields:
```rust
config.model_vlm = Some(vlm_model);
config.model_vlm_provider = Some(vlm_provider);
// Compact stored via agents map:
config.agents.insert("compact", AgentConfigInline { model, provider, .. });
```

#### Summary display

Port `show_config_summary()` from Python. Uses `rail_summary_box` with rows:
- Normal: {provider} / {model}
- Vision: (same as Normal) or {provider} / {model}
- Compact: (same as Normal) or {provider} / {model}
- API Keys section: list env vars with ✓/set status

### Step 6: Update `mod.rs` module declarations

Add module declarations for new files:
```rust
pub mod providers;
pub mod rail_ui;
pub mod interactive_menu;
```

## Key Differences from Python

- **No Rich library**: Use crossterm directly for ANSI colors and terminal control
- **No `getpass`**: Use crossterm raw mode to read password chars without echo
- **Terminal width**: `crossterm::terminal::size()` instead of `Console().width`
- **Key reading**: `crossterm::event::read()` instead of `tty.setraw()` + `sys.stdin.read()`
- **Error handling**: Return `Result<_, SetupError>` instead of returning `None`/`False`

## Verification Plan

1. `cargo build --release -p opendev-cli` — must compile cleanly
2. `rm -rf ~/.opendev && opendev` — should launch rail-style wizard with interactive menus
3. Walk through all 9 steps — verify each slot menu works, search filters, arrow keys navigate
4. Verify summary shows correct "same as Normal/Thinking" labels
5. Confirm save writes correct `settings.json` with all slot fields
6. `cargo test -p opendev-cli` — all existing + new tests pass

## Dependencies

- `crossterm` — already in workspace (`version = "0.28", features = ["event-stream"]`)
- `opendev-config` — already a dependency of `opendev-cli` (provides `ModelRegistry`, `Paths`)
- `opendev-models` — already a dependency (provides `AppConfig`)
