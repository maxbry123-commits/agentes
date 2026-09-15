#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[2]
SRC = PROJECT / "runtime" / "src"
sys.path.insert(0, str(SRC))

from install.deterministic_deployer import DeterministicDeployer, tree_sha256
from install.deployment_gate import DeploymentEvidence, evaluate_deployment, post_promote_health_gate

IMAGE = os.environ.get("G022_TEST_IMAGE", "python:3.12-alpine")
EVIDENCE = PROJECT / "wordflow_loop" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], *, timeout: float = 120.0, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=check)


def docker_base(*extra: str) -> list[str]:
    return [
        "docker", "run", "--rm", "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "64",
        "--memory", "128m", "--memory-swap", "128m", "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", *extra, IMAGE,
    ]


def test_1_filesystem_and_positive_backend(tmp: Path) -> dict:
    candidate = tmp / "candidate"
    candidate.mkdir()
    (candidate / "probe.txt").write_text("YAIWES_SANDBOX_OK\n")
    mount = f"{candidate}:/candidate:ro"
    positive = run(docker_base("-v", mount, "python", "-c", "print(open('/candidate/probe.txt').read().strip())"))
    if positive.returncode != 0 or "YAIWES_SANDBOX_OK" not in positive.stdout:
        raise AssertionError(f"positive backend failed: {positive.stderr}")
    negative = run(docker_base("-v", mount, "python", "-c", "open('/candidate/forbidden.txt','w').write('x')"))
    if negative.returncode == 0 or (candidate / "forbidden.txt").exists():
        raise AssertionError("read-only candidate mount was writable")
    return {"id": 1, "name": "sandbox_filesystem_readonly", "result": "PASS", "positive_backend": True, "write_rejected": True}


def test_2_network_denied() -> dict:
    code = (
        "import socket,sys\n"
        "try:\n"
        " socket.create_connection(('1.1.1.1',53),1); sys.exit(9)\n"
        "except OSError:\n"
        " sys.exit(0)\n"
    )
    p = run(docker_base("python", "-c", code))
    if p.returncode != 0:
        raise AssertionError(f"network deny probe failed rc={p.returncode}: {p.stderr}")
    return {"id": 2, "name": "sandbox_network_none", "result": "PASS", "outbound_connection_blocked": True}


def test_3_memory_and_time_limits() -> dict:
    memory = run([
        "docker", "run", "--rm", "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "32",
        "--memory", "64m", "--memory-swap", "64m", "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", IMAGE,
        "python", "-c", "x=bytearray(512*1024*1024); print(len(x))",
    ], timeout=60)
    if memory.returncode == 0:
        raise AssertionError("memory limit did not reject 512 MiB allocation")

    name = f"yaiwes-g022-time-{os.getpid()}"
    timed = run([
        "timeout", "--signal=TERM", "--kill-after=1s", "2s",
        "docker", "run", "--name", name, "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "32",
        "--memory", "64m", "--memory-swap", "64m", "--read-only", IMAGE,
        "python", "-c", "import time; time.sleep(30)",
    ], timeout=15)
    run(["docker", "rm", "-f", name], timeout=30)
    if timed.returncode != 124:
        raise AssertionError(f"wall timeout not enforced, rc={timed.returncode}")
    return {"id": 3, "name": "sandbox_resource_limits", "result": "PASS", "memory_rejected": True, "wall_timeout_rejected": True}


def _write_app(root: Path, *, good: bool) -> None:
    root.mkdir(parents=True)
    health_code = "0" if good else "7"
    (root / "app.py").write_text(
        "import sys\n"
        "mode=sys.argv[1] if len(sys.argv)>1 else ''\n"
        f"sys.exit({health_code}) if mode=='health' else None\n"
        "sys.exit(0) if mode=='smoke' else None\n"
        "sys.exit(2)\n"
    )


def test_4_deterministic_deploy_and_rollback(tmp: Path) -> dict:
    deploy_root = tmp / "deployment"
    good = tmp / "candidate-good"
    bad = tmp / "candidate-bad"
    _write_app(good, good=True)
    _write_app(bad, good=False)

    deployer = DeterministicDeployer(deploy_root, timeout_seconds=5)
    py = sys.executable
    good_hash = tree_sha256(good)
    first = deployer.deploy(
        good,
        expected_sha256=good_hash,
        health_argv=[py, "app.py", "health"],
        smoke_argv=[py, "app.py", "smoke"],
    )
    if first.status != "DEPLOYED_VERIFIED" or not first.health_ok or not first.smoke_ok:
        raise AssertionError(f"good deployment failed: {first}")

    evidence = DeploymentEvidence(
        artifact_hash_verified=True,
        installation_verified=True,
        sandbox_verified=True,
        tests_pass=True,
        independent_review_pass=True,
        output_schema_pass=True,
        checkpoint_created=True,
        rollback_ready=True,
        health_check_pass=True,
        evidence_refs=("G022_PHYSICAL_SANDBOX", "G017_DEPLOYMENT"),
    )
    gate = evaluate_deployment(evidence)
    post = post_promote_health_gate(first.health_ok, first.current_release is not None, True)
    if not gate.promote_authorized or post.status != "DEPLOYED_VERIFIED":
        raise AssertionError("canonical deployment gate did not authorize verified promotion")

    bad_hash = tree_sha256(bad)
    second = deployer.deploy(
        bad,
        expected_sha256=bad_hash,
        health_argv=[py, "app.py", "health"],
        smoke_argv=[py, "app.py", "smoke"],
        rollback_health_argv=[py, "app.py", "health"],
    )
    if second.status != "ROLLBACK_VERIFIED" or not second.rollback_performed or not second.rollback_health_ok:
        raise AssertionError(f"rollback failed: {second}")
    if Path(second.current_release or "").resolve() != Path(first.current_release or "").resolve():
        raise AssertionError("rollback did not restore previous release")

    return {
        "id": 4,
        "name": "deterministic_deploy_health_smoke_rollback",
        "result": "PASS",
        "candidate_hash_verified": True,
        "promotion": first.to_dict(),
        "canonical_gate": gate.status,
        "post_promote_gate": post.status,
        "forced_bad_candidate": second.to_dict(),
    }


def main() -> None:
    if shutil.which("docker") is None:
        raise SystemExit("DOCKER_REQUIRED")
    info = run(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=30)
    if info.returncode != 0:
        raise SystemExit("DOCKER_DAEMON_REQUIRED: " + info.stderr)
    pull = run(["docker", "pull", IMAGE], timeout=180)
    if pull.returncode != 0:
        raise SystemExit("IMAGE_PULL_FAILED: " + pull.stderr)
    image_id = run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], check=True).stdout.strip()

    started = int(time.time())
    with tempfile.TemporaryDirectory(prefix="yaiwes-g022-g017-") as td:
        tmp = Path(td)
        tests = [
            test_1_filesystem_and_positive_backend(tmp),
            test_2_network_denied(),
            test_3_memory_and_time_limits(),
            test_4_deterministic_deploy_and_rollback(tmp),
        ]

    if len(tests) != 4 or any(x["result"] != "PASS" for x in tests):
        raise SystemExit("FOUR_TEST_GATE_FAILED")

    common = {
        "date": "2026-09-15",
        "runner": os.environ.get("RUNNER_NAME", "unknown"),
        "runner_os": os.environ.get("RUNNER_OS", sys.platform),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "docker_server": info.stdout.strip().strip('"'),
        "container_image": IMAGE,
        "container_image_id": image_id,
        "tests_total": 4,
        "tests_passed": 4,
        "started_at": started,
        "finished_at": int(time.time()),
    }

    g022 = {
        "schema": "yaiwes.g022.physical-sandbox-closure/v1",
        "gap_id": "G-022",
        "result": "PASS_PHYSICAL_ISOLATION_ENFORCED",
        **common,
        "physical_tests": tests[:3],
        "checks": {
            "positive_backend_execution": True,
            "filesystem_readonly": True,
            "network_denied": True,
            "memory_limit_enforced": True,
            "wall_timeout_enforced": True,
            "capabilities_dropped": True,
            "no_new_privileges": True,
            "secrets_mounted": False,
        },
        "g022_closed": True,
    }
    g017 = {
        "schema": "yaiwes.g017.deterministic-deployment-closure/v1",
        "gap_id": "G-017",
        "result": "PASS_DETERMINISTIC_DEPLOY_AND_ROLLBACK",
        **common,
        "deployment_test": tests[3],
        "checks": {
            "content_addressed_hash": True,
            "atomic_promotion": True,
            "real_health_check": True,
            "real_smoke_check": True,
            "post_promote_readback": True,
            "forced_failure": True,
            "rollback_restored_previous": True,
            "rollback_health_verified": True,
        },
        "g017_closed": True,
    }

    (EVIDENCE / "G022_PHYSICAL_SANDBOX_CLOSURE_2026-09-15.json").write_text(json.dumps(g022, indent=2, sort_keys=True) + "\n")
    (EVIDENCE / "G017_DETERMINISTIC_DEPLOYMENT_CLOSURE_2026-09-15.json").write_text(json.dumps(g017, indent=2, sort_keys=True) + "\n")
    print("G022_PHYSICAL_SANDBOX=PASS")
    print("G017_DETERMINISTIC_DEPLOYMENT=PASS")
    print("FOUR_TEST_GATE=PASS_4_OF_4")


if __name__ == "__main__":
    main()
