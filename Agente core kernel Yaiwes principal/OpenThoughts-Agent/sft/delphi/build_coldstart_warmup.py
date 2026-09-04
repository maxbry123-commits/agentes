#!/usr/bin/env python
"""Build the Delphi cold-start CoT-warmup dataset (marin #6279) and push to the laion HF org.

Source: nvidia/Llama-Nemotron-Post-Training-Dataset, SFT **science** split only.
(The SFT code split was dropped: ~1.4% of its reasoning traces fit in 3000 tokens — collecting
them would mean scanning the full 17.6 GB code file for ~4.7k rows. Science yields ~836k passing
rows from a 6 GB file.)

Filtering (all encoded in the output repo name + README):
  - reasoning == "on" only (long-CoT "detailed thinking on" examples)
  - length <= 3000 tokens, measured with the Delphi / Llama-3.1 tokenizer over input+output
  - uniform random subsample (seed 0) to 100,000 rows

Purpose: warm up the Delphi chat-template reasoning tokens (<|start_think|>/<|end_think|>) and the
think->answer shape during cold-start SFT — NOT to teach domain knowledge. Pairs with the `delphi`
LLaMA-Factory template (inline <think>...</think> is normalized to the canonical tokens at encode).
"""

import json
import random

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download
from transformers import AutoTokenizer

SRC_REPO = "nvidia/Llama-Nemotron-Post-Training-Dataset"
SRC_FILE = "SFT/science/science.jsonl"
TOKENIZER = "marin-community/delphi-3e18-447Mparams-1.2Btokens"  # Llama-3.1 tokenizer
OUT_REPO = "laion/llama-nemotron-science-reasoning-on-le3000tok-100k"
MAX_TOKENS = 3000
TARGET = 100_000
POOL = 150_000  # reservoir size (exact-token-filtered down to TARGET)
CHAR_CAP = 12_000  # cheap pre-filter before tokenizing (>=3000 tok is virtually always >12k char)
SEED = 0
OUT_DIR = "/tmp/coldstart_warmup_build"


def stream_reservoir(path: str) -> list[dict]:
    rng = random.Random(SEED)
    pool: list[dict] = []
    seen = 0
    total = 0
    with open(path) as fh:
        for line in fh:
            total += 1
            if total % 100_000 == 0:
                print(
                    f"  scanned {total:,} | char-pass {seen:,} | pool {len(pool):,}",
                    flush=True,
                )
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("reasoning") != "on":
                continue
            inp = d.get("input")
            inp_text = (
                " ".join(m.get("content", "") for m in inp)
                if isinstance(inp, list)
                else str(inp or "")
            )
            out = d.get("output", "") or ""
            if len(inp_text) + len(out) > CHAR_CAP:
                continue
            seen += 1
            slim = {
                k: d.get(k)
                for k in (
                    "input",
                    "output",
                    "category",
                    "reasoning",
                    "generator",
                    "license",
                )
            }
            if len(pool) < POOL:
                pool.append(slim)
            else:
                j = rng.randint(0, seen - 1)
                if j < POOL:
                    pool[j] = slim
    print(
        f"  done: {total:,} rows, {seen:,} char-passing, pool={len(pool):,}", flush=True
    )
    return pool


def exact_token_filter(pool: list[dict], tok) -> list[dict]:
    kept = []
    B = 1000
    for i in range(0, len(pool), B):
        batch = pool[i : i + B]
        texts = []
        for d in batch:
            inp = d["input"]
            inp_text = (
                " ".join(m.get("content", "") for m in inp)
                if isinstance(inp, list)
                else str(inp or "")
            )
            texts.append(inp_text + "\n" + (d["output"] or ""))
        enc = tok(texts, add_special_tokens=False)
        for d, ids in zip(batch, enc.input_ids):
            if len(ids) <= MAX_TOKENS:
                d["num_tokens"] = len(ids)
                kept.append(d)
        if (i // B) % 20 == 0:
            print(
                f"  tokenized {i + len(batch):,}/{len(pool):,} | kept {len(kept):,}",
                flush=True,
            )
    return kept


def to_messages(d: dict) -> list[dict]:
    inp = d["input"]
    msgs = (
        [{"role": m["role"], "content": m["content"]} for m in inp]
        if isinstance(inp, list)
        else []
    )
    msgs.append(
        {"role": "assistant", "content": d["output"]}
    )  # output carries inline <think>...</think>
    return msgs


def main() -> None:
    api = HfApi()
    assert "laion" in [o["name"] for o in api.whoami().get("orgs", [])], (
        "no laion org access"
    )

    print(f"downloading {SRC_REPO}:{SRC_FILE} ...", flush=True)
    path = hf_hub_download(SRC_REPO, SRC_FILE, repo_type="dataset")

    print("reservoir sampling ...", flush=True)
    pool = stream_reservoir(path)

    print("loading tokenizer + exact-token filtering ...", flush=True)
    tok = AutoTokenizer.from_pretrained(TOKENIZER)
    kept = exact_token_filter(pool, tok)

    rng = random.Random(SEED)
    rng.shuffle(kept)
    rows = kept[:TARGET]
    print(f"final rows: {len(rows):,} (target {TARGET:,})", flush=True)
    licenses = sorted({r.get("license") for r in rows})
    gens = sorted({r.get("generator") for r in rows})

    import os

    os.makedirs(f"{OUT_DIR}/data", exist_ok=True)
    table = pa.table(
        {
            "messages": [to_messages(r) for r in rows],
            "num_tokens": [r["num_tokens"] for r in rows],
            "category": [r.get("category") for r in rows],
            "reasoning": [r.get("reasoning") for r in rows],
            "generator": [r.get("generator") for r in rows],
            "license": [r.get("license") for r in rows],
            "source": [f"{SRC_REPO}:{SRC_FILE}"] * len(rows),
        }
    )
    pq.write_table(table, f"{OUT_DIR}/data/train-00000-of-00001.parquet")
    print("wrote parquet", flush=True)

    readme = f"""---
license: other
language:
- en
size_categories:
- 10K<n<100K
task_categories:
- text-generation
tags:
- reasoning
- chain-of-thought
- delphi
- cold-start
- sft
---

# Llama-Nemotron science reasoning — Delphi cold-start CoT warmup (≤3000 tok, reasoning:on, 100k)

A filtered subsample of **[{SRC_REPO}](https://huggingface.co/datasets/{SRC_REPO})** built to
**warm up the Delphi chat-template reasoning tokens** (`<|start_think|>` / `<|end_think|>`) during
cold-start SFT (marin #6279). It is a *template/CoT warmup slice*, not a knowledge dataset.

## Filtering applied (this is the whole point of the repo)
Starting from `{SRC_REPO}`:
- **Subset:** `SFT/science` **only**. The `SFT/code` subset was excluded — ~98.6% of its reasoning
  traces exceed the 3000-token budget below, so it would contribute almost nothing under the filter.
  Math subsets were intentionally excluded to avoid adding math practice to the warmup.
- **`reasoning == "on"`** only — long chain-of-thought ("detailed thinking on") examples, so every
  row exercises the thinking region.
- **Length ≤ {MAX_TOKENS} tokens**, measured with the **Delphi / Llama-3.1 tokenizer**
  (`{TOKENIZER}` vocab) over `input + output`. Conservative cap: the warmup only needs to train the
  template tokens and the think→answer shape, not long reasoning.
- **Uniform random subsample** (reservoir, seed {SEED}) to **{TARGET:,}** rows.

## Format
- `messages`: ShareGPT-style `[{{role, content}}]`. The assistant turn contains an inline
  `<think>...</think>` block followed by the answer. The Delphi LLaMA-Factory template normalizes the
  inline `<think>` to the canonical `<|start_think|>`/`<|end_think|>` tokens at encode time.
- `num_tokens`: Delphi-tokenizer length of input+output (≤ {MAX_TOKENS}).
- `category` (`science`), `reasoning` (`on`), `generator`, `license`, `source`.

## Provenance / license
Derived from `{SRC_REPO}` (NVIDIA). Per-row `license` values present: {licenses}. Generators:
{gens}. Refer to the source dataset for full licensing/terms; this subsample inherits them.

## Not for
Teaching new knowledge or math skills — it is a small, length-capped slice whose only job is to
install the chat-template reasoning tokens before RL.
"""
    with open(f"{OUT_DIR}/README.md", "w") as fh:
        fh.write(readme)

    print(f"creating + uploading {OUT_REPO} ...", flush=True)
    api.create_repo(OUT_REPO, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(folder_path=OUT_DIR, repo_id=OUT_REPO, repo_type="dataset")
    print(f"DONE -> https://huggingface.co/datasets/{OUT_REPO}", flush=True)


if __name__ == "__main__":
    main()
