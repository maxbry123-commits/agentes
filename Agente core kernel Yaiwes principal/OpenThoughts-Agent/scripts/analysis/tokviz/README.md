# tokviz — exact tokenizer-input visualizer for small Qwen 3.5

This tool produces self-contained, pretty-printed **HTML** files that show, for a
small Qwen 3.5 model, the **exact literal string the tokenizer feeds the model**
at generation time — with special tokens highlighted and every whitespace /
control / byte-level character rendered with a visible glyph — plus the model's
**actual generated response** appended.

There are two halves:

* **Chat / non-agentic** (`run_chat.py`): 5 hardcoded prompts × {instruct, base}
  via pure HF `transformers` (no server). 10 HTML files. The instruct path now
  applies the chat template with **`enable_thinking=True`** (see below).
* **Agentic** (`run_agentic.py`): 5 toy local git-repo bug-fix tasks driven by
  **SWE-agent**, which talks to a minimal OpenAI-compatible FastAPI shim
  (`serve_hf_openai.py`) wrapping the same HF model. The shim logs every
  fully-templated prompt; the FIRST model call of each task (the one carrying
  both the tool docs and the issue) is rendered to HTML. The agentic half runs
  in **two parser variants** side by side — `thought_action` (text commands)
  and `function_calling` (structured `<tools>` array) — see below.

## Thinking mode (`enable_thinking=True`)

Qwen3.5's chat template defaults to **thinking-OFF**: with no `enable_thinking`
kwarg it emits an empty, pre-closed think block
(`<|im_start|>assistant\n<think>\n\n</think>\n\n`). With `enable_thinking=True`
the generation-prompt tail instead ends with an **OPEN** `<think>\n`, so the
model generates real reasoning inside `<think>…</think>` before its answer.

Every place the chat template is applied to the **instruct** model now passes
`enable_thinking=True`:

* `model_utils.py:chat_templated_string` (the chat half).
* `serve_hf_openai.py` (the agentic half / shim). The shim's `_template()`
  helper passes `enable_thinking=True` and **falls back gracefully** (omits the
  kwarg) if a tokenizer's template doesn't accept it — verified to work for both
  the instruct and base Qwen3.5 tokenizers.

The **base** chat half (`run_chat.py:run_base`) feeds a raw completion with no
template and is left unchanged.

Because thinking output is longer, the instruct chat path uses a larger bounded
generation budget: `config.MAX_NEW_TOKENS_INSTRUCT` (default **2048**, overridable
via `TOKVIZ_MAX_NEW_TOKENS_INSTRUCT`). The shim caps generation at this same
bound regardless of the client's requested `max_tokens`.

## Stop token (`eos_token_id`) — why it must be explicit

Both `model.generate()` call sites (`model_utils.py:generate_from_ids` for the
chat half, and the `/v1/chat/completions` handler in `serve_hf_openai.py` for the
agentic half) pass an **explicit `eos_token_id` stop-token *set*** via the shared
helper `model_utils.py:stop_ids(tok)`.

This is required because **`model.generate()` does NOT use
`tokenizer.eos_token_id`** to decide when to stop — it uses the eos from the
**generation config / `model.config`**. **Qwen3.5-2B ships no
`generation_config.json`**, and its `model.config.eos_token_id` is `None`. So
with no explicit `eos_token_id` argument, generation has *no* stop token at all:
the model correctly emits `<|im_end|>` (token **248046**) to end its turn, but
`generate()` ignores it and keeps going until `max_new_tokens`, **hallucinating
the rest of the conversation** — e.g. a fabricated `<tool_response>` block faking
the environment's reply, followed by a second `<tool_call>` (its own next turn).

`stop_ids(tok)` builds the stop set robustly from the tokenizer:

* `<|im_end|>` (248046) and `<|endoftext|>` (248044), looked up explicitly and
  added only when present (not the unk id);
* plus the tokenizer's own `tok.eos_token_id` (248046 for this tokenizer);
* de-duplicated and sorted → `[248044, 248046]`.

Passing this set as `eos_token_id=` makes `<|im_end|>` actually halt generation.
`pad_token_id` is left unchanged. A record that legitimately never emits a stop
token within `MAX_NEW_TOKENS_INSTRUCT` (e.g. a very long thinking trace) still
hits the cap — that is expected and is distinct from the pre-fix bug, where
*every* turn-ending response ran past `<|im_end|>` into a hallucinated next turn.

## Two agentic parser variants

The agentic half drives SWE-agent over the 5 toy repos in **both** parser
modes, for instruct and base:

* **`thought_action`** — tools are documented as **TEXT** under `COMMANDS:` in
  the system prompt (via `{{command_docs}}`); **no structured tool array** is
  sent. Bundled config: `07_thought_action.yaml`. Output files keep their
  existing names: `agentic_NN_<variant>.html`.
* **`function_calling`** — tools are sent as a **structured tool array** (OpenAI
  function schema). Qwen3.5's chat template renders them into a
  `<tools>…</tools>` JSON block in the system message — the point of this
  variant. Bundled config: `07_fcalling.yaml`. Output files get a `_funccall`
  suffix: `agentic_NN_<variant>_funccall.html`.

Both bundled configs wire the **same** tool bundles
(`registry`/`windowed`/`search`/`windowed_edit_linting`/`submit`); they differ
only in `parse_function.type` and how the tools reach the model. The
small-model `sweagent_config.yaml` override is layered on **both** and does NOT
set `parse_function`, so each variant keeps its own parser.

### Shim tool passthrough

`serve_hf_openai.py`'s request model accepts an optional `tools` field. When
present (the function_calling variant), it is forwarded to
`apply_chat_template(messages, tools=tools, add_generation_prompt=True,
tokenize=False, enable_thinking=True)` so the `<tools>` block is rendered into
the captured prompt. The shim logs the exact templated prompt (with the tools
block) **on receipt / in a `finally`** before/around generation, so a downstream
SWE-agent parse failure can never prevent the prompt from being captured. The
shim returns a well-formed OpenAI response with plain `content` (it does not
emit real `tool_calls` — a 2B model can't, and we only care about the PROMPT).

## Output location

All generated HTML (chat + agentic) is written to:

```
/Users/benjaminfeuer/Documents/foundation_models/Qwen/qwen3_5_literals/output
```

This is the default `OUTPUT_DIR` in `config.py` (the scripts themselves live
under `scripts/analysis/tokviz/`, but outputs go to the foundation_models path).
Override with the `TOKVIZ_OUTPUT_DIR` env var. The dir is created if missing and
existing files there are overwritten on a normal run.

## SWE-agent config (the agentic prompt fix)

The agentic prompt is built by **layering two `--config` files that merge in
order** (later wins), rather than a hand-rolled terse template:

```
# thought_action variant:
sweagent run \
  --config <SWE-agent>/config/sweagent_0_7/07_thought_action.yaml \
  --config <tokviz>/sweagent_config.yaml \
  ...
# function_calling variant:
sweagent run \
  --config <SWE-agent>/config/sweagent_0_7/07_fcalling.yaml \
  --config <tokviz>/sweagent_config.yaml \
  ...
```

* `07_thought_action.yaml` / `07_fcalling.yaml` are SWE-agent's **bundled**
  configs for the two parser variants. Both wire everything a real run needs:
  the tool bundles (`tools/registry`, `tools/windowed`, `tools/search`,
  `tools/windowed_edit_linting`, `tools/submit`), a system/instance template
  pair carrying the issue from `--problem_statement.path=<repo>/ISSUE.md`. They
  differ only in `parse_function.type`: `thought_action` documents the tools as
  text via `{{command_docs}}`; `function_calling` sends a structured tool array
  that Qwen3.5's template renders as a `<tools>` JSON block.
* `sweagent_config.yaml` is now a **small-model override only**: it points the
  model at the local shim, zeroes the cost/length limits, bounds
  `per_instance_call_limit`, and disables the bundled marshmallow
  demonstration + history rewriting so the first captured call is a clean
  (system + instance) prompt.

`run_agentic.py` sets `SWE_AGENT_CONFIG_ROOT=<SWE-agent>` so the bundle paths
(`tools/...`) resolve regardless of CWD.

> **Earlier bug (fixed):** the old `sweagent_config.yaml` hand-rolled a terse
> `system_template` with no `{{command_docs}}` and no instance template, so the
> captured prompts had an **empty user turn** (no issue) and **no tool docs**.
> The model received essentially no task. Basing on the bundled thought_action
> config restores both.

### Capture verification (assertion before rendering)

After running SWE-agent and **before** rendering, `run_agentic.py:verify_capture()`
checks `shim_prompts.jsonl` against three gates and **raises with a dump of the
actual captured prompt** (rather than rendering stale/empty HTML) on any failure:

* **GATE A (thinking):** at least one INSTRUCT captured prompt's tail has an
  OPEN `<think>\n` block (no `</think>` follows) — confirms
  `enable_thinking=True` took effect.
* **GATE B (thought_action):** per variant, ≥1 captured `has_tools=False` prompt
  contains the `COMMANDS` tool docs + the issue text AND has **no** `<tools>`
  array (text-only form).
* **GATE B (function_calling):** per variant, ≥1 captured `has_tools=True`
  prompt contains a `<tools>` JSON block + the issue text.

The shim's `has_tools` flag on each logged record is the discriminator between
the two parser variants. The renderer then picks the **first model call** of
each task per (variant, parser) so the visualized prompt always carries the
tools + issue.

> **Fallback:** if `base` + `function_calling` produces no captured records,
> the verifier emits a WARNING (not a failure) and that bucket is skipped —
> instruct-only function_calling is an acceptable fallback.

## Models (verified on HF Hub, 2026-05-27)

| Role     | Model ID                  | Status |
|----------|---------------------------|--------|
| Instruct | `Qwen/Qwen3.5-2B`         | exists, used |
| Base     | `Qwen/Qwen3.5-2B-Base`    | exists, used |

**No model substitution was needed** — both requested IDs resolve and are used
as-is. They are defined as constants at the top of `config.py`
(`INSTRUCT_MODEL_ID`, `BASE_MODEL_ID`) and overridable via the
`TOKVIZ_INSTRUCT_MODEL` / `TOKVIZ_BASE_MODEL` env vars.

> Note: Qwen3.5 weights use the `qwen3_5` architecture, which requires
> `transformers >= 5`. See the **Conda environments** section — this is why
> model execution uses a dedicated `tokviz-rt` env rather than `otagent`.

## Conda environments (STRICT separation)

| Env         | Interpreter | Purpose |
|-------------|-------------|---------|
| `otagent`   | `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python` | The pinned project env (transformers 4.57.3). It loads the Qwen3.5 **tokenizer** fine and runs all the rendering/orchestration code, but its `transformers` is too old to run the Qwen3.5 **weights**. It is **left untouched** to protect Harbor/SkyRL pins. |
| `tokviz-rt` | `/Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python` | Dedicated model-runtime env (python 3.11, `transformers 5.9`, torch). Runs the actual `model.generate` for the Qwen3.5 weights and the OpenAI shim. Use this interpreter to run the model-executing scripts. |
| `sweagent`  | `/Users/benjaminfeuer/miniconda3/envs/sweagent/bin/sweagent` | Standalone SWE-agent install (python 3.11), created by `setup_sweagent.sh`. **Never** installed into otagent. |

Rationale for `tokviz-rt`: the spec mandates the main script runs in otagent, but
otagent's `transformers` (4.57.3) does not recognize the `qwen3_5` architecture,
so it cannot run the requested Qwen3.5 weights. Upgrading otagent would risk the
user's pinned Harbor/SkyRL workflow. The split mirrors the mandated swe-agent
env separation: rendering/orchestration is env-agnostic; only weight execution
needs the newer env.

## How to run

### Chat half (produces 10 HTML files)
```bash
cd scripts/analysis/tokviz
/Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python run_chat.py
```

### Agentic half
1. Install SWE-agent once (own env, from source):
   ```bash
   bash setup_sweagent.sh
   ```
2. Create the toy repos (also done automatically by `run_all.py`):
   ```bash
   /Users/benjaminfeuer/miniconda3/envs/otagent/bin/python make_repos.py
   ```
3. Drive shim + swe-agent + render:
   ```bash
   /Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python run_agentic.py
   ```

### Everything
```bash
/Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python run_all.py
```

### Run the shim standalone (for manual swe-agent runs)
```bash
# instruct:
/Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python serve_hf_openai.py --model instruct --port 8123
# base:
/Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python serve_hf_openai.py --model base --port 8123
```
Then point SWE-agent at it by layering the override on the bundled config (the
override sets `api_base: http://localhost:8123/v1`, `api_key: dummy`):
```bash
SWE_AGENT_CONFIG_ROOT=/Users/benjaminfeuer/SWE-agent \
/Users/benjaminfeuer/miniconda3/envs/sweagent/bin/sweagent run \
  --config /Users/benjaminfeuer/SWE-agent/config/sweagent_0_7/07_thought_action.yaml \
  --config sweagent_config.yaml \
  --agent.model.name openai/Qwen/Qwen3.5-2B \
  --problem_statement.path=repos/offbyone/ISSUE.md \
  --env.repo.path=repos/offbyone
```

## Docker dependency (agentic half)

SWE-agent's **default execution backend is Docker**. `run_agentic.py` checks
`docker info`; if Docker is unavailable it **skips** the swe-agent invocations
and prints the exact manual commands instead — the shim + render pipeline still
run. On the build machine Docker was available and running.

## Files

| File | Role |
|------|------|
| `config.py` | Model IDs (constants), paths, generation settings, the 5 chat prompts. |
| `render_tokens.py` | **The heart.** text/ids + tokenizer → standalone HTML token visualization. |
| `model_utils.py` | Shared HF load + greedy generate + chat-template helpers. |
| `run_chat.py` | Chat half: 5 prompts × {instruct, base} → 10 HTML. |
| `serve_hf_openai.py` | Minimal OpenAI-compatible FastAPI shim; applies the template with `enable_thinking=True` + optional `tools` passthrough; logs every templated prompt (with any `<tools>` block) to `shim_prompts.jsonl`, including a `has_tools` flag. |
| `make_repos.py` | Creates 5 tiny local git repos with hand-written bugs + `ISSUE.md`. |
| `sweagent_config.yaml` | SWE-agent **small-model override** layered on top of **both** bundled configs (`07_thought_action.yaml` and `07_fcalling.yaml`): model→shim, zeroed cost/length limits, bounded call limit, demonstrations + history processors disabled. It does NOT set `parse_function`, so each variant keeps its own parser. |
| `setup_sweagent.sh` | Installs SWE-agent from source into the standalone `sweagent` env. |
| `run_agentic.py` | Starts shim, runs swe-agent on the 5 repos for both models, renders captured prompts. |
| `render_agentic.py` | Renders captured shim-log records into `agentic_*.html`. |
| `run_all.py` | Orchestrator: chat half → repos → agentic half. |

## Output files (in `OUTPUT_DIR`, see "Output location" above)

* `chat_NN_instruct.html` — instruct model, chat template applied
  (`apply_chat_template(add_generation_prompt=True, enable_thinking=True)`),
  prompt (OPEN `<think>` tail) + generated reasoning + answer.
* `chat_NN_base.html` — base model, **no chat template**, raw completion prompt +
  generated continuation.
* `agentic_NN_instruct.html` / `agentic_NN_base.html` — **thought_action**
  variant: a representative SWE-agent step's exact templated prompt (tools as
  text under `COMMANDS:`) + that step's response.
* `agentic_NN_instruct_funccall.html` / `agentic_NN_base_funccall.html` —
  **function_calling** variant: same step but with the tools rendered as a
  `<tools>` JSON array in the system message. (base+funccall may be absent if
  that bucket produced no captures — acceptable fallback.)

## Reading an HTML file

Each token is a bordered badge with alternating shading so boundaries are
obvious. Hover any badge to see its **token id** and **raw piece repr**.

* **Orange/bold badge** = special/added token (`<|im_start|>`, `<|im_end|>`,
  `<|endoftext|>`, …), labeled with its id.
* **`·` `→` `↵`** = space / tab / newline.
* **`\xHH`** (purple) = a raw or non-UTF8 byte (byte-fallback token, or a token
  that is a fragment of a multibyte UTF-8 character).
* **Dashed border / green header** = the model's generated continuation, visually
  separated from the prompt.

Byte-level BPE artifacts (`Ġ`, `Ċ`, `Â`/`Ã` noise) are decoded back to real
characters per token via `convert_tokens_to_string`, with a GPT-2 byte-decoder
fallback for fragments — so what you see is the true text, not the sentinel
alphabet.
