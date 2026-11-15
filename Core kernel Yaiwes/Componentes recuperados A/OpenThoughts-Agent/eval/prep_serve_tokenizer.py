#!/usr/bin/env python
"""Serve-side tokenizer transformers-5.x compat prep for eval.

WHY THIS EXISTS
---------------
A model exported by transformers 5.x (`TokenizersBackend`) can ship a
`tokenizer_config.json` whose `extra_special_tokens` is a **LIST** of token
strings instead of the ``{name: token}`` **dict** transformers expects. On
load, ``PreTrainedTokenizerBase._set_model_specific_special_tokens`` does
``special_tokens.keys()`` / ``.items()`` on that value, so a list crashes
vLLM's tokenizer load at API-server startup — BEFORE any TP/DP placement — with::

    AttributeError: 'list' object has no attribute 'keys'

Observed on the RL export
``laion/rl__24GPU_qwen3_coder_30b_a3b__...__Qwen3-Coder-30B-A3B-40-30B`` (jobs
48249276 / 48249279 / 48249281). This is the same transformers-5.x compat class
as ot-agent commit ``a70eb4d1`` (which coerced the *absent* ``added_tokens_decoder``
in the delphi SFT tokenizer-prep); here the serve path needs the analogous
coercion for the ``extra_special_tokens`` shape.

THE COERCION
------------
The token strings in the mis-serialized list are the model's standard special
tokens, which are ALREADY registered (``"special": true``) in ``tokenizer.json``'s
added-tokens — so they remain special regardless of ``extra_special_tokens``.
The correct, lossless fix is therefore to normalize a list-valued
``extra_special_tokens`` to an empty dict ``{}`` (a no-op for
``_set_model_specific_special_tokens``). A well-formed config (dict, or the key
absent) is left untouched.

NON-DESTRUCTIVE
---------------
We never mutate the shared HF cache. When (and only when) coercion is needed we
build a patched tokenizer directory that SYMLINKS every file of the model's
(already-downloaded) tokenizer snapshot and overrides ONLY
``tokenizer_config.json``, then print that directory on stdout. The caller passes
it to vLLM as ``--tokenizer`` (``--model`` still loads weights from the repo).
If no coercion is needed we print NOTHING → the caller adds no ``--tokenizer`` →
behavior is byte-identical to before for every well-formed model.

Usage:
    patched_dir=$(python eval/prep_serve_tokenizer.py <model_id_or_local_dir>)
    # empty  -> serve --model's own tokenizer unchanged
    # nonempty -> pass  --tokenizer "$patched_dir"  to vLLM

All diagnostics go to STDERR; STDOUT carries ONLY the patched dir path (or is
empty). The script never fails the launch: any error prints a warning to stderr
and emits an empty stdout so the serve proceeds on its original path.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# tokenizer-relevant sidecar files worth symlinking into a patched dir (any that
# exist). We also symlink every other file present in the snapshot dir so nothing
# the tokenizer needs is ever missed; this list only documents intent.
_TOKENIZER_FILES = (
    "tokenizer.json",
    "tokenizer.model",
    "vocab.json",
    "merges.txt",
    "added_tokens.json",
    "special_tokens_map.json",
    "chat_template.jinja",
    "chat_template.json",
    "tokenizer_config.json",
)


def _log(msg: str) -> None:
    print(f"[prep-serve-tokenizer] {msg}", file=sys.stderr, flush=True)


def _resolve_local_dir(model: str) -> Path | None:
    """Return the local directory holding the model's tokenizer files, or None.

    A local path is used directly. An HF repo id is resolved from the local
    cache only (``local_files_only=True``) — the compute node has no internet and
    the model is always pre-downloaded before serve.
    """
    p = Path(model)
    if p.is_dir() and (p / "tokenizer_config.json").exists():
        return p
    try:
        from huggingface_hub import snapshot_download

        local = snapshot_download(
            model,
            local_files_only=True,
            allow_patterns=list(_TOKENIZER_FILES),
        )
        return Path(local)
    except Exception as e:  # noqa: BLE001 — never block the launch
        _log(f"could not resolve local tokenizer for {model!r}: {e}")
        return None


def _needs_coercion(cfg: dict) -> bool:
    return isinstance(cfg.get("extra_special_tokens"), list)


def _coerce(cfg: dict) -> dict:
    """Normalize a list-valued ``extra_special_tokens`` to an empty dict.

    The listed tokens stay special via tokenizer.json's added-tokens, so dropping
    the redundant list is lossless and yields the dict shape transformers wants.
    """
    est = cfg.get("extra_special_tokens")
    if isinstance(est, list):
        _log(
            "coercing extra_special_tokens LIST -> {} "
            f"(dropped {len(est)} redundant entries already special in tokenizer.json): {est}"
        )
        cfg["extra_special_tokens"] = {}
    return cfg


def _build_patched_dir(src_dir: Path, patched_cfg: dict, model: str) -> Path:
    safe = model.replace("/", "__").replace(":", "_")
    base = (
        os.environ.get("SERVE_TOK_PREP_DIR")
        or os.environ.get("VLLM_CACHE_ROOT")
        or (os.environ.get("TMPDIR") or "/tmp")
    )
    out = Path(base) / "serve_tok_prep" / safe
    out.mkdir(parents=True, exist_ok=True)

    # Symlink every entry of the source tokenizer snapshot so nothing is missed;
    # then override tokenizer_config.json with a real (patched) file.
    for entry in src_dir.iterdir():
        if entry.name == "tokenizer_config.json":
            continue
        link = out / entry.name
        try:
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(entry.resolve())
        except OSError as e:
            _log(f"symlink {entry.name} failed ({e}); copying is unnecessary, skipping")

    (out / "tokenizer_config.json").write_text(
        json.dumps(patched_cfg, ensure_ascii=False, indent=2)
    )
    return out


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        _log("no model argument; nothing to do")
        return 0
    model = sys.argv[1].strip()

    src_dir = _resolve_local_dir(model)
    if src_dir is None:
        # Can't help — let vLLM proceed on its own path (prints nothing).
        return 0

    cfg_path = src_dir / "tokenizer_config.json"
    try:
        cfg = json.loads(cfg_path.read_text())
    except Exception as e:  # noqa: BLE001
        _log(f"could not read {cfg_path}: {e}; leaving serve unchanged")
        return 0

    if not _needs_coercion(cfg):
        _log(
            f"tokenizer_config.json for {model!r} is well-formed "
            "(extra_special_tokens not a list) — no override (byte-identical serve)"
        )
        return 0

    patched = _coerce(dict(cfg))
    out = _build_patched_dir(src_dir, patched, model)
    _log(f"emitting patched tokenizer dir: {out}")
    # STDOUT: ONLY the patched dir path (consumed by build_vllm_cmd.sh).
    print(str(out))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001 — a prep failure must never block serve
        _log(f"unexpected error, leaving serve unchanged: {e}")
        sys.exit(0)
