---
name: analyze-dataset-token-length
description: >-
  Analyze the token length of an OT-Agent conversation-format (ShareGPT-style) dataset —
  the per-trace distribution (median/p90/max) and/or counts under a token threshold + a
  metadata predicate (e.g. "task_complete AND < 32768 tokens"). Use when asked how long
  traces are, how many fit a context window (32k/131k), or to filter a trace dataset by
  length + a field. Uses the OT-Agent analysis tools + the Qwen3-8B tokenizer. Runs LOCALLY
  on the Mac (no GPU); full-dataset tokenization of ~10k multi-turn traces takes a few
  minutes → run it in the background.
---

# analyze-dataset-token-length

OT-Agent trace datasets are **conversation-format** (ShareGPT-style): each row is
`{"conversations": [{"role","content"}, …], + metadata}` (some use `"messages"`; metadata
fields are e.g. `task`, `result`, `run_id`, `trial_name`, `model`, `agent`). "Token length
of a trace" = the tokenized length of the *whole* conversation.

## The canonical OT-Agent tools (don't reinvent)
- **`scripts/analysis/utils.py`** — canonical pure conversation/token helpers:
  `extract_conversation_text(record)`, `render_token_representation(...)`, and
  `count_conversation_tokens(...)`. Every count must explicitly select
  `serialized`, `conversation_text`, or `chat_template`; these are different
  measurements and must never be silently substituted for one another.
- **`scripts/analysis/context_length_compare.py`** — cross-dataset context-length comparison.

## Tokenizer convention
**Always Qwen/Qwen3-8B** (`AutoTokenizer.from_pretrained("Qwen/Qwen3-8B", trust_remote_code=True)`).
Our trace datasets are Qwen3-8B-tokenized even when named for GLM/Kimi/etc. — those "GLM-4.7-…"
models are Qwen3-8B SFTs (see memory `reference_glm47_swesmith_is_qwen3_8b`); the *served* model
name in a row's `model` field (e.g. `hosted_vllm/<numeric-id>`) is NOT a usable tokenizer name.

## Three token-count representations — pick by the question
- **conversation_text** = `tokenizer(extract_conversation_text(row), add_special_tokens=False)` — fast;
  slightly **under**-counts vs training (no chat-template tokens).
  Right for distribution/relative comparisons.
- **chat_template** = `len(tokenizer.apply_chat_template(conv, tokenize=True, add_generation_prompt=False))`
  — what an SFT trainer actually tokenizes; use when the question is **"does it fit a 32k/131k
  training window."** If a trace's role shape makes the template raise, report it as
  uncountable for this representation and tally it separately; do not substitute a
  plain-text count.
- ⚠️ **The two can differ by MORE than the wrapper tokens — and in the surprising direction.**
  Qwen3's chat template **strips historical `<think>` blocks** from earlier assistant turns, so on
  thinking-mode traces `apply_chat_template` can count **fewer** tokens than plain-concat (which keeps
  all thinking) — i.e. *more* traces "fit" under the template. So the "right" count for a `< N` filter
  depends on **whether your SFT template preserves thinking**: default Qwen3 (strips) → optimistic
  count; a thinking-preserving template (`qwen3_thinking_acc.jinja2`) → conservative count ≈ plain.
  Report BOTH and pick by the training template; for a safe "fits 32k" answer use the larger (plain /
  thinking-preserving) count.
- **serialized** = compact JSON of the raw `conversations` value, including role
  fields and JSON punctuation. This is the legacy datagen-counter measurement;
  it is useful for continuity but is neither plain text nor training-faithful.

## Threshold + metadata filter-count (the common ask)
Recipe: `load_dataset` (non-streaming) → per row compute (a) the token count and (b) a metadata
predicate → count the intersection; report each leg separately so it's auditable.

### ⚠️ The metadata-confound trap (read this before any field predicate)
Instruction text leaks into the trace. Fields like **`task_complete`** appear *verbatim in the user
instruction of EVERY trace* (`…include "task_complete": true in your response…`), so a naive
`'"task_complete": true' in full_text` matches **all** rows (false 100%). **Scope the predicate to the
agent's actual emission** — i.e. an **assistant-role** message containing the field, not the prompt:
```python
def agent_complete(conv):
    return any(m.get("role") == "assistant" and '"task_complete": true' in (m.get("content") or "")
               for m in conv)
```
**Always sanity-check the predicate VARIES** (not all-true / all-false) before trusting a count — print
the per-leg breakdown and an early per-1000-row progress line. (Same caution for any tool-name /
status substring: confirm you're matching the agent's output, not the system/user scaffolding.)

## How to run
Local, otagent python, HF token sourced; full-dataset tokenization of ~10k multi-turn traces is a
few minutes → background it:
```bash
source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python scripts/analysis/<script>.py   # run_in_background
```
First run downloads + caches the parquet (~hundreds of MB). A benign `'NoneType' has no attribute
'ArrowInvalid'` on streaming-generator teardown can be ignored (use non-streaming `load_dataset` anyway).

## Worked example — swesmith, "task_complete AND < 32768 tok"
`DCAgent2/GLM-4.7-swesmith-sandboxes-with_tests-oracle_verified_120s-maxeps-131k` (9437 traces):
detect completion via the **assistant-scoped** `"task_complete": true` (not the instruction prose),
count tokens via `apply_chat_template` (Qwen3-8B), filter `complete AND ct < 32768`. Reports three
legs — #complete, #<32k, and the intersection — so the filter is auditable. (Early progress
`1000/9437: complete=924 / fit32k=886 / both=854` confirmed the predicate varies ≈92%, i.e. the
confound was correctly excluded.)
