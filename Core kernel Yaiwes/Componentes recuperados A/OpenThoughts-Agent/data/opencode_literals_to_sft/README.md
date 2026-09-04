# opencode literals → TRAIN==SERVE SFT dataset

Reusable data-preprocessing for turning an **opencode agentic-trace dataset** (Harbor datagen
output) into an SFT dataset that is **structurally byte-identical to what the model is served
under at eval/RL** — the fix for the recurring train/serve data-format bug class (bug ledger #2
in the densemixer A/B SFT experiment).

Home of the load-bearing preprocessing code for
`experiments/active/axolotl-sft-opencode-densemoe/` (see that experiment's `REPRO.md` for the
full end-to-end reproduction formula). Re-homed from
Use `python -m data.opencode_literals_to_sft` for this conversion.

---

## The problem this solves

Harbor opencode trace datasets (e.g.
`penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces`) store a **lossy
`conversations` field**:

- no `system` message; an empty turn-0; **no `<tools>` block**,
- assistant tool calls flattened to **inline `<tool_call>{…}` text**,
- tool results as **`role: user`** (not `role: tool`).

A model SFT'd on that field never learns to condition on a task, a `<tools>` system block, or
the opencode read/edit workflow — it defaults to reflexive bash and scores ~0 on agentic evals.

The full served prompt **survives in the literal token columns** `prompt_token_ids` /
`completion_token_ids`. This tool reconstructs each row from those columns into a serve-shaped
SFT example.

## What it emits

One row per convertible trace, with an explicit (Arrow-safe) schema:

| column | shape | notes |
|---|---|---|
| `messages` | `list[{role, content, tool_calls}]` | `system` = opencode agent prompt (teacher tool-boilerplate stripped at `</IMPORTANT>`); task-grounded `user` turn-0; **structured** assistant `tool_calls` `[{type, function:{name, arguments}}]` with verbatim `<think>` kept as `content`; `role: tool` observations |
| `tools` | JSON string | the 10 opencode function schemas (bash/edit/glob/grep/read/skill/task/todowrite/webfetch/write); renders the `<tools>` system block at train time |
| `task`, `num_turns`, `num_tool_calls` | scalars | bookkeeping |

`tool_calls.function.arguments` is a **JSON string** (keeps the row schema Arrow-uniform); the
SFT framework parses it back to a dict before the chat template renders it — the exact path the
server takes.

### Correctness guards (rows are dropped, never emitted misaligned)

- no literal completion tokens → drop;
- `len(conversations assistant turns) != len(completion_token_ids)` (step-count mismatch) → drop;
- no recoverable `system`/`<tools>`/task turn-0 → drop.

The teacher tokenizer used to **decode** the literal columns is auto-resolved from the source
dataset's `tokenizer_provenance.json` (`served_model`, here `Qwen/Qwen3.5-122B-A10B-FP8`);
override with `--tokenizer`. The **student** model (`--student_model`, default
`Qwen/Qwen3-30B-A3B-Thinking-2507`) is used only by `--validate` to render the parity check.

---

## CLI

```bash
# Build + upload the serve-parity SFT dataset (HF_TOKEN in env).
python -m data.opencode_literals_to_sft \
  --source_repo penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces \
  --source_revision 6cc0c0b5ccec0792a61a98c384a1612bb38c2309 \
  --target_repo laion/nemotron-code-oracle-opencode-sft-serveparity

# Dry-run: convert + structural asserts + RENDER N rows under the student tools-aware template.
# Prints whether the render carries <|im_start|>system / <tools> / <tool_call> / <tool_response>
# / <think> — i.e. the train==serve parity signals. No upload.
python -m data.opencode_literals_to_sft \
  --source_repo penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces \
  --student_model Qwen/Qwen3-30B-A3B-Thinking-2507 --validate 3
```

Key flags: `--limit N` (cap rows), `--private` (private HF repo — note the `laion` org's
PRIVATE quota is full, push PUBLIC), `--drop_reasoning` (drop `<think>` from assistant content;
default keeps verbatim reasoning for Qwen3-Thinking parity), `--tokenizer` (teacher override).

Streaming + bounded (no full-dataset RAM load).

The removed legacy entrypoint `python -m scripts.harbor.literal_traces_to_opencode_sft …`
is no longer supported; use the module command above.

---

## Full end-to-end preprocessing chain

This module is **step 2** of three. It produces train==serve *messages+tools rows*; the
tokenize+mask+pack (SFT framework preprocess) is step 3, and a retention/masking parity gate
verifies the join.

### (1) Source — the literal opencode trace dataset

A Harbor datagen trace dataset carrying `prompt_token_ids` / `completion_token_ids` +
`tokenizer_provenance.json`. Pinned for the densemixer experiment:
`penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces`
@ `6cc0c0b5ccec0792a61a98c384a1612bb38c2309` (mean reward 0.856, 5688 trials). Pin the revision.

### (2) literals → messages+tools  *(this module)*

`python -m data.opencode_literals_to_sft --source_repo … --source_revision … --target_repo …`
→ the serve-parity SFT dataset `laion/nemotron-code-oracle-opencode-sft-serveparity`. Pin the
pushed revision. **Verify with `--validate 3` first** (all parity probes `True`).

### (3) SFT-framework preprocess — tokenize + mask + pack

The SFT config consumes the step-2 dataset. Framework-agnostic keys any tool-aware trainer needs:

```yaml
field_messages: messages          # the rebuilt messages
field_tools: tools                # renders the <tools> system block (train==serve)
chat_template: tokenizer_default  # base Qwen3-30B-A3B-Thinking tools-aware template (4049 chars)
sequence_len: 16384
sample_packing: true
```

Masking: `system` / `tools` / `user` / `tool` turns masked; assistant content trained. Confirm
0 zero-trainable rows and that rows are dropped only for exceeding `sequence_len` (the ~8k-tok
serve-parity system prompt is masked overhead — a low trainable fraction is expected,
correctness > efficiency; lever: bump `sequence_len` to 32768 to recover dropped long traces).

For the pinned dataset this gate passed at **4655/5441 retained (85.6%)**, 0 zero-trainable,
masking correct.

---

## Provenance

- Original implementation: `scripts/harbor/literal_traces_to_opencode_sft.py`.
- Adapted from the general `scripts/harbor/literal_traces_to_sft.py`, which maps tool results to
  `role: human` and keeps inline tool-call text — the **wrong** serve shape; this opencode
  variant is the serve-parity rebuild.
- Experiment: `experiments/active/axolotl-sft-opencode-densemoe/` (POLICY §7, STATE bug ledger #2).
