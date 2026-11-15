"""Flag-off parity harness for the pinggy -> controller-ingress change (Stage 0).

Every later stage of the ``pinggy-controller-ingress`` plan
(``notes/ot-agent/pinggy_controller_ingress_plan.md``) claims **G0: with
``--ingress-mode pinggy`` (the default) the pinggy decision surface is
byte-identical to today.** This module captures that surface into a committed
golden JSON and provides a ``--check`` gate that fails on any drift, so Stage 4
(the wiring swap) can prove it did not change the flag-off path.

The captured surface is the observable output of the exact functions Stage 4
edits, exercised over a ``(agent x env_type)`` matrix plus the eval-listener
pinggy env:

  1. ``hpc.pinggy_utils.needs_pinggy_tunnel(agent, env_type)`` -- the single gate.
  2. ``use_pinggy`` (mirrors the real ``has_url and has_token and needs_tunnel``
     gate) and the resulting ``api_base`` / merged agent kwargs that
     ``build_pinggy_endpoint_meta`` / ``build_endpoint_meta`` +
     ``merge_agent_kwargs`` would inject, for a FIXED synthetic pinggy URL and a
     FIXED synthetic vLLM endpoint.
  3. the eval-listener ``EVAL_PINGGY_URL`` / ``EVAL_PINGGY_TOKEN`` env that
     ``SbatchParams.to_env()`` emits, for fixed / empty ``--pinggy-url/-token``.

This stage adds NO runtime behavior; it only captures the baseline.

Usage
-----
    # regenerate the golden (only when the pinggy surface *intentionally* changes)
    .venv/bin/python tests/hpc/test_ingress_parity_harness.py --capture

    # gate: diff current code vs the committed golden, non-zero exit on drift
    .venv/bin/python tests/hpc/test_ingress_parity_harness.py --check

    # or via pytest
    .venv/bin/python -m pytest tests/hpc/test_ingress_parity_harness.py -v
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make `hpc`/`eval` importable regardless of CWD (this file lives in tests/hpc/).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

GOLDEN_PATH = Path(__file__).resolve().parent / "ingress_parity_golden.json"

# Fixed synthetic values so the capture is deterministic (never real secrets).
_FIXED_PINGGY_URL = "https://parity-fixture.a.pinggy.link"
_FIXED_PINGGY_TOKEN = "PARITY_FIXTURE_TOKEN"  # not a real token; deterministic fixture
_FIXED_VLLM_ENDPOINT = "http://10.0.0.1:8000/v1"

# The (agent x env_type) matrix. Agents span an installed agent, several
# OpenAI-compatible agents, the in-process terminus-2, and None (first-agent
# fallback); env_types span the cloud backends (tunnel) and every local backend
# (no tunnel) plus None. This exercises both branches of needs_pinggy_tunnel.
_AGENTS = ["terminus-2", "openhands", "qwen-code", "codex", "hermes", None]
_ENV_TYPES = [
    "daytona",
    "modal",
    "docker",
    "podman_hpc",
    "apptainer",
    "singularity",
    "local",
    None,
]


def _cell_key(agent: object, env_type: object) -> str:
    return f"agent={agent!r}|env={env_type!r}"


def capture_surface() -> dict:
    """Capture the full observable pinggy decision surface as a plain dict."""
    from hpc.harbor_utils import (
        build_endpoint_meta,
        merge_agent_kwargs,
    )
    from hpc.pinggy_utils import build_pinggy_endpoint_meta, needs_pinggy_tunnel

    # A fixed synthetic Harbor config so merge_agent_kwargs has a stable base.
    harbor_config_data = {
        "agents": [
            {"name": "terminus-2", "kwargs": {"model_name": "fixture-model"}},
            {"name": "openhands", "kwargs": {"model_name": "fixture-model"}},
        ]
    }

    # has_url/has_token are always True in this fixture (both provided), so
    # use_pinggy tracks needs_tunnel exactly -- mirroring the real gate
    # `use_pinggy = has_url and has_token and needs_tunnel`.
    has_url = True
    has_token = True

    matrix: dict[str, dict] = {}
    for agent in _AGENTS:
        for env_type in _ENV_TYPES:
            needs_tunnel = needs_pinggy_tunnel(agent, env_type)
            use_pinggy = has_url and has_token and needs_tunnel

            if use_pinggy:
                endpoint_meta = build_pinggy_endpoint_meta(_FIXED_PINGGY_URL)
            else:
                endpoint_meta = build_endpoint_meta(_FIXED_VLLM_ENDPOINT)

            merged_kwargs, passthrough = merge_agent_kwargs(
                harbor_config_data,
                agent_name=agent,
                endpoint_meta=endpoint_meta,
            )

            matrix[_cell_key(agent, env_type)] = {
                "needs_pinggy_tunnel": needs_tunnel,
                "use_pinggy": use_pinggy,
                "endpoint_meta": endpoint_meta,
                "merged_api_base": merged_kwargs.get("api_base"),
                "merged_api_key": merged_kwargs.get("api_key"),
                "merged_metrics_endpoint": merged_kwargs.get("metrics_endpoint"),
                "passthrough": passthrough,
            }

    # Eval-listener pinggy env emission, exercised via the real SbatchParams.to_env().
    from eval.unified_eval_listener import SbatchParams

    def _pinggy_env(url, token):
        env = SbatchParams(pinggy_url=url, pinggy_token=token).to_env()
        return {k: v for k, v in env.items() if k.startswith("EVAL_PINGGY_")}

    eval_listener = {
        "both_set": _pinggy_env(_FIXED_PINGGY_URL, _FIXED_PINGGY_TOKEN),
        "neither_set": _pinggy_env(None, None),
        "url_only": _pinggy_env(_FIXED_PINGGY_URL, None),
    }

    return {
        "_meta": {
            "description": "Flag-off pinggy decision surface (G0 baseline). "
            "Regenerate ONLY on an intentional pinggy-surface change.",
            "fixed_pinggy_url": _FIXED_PINGGY_URL,
            "fixed_vllm_endpoint": _FIXED_VLLM_ENDPOINT,
        },
        "matrix": matrix,
        "eval_listener": eval_listener,
    }


def load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text())


def write_golden(surface: dict) -> None:
    GOLDEN_PATH.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n")


def diff_against_golden() -> list[str]:
    """Return a list of human-readable drift descriptions (empty == clean)."""
    current = capture_surface()
    golden = load_golden()
    drifts: list[str] = []

    # Compare everything except the free-text _meta.description.
    def _strip(d: dict) -> dict:
        d = json.loads(json.dumps(d))  # deep copy
        d.get("_meta", {}).pop("description", None)
        return d

    cur_s = json.dumps(_strip(current), indent=2, sort_keys=True)
    gold_s = json.dumps(_strip(golden), indent=2, sort_keys=True)
    if cur_s != gold_s:
        # Produce a per-key drift list for the matrix + eval_listener.
        for section in ("matrix", "eval_listener"):
            cur_sec = current.get(section, {})
            gold_sec = golden.get(section, {})
            keys = set(cur_sec) | set(gold_sec)
            for k in sorted(keys):
                if cur_sec.get(k) != gold_sec.get(k):
                    drifts.append(
                        f"[{section}] {k}: golden={gold_sec.get(k)!r} current={cur_sec.get(k)!r}"
                    )
        if not drifts:
            drifts.append(
                "Surface changed but no per-cell diff isolated; compare golden JSON directly."
            )
    return drifts


# --------------------------------------------------------------------------- #
# pytest entry points
# --------------------------------------------------------------------------- #
def test_golden_exists():
    assert GOLDEN_PATH.exists(), (
        f"Golden {GOLDEN_PATH} missing. Regenerate with "
        f"`python tests/hpc/test_ingress_parity_harness.py --capture`."
    )


def test_flag_off_surface_matches_golden():
    drifts = diff_against_golden()
    assert not drifts, "Flag-off pinggy surface drifted from golden:\n" + "\n".join(
        drifts
    )


def test_needs_tunnel_semantics_unchanged():
    """Spot-check the load-bearing gate directly (terminus-2 + local => no tunnel; cloud => tunnel)."""
    from hpc.pinggy_utils import needs_pinggy_tunnel

    assert needs_pinggy_tunnel("terminus-2", "daytona") is False
    assert needs_pinggy_tunnel("openhands", "docker") is False
    assert needs_pinggy_tunnel("openhands", "apptainer") is False
    assert needs_pinggy_tunnel("openhands", "daytona") is True
    assert needs_pinggy_tunnel("openhands", "modal") is True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--capture", action="store_true", help="Regenerate the committed golden JSON."
    )
    g.add_argument(
        "--check",
        action="store_true",
        help="Diff current code vs golden; non-zero exit on drift.",
    )
    args = ap.parse_args(argv)

    if args.capture:
        surface = capture_surface()
        write_golden(surface)
        print(f"[ingress-parity] wrote golden -> {GOLDEN_PATH}")
        return 0

    # --check
    if not GOLDEN_PATH.exists():
        print(
            f"[ingress-parity] FAIL: golden missing at {GOLDEN_PATH}", file=sys.stderr
        )
        return 2
    drifts = diff_against_golden()
    if drifts:
        print("[ingress-parity] DRIFT vs golden:", file=sys.stderr)
        for d in drifts:
            print("  " + d, file=sys.stderr)
        return 1
    print("[ingress-parity] OK: flag-off surface byte-identical to golden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
