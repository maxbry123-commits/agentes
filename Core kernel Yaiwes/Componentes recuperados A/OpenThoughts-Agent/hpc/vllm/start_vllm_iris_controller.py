#!/usr/bin/env python3
"""Start a multi-host vLLM-TPU OpenAI HTTP endpoint on an iris slice.

This is the iris analog of ``start_vllm_ray_controller.py`` (the SLURM /
single-host path). The crucial difference: iris auto-runs the entrypoint on
ALL ``vm_count`` hosts of a TPU slice (one task per VM), injecting
``IRIS_TASK_ID`` / ``IRIS_NUM_TASKS`` per task. The only supported multi-host
vLLM-TPU serve path is ``TPU_MULTIHOST_BACKEND=ray`` →
``RayDistributedExecutor``, which requires ONE real cross-host Ray cluster
(a head + workers spanning the slice's VMs) and then ONE ``vllm serve`` on the
head whose RayDistributedExecutor fans TP/DP engine workers across the Ray
nodes.

So this script bootstraps that single cluster:

- **rank 0 (head):** ``ray start --head``; wait until ``ray.nodes()`` shows all
  ``IRIS_NUM_TASKS`` nodes joined; then launch
  ``python -m vllm.entrypoints.openai.api_server`` (with ``RAY_ADDRESS`` and
  ``TPU_MULTIHOST_BACKEND=ray`` in its env) and write the endpoint JSON the
  orchestrator consumes. On SIGTERM it terminates the api_server process group
  and stops Ray.
- **ranks 1..N-1 (workers):** read the head IP from the rendezvous, run
  ``ray start --address=<head_ip>:<port>``, verify they joined, then BLOCK
  until SIGTERM. They are the Ray worker nodes the RayDistributedExecutor
  schedules engine workers onto. They do NOT start an api_server, write
  endpoint JSON, or run harbor.

Head-IP discovery
-----------------
iris injects ``IRIS_ADVERTISE_HOST`` (the task's VPC-routable IP — see
``lib/iris/.../cluster/worker/task_attempt.py:_get_host_ip``) into every task,
so rank 0 uses that directly as the Ray head IP (falling back to a local
``socket`` probe). iris does NOT inject any peer/host list into the task env
(``TPU_WORKER_HOSTNAMES`` is collected controller-side as worker metadata, not
exposed to the task process), so we distribute the head IP to the worker ranks
via a small rendezvous file on the shared ``gs://`` job prefix the orchestrator
passes in (``--rendezvous-dir`` / ``OT_AGENT_IRIS_RENDEZVOUS_DIR``). Rank 0
writes ``ray_head.json``; ranks 1..N poll for it (with timeout).

CLI surface mirrors ``start_vllm_ray_controller.py`` so the orchestrator's
``start_vllm_controller`` / ``wait_for_endpoint`` contract is unchanged, with
two iris-specific additions: ``--rendezvous-dir`` and ``--ray-port`` (the head
port the cluster is bootstrapped on; ``--ray-address`` is no longer caller-
supplied because the head IP is discovered at runtime).
"""

from __future__ import annotations

import argparse
import json
import os
import hashlib
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

from hpc.iris.regions import region_from_metadata, region_local_output_prefix

RENDEZVOUS_FILENAME = "ray_head.json"

# How long worker ranks poll for the head's rendezvous file, and how long the
# head waits for all nodes to join the Ray cluster. Cold TPU workers can take a
# few minutes to reach this point (image build + uv sync + libtpu bring-up),
# so these are generous.
DEFAULT_RENDEZVOUS_TIMEOUT = 1200
DEFAULT_CLUSTER_JOIN_TIMEOUT = 1200
POLL_INTERVAL = 5


def _log(msg: str) -> None:
    print(f"[start_vllm_iris_controller] {msg}", flush=True)


def _rank() -> int:
    # IRIS_TASK_ID is the full task path (e.g. "/user/job/0"); on retried tasks
    # iris appends a ":N" retry suffix (e.g. "/user/job/0:2"). The rank is the
    # trailing path segment with any retry suffix stripped.
    return int(os.environ.get("IRIS_TASK_ID", "0").rsplit("/", 1)[-1].split(":", 1)[0])


def _num_tasks() -> int:
    return int(os.environ.get("IRIS_NUM_TASKS", "1"))


def _cpu_tag() -> str:
    """Stable short tag for the host CPU, used to namespace the XLA cache.

    The JAX persistent compile cache hashes the HLO graph + target hardware,
    but NOT the host CPU sub-revision. XLA's lowering passes can emit AVX-512
    vs AVX-256 host-side glue depending on the lowering machine's CPU; two
    hosts with the SAME model+TPU but DIFFERENT CPU microarchs would hash
    identical and poison each other's cache. Namespacing the cache subdir by
    CPU model avoids that. Reads /proc/cpuinfo's ``model name`` line (the
    best microarch proxy without parsing CPUID), hashes it. Returns
    "unknown" off-GCP (laptop/CI hosts share one subdir, never poisoning
    real workers).
    """
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    name = line.split(":", 1)[1].strip()
                    return hashlib.sha1(name.encode()).hexdigest()[:12]
    except FileNotFoundError:
        pass
    return "unknown"


def _model_tag(model: Optional[str]) -> str:
    """Short organizational tag for the model — last path component, sanitized.

    The JAX cache key already hashes the full HLO so this subdir level is
    purely for human-friendly cache hygiene (so you can ``gsutil rm -r``
    one model's cache without touching another's).
    """
    if not model:
        return "unknown"
    last = model.rstrip("/").rsplit("/", 1)[-1] or "unknown"
    # Strip characters that aren't safe in GCS object paths or that would
    # collide with siblings (just being defensive — gs:// is permissive).
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in last)


def _setup_xla_cache(model: Optional[str]) -> None:
    """Wire up the JAX persistent compile cache, namespaced per CPU+model.

    Reads ``OT_AGENT_XLA_CACHE_BASE`` (set by the iris launcher to the
    region-matched bucket prefix), appends per-CPU and per-model subdirs,
    and exports ``JAX_COMPILATION_CACHE_DIR`` so JAX/vLLM lowering picks
    it up. The env export reaches every subprocess we spawn (vllm serve,
    ray workers, engine cores).

    When the launcher did not set a base, falls back to this VM's own
    region-local bucket resolved from instance metadata
    (:func:`region_local_output_prefix`). No-op off-GCP (no metadata
    region) so laptop/CI runs don't fail.

    ``OT_AGENT_XLA_CACHE_BASE=disabled`` opts out entirely. Idempotent.
    """
    base = os.environ.get("OT_AGENT_XLA_CACHE_BASE", "").strip()
    if base.lower() == "disabled":
        return
    if not base:
        if region_from_metadata() is None:
            return  # Off-GCP (laptop/CI): no region-local bucket to fall back to.
        base = region_local_output_prefix("ot-agent/xla_cache")
        _log(f"XLA cache: OT_AGENT_XLA_CACHE_BASE unset; using region-local {base}")
    cache_dir = f"{base.rstrip('/')}/{_cpu_tag()}/{_model_tag(model)}"
    os.environ["JAX_COMPILATION_CACHE_DIR"] = cache_dir
    # Also surface for vLLM-TPU's lowering passes which look at this env
    # name in some code paths.
    os.environ.setdefault("XLA_PERSISTENT_CACHE_PATH", cache_dir)
    _log(
        f"XLA cache: {cache_dir} (cpu_tag={_cpu_tag()}, model_tag={_model_tag(model)})"
    )


def _own_ip() -> str:
    """Routable IP of this host.

    Prefers iris's ``IRIS_ADVERTISE_HOST`` (the VPC-routable IP iris computed
    for this task under ``--network=host``); falls back to a local UDP-socket
    probe identical to iris's own ``_get_host_ip``.
    """
    advertised = os.environ.get("IRIS_ADVERTISE_HOST")
    if advertised and advertised != "127.0.0.1":
        return advertised
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Rendezvous (GCS) — head publishes its IP, workers poll for it.
# ---------------------------------------------------------------------------


def _gcs_fs():
    """Return a gcsfs filesystem (the repo's established GCS helper).

    Mirrors ``scripts/iris/mirror_hf_to_gcs.py:_gcs_fs`` — uses gcsfs's default
    credential discovery (workload-identity on iris workers, ADC locally).
    """
    import gcsfs

    return gcsfs.GCSFileSystem()


def _rendezvous_uri(rendezvous_dir: str) -> str:
    return f"{rendezvous_dir.rstrip('/')}/{RENDEZVOUS_FILENAME}"


def write_rendezvous(rendezvous_dir: str, head_ip: str, ray_port: int) -> None:
    uri = _rendezvous_uri(rendezvous_dir)
    payload = {
        "head_ip": head_ip,
        "port": ray_port,
        "num_tasks": _num_tasks(),
        "written_at": time.time(),
    }
    fs = _gcs_fs()
    with fs.open(uri, "w") as f:
        json.dump(payload, f)
    _log(f"Wrote rendezvous {uri}: head_ip={head_ip} port={ray_port}")


# Slack for the rendezvous-freshness check. Tolerates clock skew between
# the head VM and worker VMs and the ~30s rank-0 needs to start Ray head
# in cases where workers race rank 0 on attempt 1.
RENDEZVOUS_FRESHNESS_SLACK = 60


def poll_rendezvous(
    rendezvous_dir: str,
    timeout: int,
    min_written_at: float | None = None,
) -> dict:
    """Poll for the head's rendezvous file. Returns its parsed payload.

    When ``min_written_at`` is provided, payloads with an older ``written_at``
    are treated as stale (from a prior iris task attempt) and ignored — the
    poller keeps waiting for a fresh write by rank 0. ``RENDEZVOUS_FRESHNESS_SLACK``
    seconds of slack apply, to absorb clock skew across VMs.
    """
    uri = _rendezvous_uri(rendezvous_dir)
    fs = _gcs_fs()
    deadline = time.time() + timeout
    threshold = (
        (min_written_at - RENDEZVOUS_FRESHNESS_SLACK) if min_written_at else None
    )
    if threshold is not None:
        _log(
            f"Polling for rendezvous {uri} (timeout {timeout}s, "
            f"min written_at {threshold:.0f})..."
        )
    else:
        _log(f"Polling for rendezvous {uri} (timeout {timeout}s)...")
    while time.time() < deadline:
        try:
            if fs.exists(uri):
                with fs.open(uri, "r") as f:
                    payload = json.load(f)
                if payload.get("head_ip"):
                    written_at = payload.get("written_at", 0)
                    if threshold is not None and written_at < threshold:
                        _log(
                            f"Ignoring stale rendezvous (written_at={written_at:.0f} "
                            f"< threshold={threshold:.0f}); waiting for rank-0 rewrite."
                        )
                    else:
                        _log(f"Found rendezvous: {payload}")
                        return payload
        except Exception as exc:  # pragma: no cover - transient GCS hiccup
            _log(f"rendezvous poll error (will retry): {exc}")
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(
        f"Worker rank {_rank()} timed out after {timeout}s waiting for "
        f"rank-0 rendezvous at {uri}. Did the head task fail to start?"
    )


def clear_rendezvous(rendezvous_dir: str) -> None:
    """Best-effort delete of the rendezvous file (rank 0, on exit)."""
    uri = _rendezvous_uri(rendezvous_dir)
    try:
        fs = _gcs_fs()
        if fs.exists(uri):
            fs.rm(uri)
            _log(f"Removed rendezvous {uri}")
    except Exception as exc:  # pragma: no cover
        _log(f"Warning: could not remove rendezvous {uri}: {exc}")


# ---------------------------------------------------------------------------
# Ray cluster bootstrap.
# ---------------------------------------------------------------------------


def ray_start_head(head_ip: str, ray_port: int) -> None:
    cmd = [
        "ray",
        "start",
        "--head",
        f"--node-ip-address={head_ip}",
        f"--port={ray_port}",
        "--dashboard-host=0.0.0.0",
    ]
    _log(f"Starting Ray HEAD: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def ray_start_worker(head_ip: str, ray_port: int, node_ip: str) -> None:
    cmd = [
        "ray",
        "start",
        f"--address={head_ip}:{ray_port}",
        f"--node-ip-address={node_ip}",
    ]
    _log(f"Starting Ray WORKER: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def ray_stop() -> None:
    try:
        subprocess.run(["ray", "stop", "--force"], check=False, timeout=60)
    except subprocess.TimeoutExpired:
        _log("Warning: 'ray stop' timed out")


def wait_for_nodes(ray_address: str, expected_nodes: int, timeout: int) -> None:
    """Block until the Ray cluster reports ``expected_nodes`` alive nodes."""
    import ray

    deadline = time.time() + timeout
    _log(
        f"Waiting for {expected_nodes} Ray node(s) at {ray_address} (timeout {timeout}s)..."
    )
    ray.init(address=ray_address, ignore_reinit_error=True)
    try:
        last_count = -1
        while time.time() < deadline:
            alive = [n for n in ray.nodes() if n.get("Alive")]
            count = len(alive)
            if count != last_count:
                _log(f"Ray nodes alive: {count}/{expected_nodes}")
                last_count = count
            if count >= expected_nodes:
                _log(
                    f"All {expected_nodes} Ray node(s) joined. Resources: {ray.cluster_resources()}"
                )
                return
            time.sleep(POLL_INTERVAL)
        raise TimeoutError(
            f"Only {last_count}/{expected_nodes} Ray nodes joined within {timeout}s."
        )
    finally:
        ray.shutdown()


# ---------------------------------------------------------------------------
# vLLM api_server command (mirrors start_vllm_ray_controller.build_vllm_command).
# ---------------------------------------------------------------------------


def build_vllm_command(args: argparse.Namespace, extra_args: List[str]) -> List[str]:
    model = args.model or os.environ.get("VLLM_MODEL_PATH")
    if not model:
        raise ValueError("--model or VLLM_MODEL_PATH environment variable is required")

    cmd: List[str] = [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        model,
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--tensor-parallel-size",
        str(args.tensor_parallel_size),
        # tpu_platform forces RayDistributedExecutor when TPU_MULTIHOST_BACKEND=ray;
        # passing the backend explicitly keeps the GPU/CPU path consistent too.
        "--distributed-executor-backend",
        "ray",
        "--trust-remote-code",
    ]

    if args.pipeline_parallel_size > 1:
        cmd.extend(["--pipeline-parallel-size", str(args.pipeline_parallel_size)])
    if args.data_parallel_size > 1:
        cmd.extend(["--data-parallel-size", str(args.data_parallel_size)])
    if args.served_model_name:
        cmd.extend(["--served-model-name", args.served_model_name])
    if extra_args:
        cmd.extend(extra_args)

    # Remote (object-store) model dir => vLLM needs the Run:ai model streamer to
    # read weights over the S3/GCS-compat endpoint. Auto-inject --load-format
    # runai_streamer when the model is an s3://|gs:// URI and no load-format is
    # already set. A local HF path/id is untouched.
    if model.startswith(("s3://", "gs://")) and not any(
        str(a).startswith(("--load-format", "--load_format")) for a in cmd
    ):
        cmd.extend(["--load-format", "runai_streamer"])
    return cmd


def write_endpoint_json(
    endpoint_json: Path,
    host: str,
    port: int,
    model: str,
    ray_address: str,
    args: argparse.Namespace,
) -> None:
    endpoint_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_name": args.served_model_name or model,
        "endpoint_url": f"http://{host}:{port}",
        "ray_address": ray_address,
        "created_by": "start_vllm_iris_controller",
        "metadata": {
            "tensor_parallel_size": args.tensor_parallel_size,
            "pipeline_parallel_size": args.pipeline_parallel_size,
            "data_parallel_size": args.data_parallel_size,
        },
    }
    endpoint_json.write_text(json.dumps(payload, indent=2))
    _log(f"Endpoint configuration written to {endpoint_json}")


# ---------------------------------------------------------------------------
# Argument parsing — mirrors start_vllm_ray_controller plus iris additions.
# ---------------------------------------------------------------------------


def parse_args() -> tuple[argparse.Namespace, List[str]]:
    parser = argparse.ArgumentParser(
        description="Launch a multi-host vLLM-TPU OpenAI endpoint on an iris slice "
        "by bootstrapping one cross-host Ray cluster. Unknown args pass through to vLLM.",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind interface for the API server."
    )
    parser.add_argument("--port", type=int, default=8000, help="API server port.")
    parser.add_argument(
        "--model", type=str, help="Model path (defaults to VLLM_MODEL_PATH)."
    )
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--pipeline-parallel-size", type=int, default=1)
    parser.add_argument("--data-parallel-size", type=int, default=1)
    parser.add_argument("--served-model-name", type=str, default=None)
    parser.add_argument(
        "--endpoint-json",
        type=Path,
        default=None,
        help="Path to write endpoint metadata JSON.",
    )
    parser.add_argument(
        "--ray-port",
        type=int,
        default=int(os.environ.get("OT_AGENT_IRIS_RAY_PORT", "6379")),
        help="Port the Ray head binds (default 6379).",
    )
    parser.add_argument(
        "--rendezvous-dir",
        default=os.environ.get("OT_AGENT_IRIS_RENDEZVOUS_DIR"),
        help="Shared gs:// dir for the head/worker rendezvous file. "
        "Defaults to $OT_AGENT_IRIS_RENDEZVOUS_DIR.",
    )
    parser.add_argument(
        "--rendezvous-timeout",
        type=int,
        default=DEFAULT_RENDEZVOUS_TIMEOUT,
        help=f"Seconds workers poll for the head rendezvous (default {DEFAULT_RENDEZVOUS_TIMEOUT}).",
    )
    parser.add_argument(
        "--cluster-join-timeout",
        type=int,
        default=DEFAULT_CLUSTER_JOIN_TIMEOUT,
        help=f"Seconds the head waits for all nodes to join (default {DEFAULT_CLUSTER_JOIN_TIMEOUT}).",
    )
    return parser.parse_known_args()


def _print_env_snapshot() -> None:
    _log("environment snapshot:")
    for key in (
        "IRIS_TASK_ID",
        "IRIS_NUM_TASKS",
        "IRIS_ADVERTISE_HOST",
        "JAX_PLATFORMS",
        "PJRT_DEVICE",
        "TPU_MULTIHOST_BACKEND",
        "RAY_ADDRESS",
        "HF_HOME",
        "MODEL_IMPL_TYPE",
        "OT_AGENT_XLA_CACHE_BASE",
        "JAX_COMPILATION_CACHE_DIR",
    ):
        print(f"  {key}={os.environ.get(key, '<unset>')}", flush=True)


# ---------------------------------------------------------------------------
# Roles.
# ---------------------------------------------------------------------------


def run_head(args: argparse.Namespace, extra_args: List[str]) -> int:
    num_tasks = _num_tasks()
    head_ip = _own_ip()
    ray_address = f"{head_ip}:{args.ray_port}"
    _log(f"ROLE=head rank=0/{num_tasks} head_ip={head_ip} ray_port={args.ray_port}")

    # On iris task retry (preemption), the rendezvous file from a previous
    # attempt still points at a now-dead head VM. Purge it before starting
    # the new Ray head so worker ranks don't race-read stale data.
    if num_tasks > 1 and args.rendezvous_dir:
        clear_rendezvous(args.rendezvous_dir)

    ray_start_head(head_ip, args.ray_port)

    # Publish the head IP so worker ranks can join. Single-host slices
    # (num_tasks==1) skip the rendezvous entirely.
    if num_tasks > 1:
        if not args.rendezvous_dir:
            raise ValueError(
                "Multi-host iris slice (IRIS_NUM_TASKS>1) requires --rendezvous-dir "
                "(or OT_AGENT_IRIS_RENDEZVOUS_DIR) so worker ranks can discover the head IP."
            )
        write_rendezvous(args.rendezvous_dir, head_ip, args.ray_port)
        wait_for_nodes(ray_address, num_tasks, args.cluster_join_timeout)
    else:
        _log("Single-host slice: skipping rendezvous and multi-node wait.")

    env = os.environ.copy()
    env["VLLM_MODEL_PATH"] = args.model or env.get("VLLM_MODEL_PATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    # The only supported multi-host vLLM-TPU serve path: force the Ray backend
    # and point vLLM's internal ray.init at our head.
    env["TPU_MULTIHOST_BACKEND"] = "ray"
    env["RAY_ADDRESS"] = ray_address

    cmd = build_vllm_command(args, extra_args)
    _log("Launching vLLM api_server:")
    _log("  " + " ".join(cmd))
    if extra_args:
        _log(f"  (pass-through args: {' '.join(extra_args)})")
    sys.stdout.flush()
    sys.stderr.flush()

    # start_new_session=True puts the child in its own process group so we can
    # signal the whole tree on shutdown (mirrors marin's vllm_server.py).
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        start_new_session=True,
    )

    def _tee_child_output() -> None:
        assert process.stdout is not None
        try:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
        except Exception as exc:  # pragma: no cover
            print(
                f"[start_vllm_iris_controller] tee error: {exc}",
                file=sys.stderr,
                flush=True,
            )

    threading.Thread(target=_tee_child_output, daemon=True).start()

    def _flush_loop() -> None:
        try:
            while process.poll() is None:
                sys.stdout.flush()
                sys.stderr.flush()
                time.sleep(5)
        except Exception:
            pass

    threading.Thread(target=_flush_loop, daemon=True).start()

    shutting_down = threading.Event()

    def _shutdown(signum, _frame) -> None:
        if shutting_down.is_set():
            return
        shutting_down.set()
        _log(
            f"Received signal {signum}; terminating api_server process group and stopping Ray..."
        )
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=30)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        if args.rendezvous_dir and num_tasks > 1:
            clear_rendezvous(args.rendezvous_dir)
        ray_stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Write the endpoint JSON once the server process is up (orchestrator's
    # wait_for_endpoint polls for this file; its run_endpoint_health_check
    # then waits for the HTTP endpoint to actually serve).
    if args.endpoint_json:
        model = args.model or os.environ.get("VLLM_MODEL_PATH", "unknown")
        write_endpoint_json(
            args.endpoint_json, args.host, args.port, model, ray_address, args
        )

    exit_code = process.wait()
    if args.rendezvous_dir and num_tasks > 1:
        clear_rendezvous(args.rendezvous_dir)
    ray_stop()
    return exit_code


def run_worker(args: argparse.Namespace) -> int:
    worker_start = time.time()
    rank = _rank()
    num_tasks = _num_tasks()
    node_ip = _own_ip()
    _log(f"ROLE=worker rank={rank}/{num_tasks} node_ip={node_ip}")

    if not args.rendezvous_dir:
        raise ValueError(
            "Worker rank requires --rendezvous-dir (or OT_AGENT_IRIS_RENDEZVOUS_DIR) "
            "to discover the head IP."
        )

    # Pass worker_start as the freshness floor: on preempt-retry, the
    # rendezvous file from a prior attempt is older than this worker's
    # restart time, so it's rejected and we wait for rank-0's rewrite.
    payload = poll_rendezvous(
        args.rendezvous_dir,
        args.rendezvous_timeout,
        min_written_at=worker_start,
    )
    head_ip = payload["head_ip"]
    ray_port = int(payload.get("port", args.ray_port))
    ray_address = f"{head_ip}:{ray_port}"

    ray_start_worker(head_ip, ray_port, node_ip)
    # Verify this node actually joined before parking. This connects as a
    # driver to the local raylet, which is up after ray_start_worker returns.
    wait_for_nodes(ray_address, num_tasks, args.cluster_join_timeout)
    _log(
        f"Worker rank {rank} joined Ray cluster at {ray_address}; parking until SIGTERM."
    )

    stop = threading.Event()

    def _shutdown(signum, _frame) -> None:
        _log(f"Worker rank {rank} received signal {signum}; stopping Ray.")
        stop.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Block until signalled. The api_server on rank 0 schedules engine workers
    # onto this Ray node; this process just keeps the node alive.
    stop.wait()
    ray_stop()
    return 0


def main() -> None:
    args, extra_args = parse_args()
    # Set up the JAX persistent compile cache before _print_env_snapshot
    # so the snapshot logs the resolved cache dir, and before any code path
    # (head or worker) spawns subprocesses — those subprocesses inherit
    # JAX_COMPILATION_CACHE_DIR via os.environ.
    _setup_xla_cache(args.model)
    _print_env_snapshot()
    rank = _rank()
    if rank == 0:
        exit_code = run_head(args, extra_args)
    else:
        exit_code = run_worker(args)
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
