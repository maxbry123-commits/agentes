"""Stage 4 — tokenizer-footgun-THROUGH-LAUNCHER gate (CRITICAL, HARD BLOCKER).

Runs on the CHECKPOINT the launcher (`python -m hpc.launch --sft_backend axolotl`)
actually produced from a delphi smoke — NOT a hand-crafted save. It proves the
Cycle-1 save-time footgun fix (tokenizer_save_jinja_files:false + the
template_integrity plugin) carried through the launch path, closing the silent
0%-SWE-bench OOD regression *through the launcher*.

jinja-as-ground-truth reframe (notes/axolotl-sft-launch/README.md §Gate M/P
DECISION): the delphi jinja IS the training template AND the serving ground truth.
The byte-match target is the canonical delphi.jinja render (itself byte-identical to
LF DELPHI_V0_JINJA_TEMPLATE, sha256 04a181f5b75f — proven by the submodule's
scripts/marin_fork_gates/stage1_delphi_render.py). No LF-loss-match here.

Asserts, on `<ckpt_dir>` (argv[1]) and every `<ckpt_dir>/checkpoint-*`:
  1. tokenizer_config.json embeds a POPULATED `chat_template` (NOT a
     chat_template.jinja-only split-out save).
  2. apply_chat_template with the tokenizer's OWN embedded template reproduces the
     delphi protocol BYTE-FOR-BYTE vs the canonical delphi.jinja render.
  3. the per-checkpoint dirs ALSO carry the embedded template (the flag-ignoring
     trainer save the plugin must cover).

Self-contained (does not import the submodule's _common, to avoid sys.path/local-path
fragility on the cluster) — reads delphi.jinja from the pinned submodule.

Usage (CPU, on the cluster; transformers-only):
  python sft/axolotl_gates/stage4_footgun_through_launcher.py <ckpt_dir> [--delphi-jinja PATH]

Exit 0 = PASS. Any assertion failure = HARD BLOCK (fails loud, exit 1).
"""
import argparse
import json
import sys
from pathlib import Path

# Canonical delphi.jinja in the pinned axolotl submodule (relative to this repo root).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DELPHI_JINJA = (
    _REPO_ROOT / "sft" / "axolotl" / "src" / "axolotl" / "utils"
    / "chat_templates" / "templates" / "delphi.jinja"
)

# Canonical tool_calls + role:tool conversation (mirrors the submodule's
# marin_fork_gates/_common.py TOOLCALL_CONVO / TOOLS).
TOOLCALL_CONVO = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the weather in Paris?"},
    {
        "role": "assistant",
        "reasoning_content": "The user wants weather. I should call the tool.",
        "content": "Let me check.",
        "tool_calls": [
            {"function": {"name": "get_weather", "arguments": {"city": "Paris"}}}
        ],
    },
    {"role": "tool", "content": '{"temp_c": 18, "cond": "cloudy"}'},
    {"role": "assistant", "content": "It's 18C and cloudy in Paris."},
]
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]


def ok(msg):
    print(f"  PASS  {msg}")


def fail(msg):
    print(f"  FAIL  {msg}")
    sys.exit(1)


def _render(save_dir: Path, chat_template):
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(save_dir))
    kwargs = dict(tokenize=False, add_generation_prompt=True, tools=TOOLS)
    if chat_template is not None:
        kwargs["chat_template"] = chat_template
    return tok.apply_chat_template(TOOLCALL_CONVO, **kwargs)


def assert_dir(save_dir: Path, label: str, delphi_jinja: str) -> None:
    print(f"\n--- {label}: {save_dir} ---")
    tok_cfg_path = save_dir / "tokenizer_config.json"
    if not tok_cfg_path.exists():
        fail(f"{label}: no tokenizer_config.json in {save_dir}")
    tok_cfg = json.loads(tok_cfg_path.read_text())

    # 1. embedded, populated chat_template (not split-out-only)
    embedded = tok_cfg.get("chat_template")
    if not embedded:
        jinja_only = (save_dir / "chat_template.jinja").exists()
        fail(
            f"{label}: tokenizer_config.json has NO populated chat_template "
            f"(chat_template.jinja-only={jinja_only}) — footgun NOT closed through the launcher"
        )
    ok(f"{label}: tokenizer_config.json embeds a populated chat_template ({len(embedded)} chars)")

    # 2. embedded render == canonical delphi.jinja render, byte-for-byte
    r_embedded = _render(save_dir, None)                 # tokenizer's own template (serving path)
    r_canonical = _render(save_dir, delphi_jinja)        # canonical ground-truth jinja
    if r_embedded != r_canonical:
        for i, (a, b) in enumerate(zip(r_embedded, r_canonical)):
            if a != b:
                lo = max(0, i - 40)
                fail(
                    f"{label}: embedded render != canonical delphi.jinja render at char {i}\n"
                    f"  embedded : ...{r_embedded[lo:i+40]!r}\n"
                    f"  canonical: ...{r_canonical[lo:i+40]!r}"
                )
        fail(f"{label}: embedded render length {len(r_embedded)} != canonical {len(r_canonical)}")
    ok(f"{label}: embedded render BYTE-IDENTICAL to canonical delphi.jinja render ({len(r_embedded)} chars)")

    for marker in ("<|start_think|>", "<|tool_call|>", "<|tool_call_end|>",
                   "<|tool_result|>", "<|tool_result_end|>"):
        if marker not in r_embedded:
            fail(f"{label}: delphi render missing protocol marker {marker}")
    ok(f"{label}: render carries the full <|tool_call|>/<|tool_result|> protocol")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpt_dir")
    ap.add_argument("--delphi-jinja", default=str(_DEFAULT_DELPHI_JINJA))
    args = ap.parse_args()

    root = Path(args.ckpt_dir).resolve()
    if not root.is_dir():
        fail(f"checkpoint dir not found: {root}")
    delphi_jinja = Path(args.delphi_jinja).read_text()

    assert_dir(root, "output_dir", delphi_jinja)

    ckpt_dirs = sorted(p for p in root.glob("checkpoint-*") if p.is_dir())
    if not ckpt_dirs:
        fail(
            "no checkpoint-* dirs found under the output_dir — cannot verify the "
            "flag-ignoring per-checkpoint save carries the template"
        )
    for cd in ckpt_dirs:
        assert_dir(cd, f"checkpoint {cd.name}", delphi_jinja)

    print("\nSTAGE 4 FOOTGUN-THROUGH-LAUNCHER GATE: PASS")
    print(f"  covered: output_dir + {len(ckpt_dirs)} checkpoint-* dir(s)")


if __name__ == "__main__":
    main()
