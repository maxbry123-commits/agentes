# i18n Language Fix — Full Design

**Issue:** #109 — Windows EXE install with English selected still replies in German
**Date:** 2026-04-12

## Root Cause

Language is selected in `first_run.py` and written to `config.yaml`, but:

1. `agents.yaml.default` hardcodes `language: de` on all 6 agents
2. Planner `SYSTEM_PROMPT` is hardcoded German text
3. `_build_formulate_messages` hardcodes German prompts ("Antworte auf Deutsch")
4. Voice STT modules hardcode `language="de"`
5. Agent `language` field exists but is never used when building prompts

Even though `prompt_presets.py` has English variants available, they are only partially wired in.

## Fix Strategy

**Single source of truth:** `config.language` — set at first run, read everywhere.

### 1. first_run.py
- When user selects a language, write it to BOTH `config.yaml` AND update `agents.yaml` agents' `language` field
- Also replace the system prompt of the main agent with the matching locale

### 2. config.py
- Keep default `"de"` (to not break existing installs) — but add a migration that reads selected language from marker

### 3. planner.py SYSTEM_PROMPT
- Check `self._config.language` first
- Look up `prompt_presets[language]["plannerSystem"]`
- Fall back to German if language not in presets
- Already half-implemented in `_load_prompt_from_file` — just needs wiring

### 4. _build_formulate_messages
- Extract German strings into locale-aware dict
- Key off `self._config.language`
- Both "direct answer" and "search result summarization" prompts

### 5. Voice STT channels
- Read `config.language` as STT default
- Voice channels get a `language` config param

### 6. agents.yaml loader
- When loading, if `language` field is missing → use `config.language`
- Add post-load sync: if `config.language` changed, update in-memory agent profiles

### 7. Chat UI
- Language selector in config TUI / Flutter Settings to change language after install
- Writing to `config.yaml` triggers reload

## Files to Modify

| File | Change |
|------|--------|
| `installer/first_run.py` | Also update agents.yaml language on first run |
| `installer/agents.yaml.default` | Remove hardcoded `language: de`, use `{{config.language}}` placeholder resolved by first_run |
| `src/cognithor/core/planner.py` | SYSTEM_PROMPT lookup via preset, `_build_formulate_messages` locale-aware |
| `src/cognithor/i18n/prompt_presets.py` | Add English presets for `formulate_direct`, `formulate_search`, `formulate_system` |
| `src/cognithor/channels/voice.py` | Accept `language` from config |
| `src/cognithor/channels/voice_ws_bridge.py` | Same |
| `src/cognithor/channels/telegram.py` | Same |
| `src/cognithor/channels/signal.py` | Same |

## Non-goals

- Not refactoring the entire i18n system
- Not adding new languages (zh, ar stubs remain)
- Not changing how `config.yaml` stores the value
