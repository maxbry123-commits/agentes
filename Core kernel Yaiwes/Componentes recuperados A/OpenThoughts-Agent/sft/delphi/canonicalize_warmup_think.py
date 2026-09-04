#!/usr/bin/env python
"""Fix C — regenerate the Delphi cold-start CoT-warmup dataset with CANONICAL think tokens.

The original warmup repo (laion/llama-nemotron-science-reasoning-on-le3000tok-100k) ships
assistant turns carrying inline ``<think>...</think>``. LLaMA-Factory's training-time encode
(`ReasoningTemplate.encode_oneturn`) checks for the *literal* canonical string
``<|start_think|>`` in the content; inline ``<think>`` does NOT satisfy that check, so LF
injects an EMPTY canonical block (``<|start_think|><|end_think|>``) as the loss target and
leaves the real reasoning as literal ``<think>`` text. The model is therefore trained on a
malformed think target (empty-think-then-open-reasoning).

This script converts every assistant message's inline ``<think>...</think>`` into the canonical
``<|start_think|>\n...\n<|end_think|>\n\n`` + answer form, byte-for-byte mirroring the reasoning
extraction in chat_templates/delphi_v0.jinja2 (lines 44-56):

    {%- elif '</think>' in content %}
        {%- set reasoning = content.split('</think>')[0].rstrip('\n').split('<think>')[-1].lstrip('\n') %}
        {%- set content   = content.split('</think>')[-1].lstrip('\n') %}
    {%- endif %}
    ...
    {%- if reasoning %}
        {{- '<|start_think|>\n' + reasoning.strip('\n') + '\n<|end_think|>\n\n' }}
    {%- endif %}
    {{- content }}

So once this runs, the assistant content literally begins with ``<|start_think|>`` → LF's
encode_oneturn check passes → no empty block is injected → the real reasoning trains as targets.

Rows with no ``</think>`` are left as-is (pure answer; LF/encode handles them).
All other fields (num_tokens, category, ...) and system/user turns are preserved byte-for-byte.
"""

import argparse
import os

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

START_THINK = "<|start_think|>"
END_THINK = "<|end_think|>"

SRC_REPO = "laion/llama-nemotron-science-reasoning-on-le3000tok-100k"
SRC_FILE = "data/train-00000-of-00001.parquet"
OUT_REPO = "laion/llama-nemotron-science-reasoning-on-le3000tok-100k-canonical-think"


def canonicalize_content(content: str) -> str:
    """Mirror delphi_v0.jinja2's inline-think -> canonical-token normalization.

    Only fires when '</think>' is present (exactly the jinja's guard). Otherwise returns
    content unchanged. When the extracted reasoning is empty, emits no block at all (also
    matching the jinja's `{%- if reasoning %}`).
    """
    if "</think>" not in content:
        return content
    reasoning = (
        content.split("</think>")[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
    )
    answer = content.split("</think>")[-1].lstrip("\n")
    reasoning = reasoning.strip("\n")
    if reasoning:
        return f"{START_THINK}\n{reasoning}\n{END_THINK}\n\n{answer}"
    return answer


def transform_messages(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        if m.get("role") == "assistant" and isinstance(m.get("content"), str):
            out.append(
                {"role": m["role"], "content": canonicalize_content(m["content"])}
            )
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="/tmp/coldstart_warmup_canonical")
    ap.add_argument("--no_upload", action="store_true")
    args = ap.parse_args()

    print(f"downloading {SRC_REPO}:{SRC_FILE} ...", flush=True)
    src_path = hf_hub_download(SRC_REPO, SRC_FILE, repo_type="dataset")

    table = pq.read_table(src_path)
    cols = table.column_names
    messages = table.column("messages").to_pylist()

    n_assist = n_converted = n_close_only = n_passthrough = 0
    new_messages = []
    for row in messages:
        new_row = []
        for m in row:
            if m.get("role") == "assistant" and isinstance(m.get("content"), str):
                n_assist += 1
                c = m["content"]
                nc = canonicalize_content(c)
                if nc != c:
                    n_converted += 1
                    if "<think>" not in c:
                        n_close_only += 1
                else:
                    n_passthrough += 1
                new_row.append({"role": m["role"], "content": nc})
            else:
                new_row.append({"role": m["role"], "content": m["content"]})
        new_messages.append(new_row)

    print(
        f"rows={len(messages)} assistant_msgs={n_assist} converted={n_converted} "
        f"(close-only={n_close_only}) passthrough(no </think>)={n_passthrough}",
        flush=True,
    )

    # Rebuild the table: replace `messages`, keep all other columns byte-for-byte.
    arrays = []
    names = []
    for name in cols:
        if name == "messages":
            arrays.append(
                pa.array(new_messages, type=table.schema.field("messages").type)
            )
        else:
            arrays.append(table.column(name))
        names.append(name)
    out_table = pa.table(arrays, names=names)

    os.makedirs(f"{args.out_dir}/data", exist_ok=True)
    out_parquet = f"{args.out_dir}/data/train-00000-of-00001.parquet"
    pq.write_table(out_table, out_parquet)
    print(f"wrote {out_parquet}", flush=True)

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

# Llama-Nemotron science reasoning — Delphi cold-start CoT warmup (canonical think tokens)

Regenerated (**Fix C**) variant of
**[{SRC_REPO}](https://huggingface.co/datasets/{SRC_REPO})**.

The original repo's assistant turns carry inline `<think>...</think>`. LLaMA-Factory's
`ReasoningTemplate.encode_oneturn` checks for the *literal* canonical string `<|start_think|>`
in the assistant content; inline `<think>` does NOT satisfy that check, so LF injects an EMPTY
canonical block (`<|start_think|><|end_think|>`) as the loss target and leaves the real reasoning
as literal `<think>` text — i.e. the model is trained on a malformed think target
(empty-think-then-open-reasoning), and in-channel reasoning never actually trains.

This variant converts every assistant message's inline `<think>...</think>` into the canonical
`<|start_think|>\\n...\\n<|end_think|>\\n\\n` + answer form, **byte-for-byte mirroring the
reasoning extraction in `chat_templates/delphi_v0.jinja2`**. With this data, `encode_oneturn`'s
canonical-string check PASSES → no empty block is injected → the reasoning trains as real targets.

- Rows with no `</think>` are left unchanged (pure answer; LF handles them).
- All other fields (`num_tokens`, `category`, `reasoning`, `generator`, `license`, `source`) and
  the system/user turns are preserved byte-for-byte from the source repo.

Produced by `sft/delphi/canonicalize_warmup_think.py` in OpenThoughts-Agent. Inherits the source
dataset's licensing/provenance (derived from `nvidia/Llama-Nemotron-Post-Training-Dataset`).
"""
    with open(f"{args.out_dir}/README.md", "w") as fh:
        fh.write(readme)

    if args.no_upload:
        print("--no_upload set; skipping HF upload", flush=True)
        return

    api = HfApi()
    assert "laion" in [o["name"] for o in api.whoami().get("orgs", [])], (
        "no laion org access"
    )
    print(f"creating + uploading {OUT_REPO} ...", flush=True)
    api.create_repo(OUT_REPO, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(folder_path=args.out_dir, repo_id=OUT_REPO, repo_type="dataset")
    print(f"DONE -> https://huggingface.co/datasets/{OUT_REPO}", flush=True)


if __name__ == "__main__":
    main()
