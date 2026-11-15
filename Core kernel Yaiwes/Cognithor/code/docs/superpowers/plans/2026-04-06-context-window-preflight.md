# Context-Window Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent oversized LLM requests by checking estimated token count against context window before every API call, with auto-compaction and user notification.

**Architecture:** Single new module `core/preflight.py` with integration into `UnifiedLLMClient.chat()` and PGE loop error handling.

**Tech Stack:** Python 3.12+, dataclasses, json, pytest

---

### Task 1: Create preflight module

**Files:**
- Create: `src/jarvis/core/preflight.py`
- Test: `tests/test_preflight.py`

- [ ] **Step 1: Create `src/jarvis/core/preflight.py`**

- [ ] **Step 2: Create `tests/test_preflight.py`**

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_preflight.py -v`

- [ ] **Step 4: Commit**

### Task 2: Integrate into UnifiedLLMClient

**Files:**
- Modify: `src/jarvis/core/unified_llm.py`

- [ ] **Step 1: Add preflight call in `chat()` method**

- [ ] **Step 2: Commit**

### Task 3: Add i18n keys

**Files:**
- Modify: `src/jarvis/i18n/locales/en.json`
- Modify: `src/jarvis/i18n/locales/de.json`

- [ ] **Step 1: Add context_window_exceeded error messages**

- [ ] **Step 2: Commit**
