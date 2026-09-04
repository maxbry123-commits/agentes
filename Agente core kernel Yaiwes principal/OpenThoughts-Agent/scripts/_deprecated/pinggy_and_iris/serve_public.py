#!/usr/bin/env python3
"""serve_public.py — front a `marin-serve` endpoint with a public Pinggy URL (vibe testing).

`marin-serve` stands up vLLM on an Iris TPU slice and exposes it only through
the auth-gated Iris controller proxy — reachable at
``http://127.0.0.1:<port>/proxy/serve.<endpoint>/`` via your controller SSH
tunnel, i.e. only to people with cluster access. This launches (or attaches to)
marin-serve, parses the local dashboard URL, and opens a **Pinggy** tunnel from
our endpoint bank in front of that local port, yielding a shareable public
``https://…a.pinggy.link`` URL anyone on the internet can hit.

It reuses ``hpc.pinggy_utils.PinggyTunnel`` for the tunnel and the
``notes/ot-agent/pinggy_bank.md`` pairs for the persistent URLs/tokens.

⚠️  SECURITY: the public URL is UNAUTHENTICATED — it inherits the no-auth
localhost view of the controller proxy. For throwaway vibe testing only, not a
production service. A short default ``--timeout-hours`` (marin-serve self-stops
the slice) and one-shot pinggy pairs you can rotate are baked in; tear it down
when done.

Examples
--------
  # Launch the Delphi 9.7B SFT canary + a public URL, pinggy pair 1:
  python scripts/inference/serve_public.py \
      laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft \
      --tpu v6e-4 --region europe-west4 \
      --chat-template https://raw.githubusercontent.com/open-thoughts/OpenThoughts-Agent/ed4d6f483151f14d6d78cf732f04cd3c8ff5c606/chat_templates/delphi_v0.jinja2 \
      --pair 1

  # Attach a public URL to an already-running local marin-serve dashboard:
  python scripts/inference/serve_public.py \
      --attach-local-url http://127.0.0.1:10044/proxy/serve.serve-qwen3-0-6b-ab12cd/ --pair 2
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# Make `hpc` importable regardless of CWD (this file lives in scripts/inference/).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hpc.pinggy_utils import PinggyConfig, PinggyTunnel  # noqa: E402

DEFAULT_BANK = os.environ.get(
    "PINGGY_BANK",
    str(Path.home() / "Documents" / "notes" / "ot-agent" / "pinggy_bank.md"),
)
# marin-serve invocation. Default to the module form (the console script isn't
# registered by the marin root `uv sync`); works whenever the marin package is
# importable. May be a multi-token command (shlex-split). Override with
# --marin-serve-bin / MARIN_SERVE_BIN (e.g. an actual `marin-serve` on PATH).
_MARIN_PY = str(Path.home() / "Documents" / "marin" / ".venv" / "bin" / "python")
DEFAULT_MARIN_SERVE = os.environ.get(
    "MARIN_SERVE_BIN", f"{_MARIN_PY} -m marin.inference.quick_serve_cli"
)
# READY — dashboard: http://127.0.0.1:10044/proxy/serve.serve-qwen3-0-6b-ab12cd/
_READY_RE = re.compile(r"http://127\.0\.0\.1:(\d+)(/proxy/serve\.[^/\s]+/)")


def parse_bank(path: str) -> list[tuple[str, str]]:
    """Parse pinggy_bank.md into ordered (persistent_url, token) pairs."""
    text = Path(path).read_text()
    # Each "## Pair N" block holds a *.a.pinggy.link line and a token line.
    pairs: list[tuple[str, str]] = []
    url = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("--"):
            continue
        if s.endswith(".a.pinggy.link") or ".a.pinggy.link" in s:
            url = s.split()[0]
        elif url is not None:
            pairs.append((url, s.split()[0]))
            url = None
    if not pairs:
        raise SystemExit(f"No pinggy pairs parsed from {path}")
    return pairs


def pick_pair(args) -> tuple[str, str]:
    if args.pinggy_url and args.pinggy_token:
        return args.pinggy_url, args.pinggy_token
    pairs = parse_bank(args.pinggy_bank)
    if args.pair is not None:
        if not (1 <= args.pair <= len(pairs)):
            raise SystemExit(
                f"--pair {args.pair} out of range (bank has {len(pairs)} pairs)"
            )
        return pairs[args.pair - 1]
    # default: first pair, but warn (caller should pick an unused one)
    print(
        f"[serve_public] no --pair given; defaulting to pair 1 ({pairs[0][0]}). "
        f"Pass --pair N (1..{len(pairs)}) to pick another if it's in use."
    )
    return pairs[0]


def build_marin_cmd(args) -> list[str]:
    cmd = shlex.split(args.marin_serve_bin) + [
        args.model,
        "--cluster",
        args.cluster,
        "--tpu",
        args.tpu,
        "--timeout-hours",
        str(args.timeout_hours),
    ]
    if args.region:
        cmd += ["--region", args.region]
    if args.chat_template:
        cmd += ["--chat-template", args.chat_template]
    if args.tensor_parallel_size:
        cmd += ["--tensor-parallel-size", str(args.tensor_parallel_size)]
    if args.max_model_len:
        cmd += ["--max-model-len", str(args.max_model_len)]
    if args.extra:
        cmd += args.extra.split()
    return cmd


def verify_public(persistent_url: str, base_path: str) -> tuple[bool, str]:
    """Probe the public /v1/models via the REAL Pinggy edge, bypassing local DNS.

    Some ISPs poison ``*.a.pinggy.link`` to a dead IP, so a probe using the
    system resolver hangs even when the tunnel is live. Resolve the edge via
    1.1.1.1 and force it with ``curl --resolve`` so this check reflects the
    tunnel's real state, not the launch host's broken DNS.

    Returns (ok, detail) where ok is True iff /v1/models returns HTTP 200.
    """
    try:
        dig = subprocess.run(
            ["dig", "@1.1.1.1", "+short", persistent_url],
            capture_output=True,
            text=True,
            timeout=15,
        )
        edge_ip = (dig.stdout.strip().splitlines() or [""])[-1].strip()
    except Exception:
        edge_ip = ""
    url = f"https://{persistent_url}{base_path}v1/models"
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "25"]
    if edge_ip:
        cmd += ["--resolve", f"{persistent_url}:443:{edge_ip}"]
    cmd.append(url)
    try:
        code = subprocess.run(
            cmd, capture_output=True, text=True, timeout=35
        ).stdout.strip()
    except Exception as e:
        return False, f"probe error: {e}"
    return code == "200", f"HTTP {code} via edge {edge_ip or '(system DNS)'}"


def launch_marin_serve(args) -> tuple[subprocess.Popen, int, str]:
    """Launch marin-serve, stream its output, return (proc, local_port, base_path) once READY."""
    cmd = build_marin_cmd(args)
    print(f"[serve_public] launching: {' '.join(cmd)}\n")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    deadline = time.time() + args.ready_timeout
    port, base = None, None
    assert proc.stdout is not None
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line == "" and proc.poll() is not None:
            raise SystemExit(
                f"marin-serve exited (code {proc.returncode}) before READY."
            )
        if not line:
            continue
        sys.stdout.write("  [marin-serve] " + line)
        m = _READY_RE.search(line)
        if m:
            port, base = int(m.group(1)), m.group(2)
            break
    if port is None:
        proc.terminate()
        raise SystemExit(
            f"Timed out after {args.ready_timeout}s waiting for marin-serve READY line."
        )

    # keep draining marin-serve stdout so its pipe never blocks
    def _drain():
        for ln in proc.stdout:  # type: ignore[union-attr]
            sys.stdout.write("  [marin-serve] " + ln)

    threading.Thread(target=_drain, daemon=True).start()
    return proc, port, base


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "model",
        nargs="?",
        help="HF repo id or gs:// checkpoint to serve (launch mode).",
    )
    p.add_argument(
        "--attach-local-url",
        help="Attach to an already-running marin-serve local dashboard URL "
        "(http://127.0.0.1:<port>/proxy/serve.<ep>/) instead of launching.",
    )
    # marin-serve passthrough
    p.add_argument("--cluster", default="marin")
    p.add_argument("--tpu", default="v6e-8")
    p.add_argument("--region", default=None)
    p.add_argument("--chat-template", default=None)
    p.add_argument(
        "--timeout-hours",
        type=float,
        default=6.0,
        help="marin-serve self-stop (default 6h for vibe tests; marin-serve's own default is 24h).",
    )
    p.add_argument("--tensor-parallel-size", type=int, default=None)
    p.add_argument("--max-model-len", type=int, default=None)
    p.add_argument("--marin-serve-bin", default=DEFAULT_MARIN_SERVE)
    p.add_argument(
        "--extra",
        default=None,
        help="Extra raw args appended to the marin-serve command.",
    )
    p.add_argument(
        "--ready-timeout",
        type=int,
        default=2700,
        help="Seconds to wait for marin-serve READY (cold compile).",
    )
    # pinggy
    p.add_argument(
        "--pair", type=int, default=None, help="Pinggy bank pair number (1-based)."
    )
    p.add_argument("--pinggy-bank", default=DEFAULT_BANK)
    p.add_argument(
        "--pinggy-url",
        default=None,
        help="Explicit pinggy persistent url (overrides bank).",
    )
    p.add_argument(
        "--pinggy-token",
        default=None,
        help="Explicit pinggy token (with --pinggy-url).",
    )
    args = p.parse_args()

    if not args.attach_local_url and not args.model:
        p.error("provide a model (launch mode) or --attach-local-url (attach mode).")

    url, token = pick_pair(args)

    proc = None
    if args.attach_local_url:
        m = _READY_RE.search(args.attach_local_url) or re.search(
            r"http://[^:]+:(\d+)(/\S*/)", args.attach_local_url
        )
        if not m:
            raise SystemExit(
                "Could not parse <port> and base path from --attach-local-url."
            )
        local_port, base_path = int(m.group(1)), m.group(2)
        print(f"[serve_public] attaching to local 127.0.0.1:{local_port}{base_path}")
    else:
        proc, local_port, base_path = launch_marin_serve(args)

    cfg = PinggyConfig(
        persistent_url=url, token=token, local_port=local_port, local_host="127.0.0.1"
    )
    log_path = Path("/tmp") / f"pinggy_{url.split('.')[0]}.log"
    tunnel = PinggyTunnel(config=cfg, log_path=log_path)

    def _shutdown(*_):
        print("\n[serve_public] shutting down…")
        try:
            tunnel.stop()
        finally:
            if proc and proc.poll() is None:
                proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    tunnel.start()
    public_dash = f"https://{url}{base_path}"
    public_openai = f"https://{url}{base_path}v1"

    ok, detail = verify_public(url, base_path)
    status = "LIVE ✓" if ok else "TUNNEL UP — public probe FAILED ✗"
    print("\n" + "=" * 72)
    print(
        f"  PUBLIC vibe-test endpoint {status} (unauthenticated — throwaway use only)"
    )
    print(f"  dashboard : {public_dash}")
    print(f"  OpenAI    : {public_openai}")
    print(f"  curl: curl {public_openai}/models")
    print(f"  verify    : {detail}")
    print(
        f"  tunnel log: {log_path}   |   marin-serve self-stops in {args.timeout_hours}h"
    )
    if not ok:
        print(
            "  ⚠ Public /v1/models did not return 200. The endpoint may still be cold-loading;"
            "\n    re-probe shortly, or inspect the tunnel log. If YOUR browser can't load it but"
            "\n    this probe passed, your ISP is poisoning *.a.pinggy.link — point system DNS at"
            "\n    1.1.1.1/8.8.8.8 or add a /etc/hosts entry for the edge IP shown above."
        )
    print("  Ctrl-C to tear down the tunnel (and marin-serve if launched here).")
    print("=" * 72 + "\n")

    # hold until the tunnel or marin-serve dies, or Ctrl-C
    while tunnel.is_running and (proc is None or proc.poll() is None):
        time.sleep(3)
    print("[serve_public] tunnel or marin-serve exited; cleaning up.")
    _shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
