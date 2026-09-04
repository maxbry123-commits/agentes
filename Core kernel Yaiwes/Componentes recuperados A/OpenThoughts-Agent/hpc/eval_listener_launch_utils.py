"""Thin-wrapper launch path for `hpc.launch --job_type eval_listener`.

Forwards `sys.argv` VERBATIM to `eval/unified_eval_listener.py` after running the
`hpc.launch` preamble (`detect_hpc` + `set_environment` + `setup_hosted_vllm_api_key` +
`load_supabase_keys`, the latter already called in `hpc.launch.main`).

This is the Stage-1 thin wrapper of the eval-listener-unification plan. The listener
parses its own ~50 flags natively (no redeclaration in `hpc/arguments.py`, no
`parse_known_args` coupling to the launcher's argparse) — so forwarding is lossless and
the only argv mutation is stripping the launcher's own `--job_type eval_listener` pair.

The preamble gives the listener, for free, what operators previously had to do by hand:
`source hpc/dotenv/<cluster>.env` (→ DCFT / DCFT_ACTIVATE_ENV / EXPERIMENTS_DIR /
PYTHONPATH) + the hosted-vllm + Supabase key setup. The listener's own
`--cluster-config eval/clusters/<c>.yaml` is orthogonal (the eval cluster YAML) and is
forwarded unchanged.

G2 (wrapper parity) is proven by `eval/tests/listener_submit_harness.py --check`:
the resolved submit artifacts are byte-identical whether the listener is invoked
directly or via this wrapper.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional


def _is_eval_listener_request(argv: Optional[List[str]] = None) -> bool:
    """True iff argv asks for the eval_listener fast-path.

    Matches both `--job_type eval_listener` (the canonical Stage-1 name) AND
    `--job_type eval` (the Stage-3 deprecated alias that reroutes to the listener —
    the single-shot eval path was removed as strictly subsumed; see
    notes/ot-agent/eval_singleshot_audit.md).
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--job_type" and i + 1 < len(argv):
            return argv[i + 1] in ("eval_listener", "eval")
        if tok.startswith("--job_type="):
            return tok.split("=", 1)[1] in ("eval_listener", "eval")
        i += 1
    return False


def _is_eval_alias(argv: Optional[List[str]] = None) -> bool:
    """True iff argv uses the deprecated `--job_type eval` alias (not `eval_listener`)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--job_type" and i + 1 < len(argv):
            return argv[i + 1] == "eval"
        if tok.startswith("--job_type="):
            return tok.split("=", 1)[1] == "eval"
        i += 1
    return False


def _strip_job_type(argv: List[str]) -> List[str]:
    """Remove the `--job_type eval_listener` / `--job_type=eval_listener` pair."""
    cleaned: List[str] = []
    skip_next = False
    for i, tok in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if tok == "--job_type":
            # Value is the next token; skip both. (Only called when value is eval_listener.)
            skip_next = True
            continue
        if tok.startswith("--job_type="):
            continue
        cleaned.append(tok)
    return cleaned


def launch_eval_listener_from_argv() -> int:
    """Run the preamble, then run the listener IN-PROCESS with forwarded argv.

    Stage 5: instead of shelling out to ``eval/unified_eval_listener.py`` via
    ``subprocess``, the listener's own ``main()`` is invoked in this process.
    This is the deep-integration end-state: ``hpc.launch --job_type eval_listener``
    runs the listener in-process, sharing the launcher's preamble (detect_hpc /
    set_environment / setup_hosted_vllm_api_key / load_supabase_keys) + Python
    interpreter. The listener's public API (parse_args / build_config /
    EvalListener / PRESETS / load_cluster_config) and the standalone
    ``python eval/unified_eval_listener.py`` script are UNTOUCHED — every
    ``from eval.unified_eval_listener import X`` still resolves.

    We do NOT physically relocate the 4.7k-line listener into a ``hpc/eval_listener/``
    package: the in-process call achieves the unification goal (single entry point,
    shared preamble + interpreter, unified exit-code propagation) without the
    large-diff regression risk of a file move. ``sys.argv`` is set so the listener's
    ``parse_args()`` (which reads ``sys.argv``) sees the forwarded flags verbatim.

    Returns the listener's exit code (0 normally; argparse may SystemExit on --help
    or a parse error, which propagates as the process exit).
    """
    from hpc.hpc import detect_hpc, set_environment
    from hpc.launch_utils import setup_hosted_vllm_api_key
    import eval.unified_eval_listener as uel

    # --- preamble (the ergonomic win: operators no longer source the dotenv by hand) ---
    hpc = detect_hpc()
    set_environment(hpc)
    setup_hosted_vllm_api_key()

    # --- forward the listener's own flags verbatim (strip only --job_type eval_listener) ---
    listener_argv = _strip_job_type(list(sys.argv[1:]))

    # Deprecation nudge for the `eval` alias (one-window; the canonical name is
    # `eval_listener`). The alias still works — it forwards to the listener unchanged.
    if _is_eval_alias():
        print(
            "[hpc.launch] note: --job_type eval is a deprecated alias for "
            "--job_type eval_listener (the single-shot eval path was removed); "
            "rerouting to the listener. Prefer --job_type eval_listener.",
            file=sys.stderr,
        )

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # The listener resolves relative paths (eval/clusters/*.yaml, eval/lists/*) against
    # cwd, and its sbatch WORKDIR guard requires cwd == repo root. The skill's §3 🚧
    # note exists precisely because this trips when launched from elsewhere.
    os.chdir(repo_root)

    # PYTHONPATH must include the repo root (listener imports top-level packages:
    # database, eval, hpc). set_environment() already adds $DCFT, but set it
    # explicitly so the wrapper is correct even if dotenv is missing.
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = repo_root + (os.pathsep + existing if existing else "")
    os.environ["PYTHONPATH"] = env["PYTHONPATH"]

    # Set sys.argv so the listener's parse_args() (which reads sys.argv) sees the
    # forwarded flags verbatim — argv[0] is the logical program name.
    preview = " ".join(listener_argv[:4])
    print(
        f"[hpc.launch:eval_listener] cluster={hpc.name} | running listener in-process "
        f"with {len(listener_argv)} arg(s): {preview}{'…' if len(listener_argv) > 4 else ''}",
        file=sys.stderr,
    )
    sys.argv = ["unified_eval_listener.py"] + listener_argv

    # Run the listener's main() in THIS process. argparse may raise SystemExit
    # (--help, parse error) which propagates as the process exit code — desired.
    try:
        uel.main()
        return 0
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else (1 if e.code else 0)
