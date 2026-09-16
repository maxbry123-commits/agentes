from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

SCHEMA = "yaiwes.agent-source-copy-evidence/v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_dir(root: Path, *, max_file_bytes: int) -> tuple[list[dict[str, Any]], str]:
    if not root.is_dir():
        raise RuntimeError(f"SOURCE_DIR_NOT_FOUND:{root}")
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink():
            raise RuntimeError(f"SYMLINK_REJECTED:{path.relative_to(root).as_posix()}")
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            raise RuntimeError(f"FILE_TOO_LARGE:{path.relative_to(root).as_posix()}:{size}")
        rows.append({
            "rel": path.relative_to(root).as_posix(),
            "bytes": size,
            "sha256": sha256_file(path),
        })
    digest = hashlib.sha256()
    for row in rows:
        digest.update(f"{row['rel']}\0{row['bytes']}\0{row['sha256']}\n".encode("utf-8"))
    return rows, digest.hexdigest()


def load_gate(path: Path):
    spec = importlib.util.spec_from_file_location("yaiwes_canonical_motor_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CANONICAL_GATE_IMPORT_GAP")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_motor_stdout(stdout: str) -> dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("COPY_MOTOR_EMPTY_STDOUT")
    return json.loads(lines[-1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--external-root", required=True)
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    external_root = Path(args.external_root).resolve()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    authorized_root = (repo_root / plan["authorized_root"]).resolve()
    destination_root = (repo_root / plan["destination_root"]).resolve()
    evidence_dir = authorized_root / "wordflow_loop" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    state_dir = evidence_dir / "agent-source-copy-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "AGENT_SOURCE_COPY_2026-09-15.json"

    gate_path = authorized_root / "runtime" / "src" / "core" / "canonical_motor_gate.py"
    gate = load_gate(gate_path)
    motor_lock = gate.verify_motor(repo_root, "copy")
    if motor_lock["actual_blob_sha"] != plan["copy_motor_expected_git_blob"]:
        raise RuntimeError("PLAN_MOTOR_BLOB_MISMATCH")
    motor_path = repo_root / str(motor_lock["motor_path"])

    max_file_bytes = int(plan["rules"]["max_file_bytes"])
    batch_size = int(plan["rules"]["batch_size"])
    results: list[dict[str, Any]] = []
    resolved_total = 0
    verified_total = 0
    failures = 0

    for entry in plan["agents"]:
        agent_id, checkout, source_path, source_kind = entry
        destination = destination_root / agent_id
        if checkout == "unresolved":
            results.append({
                "agent_id": agent_id,
                "status": "UNRESOLVED_SOURCE",
                "detail": plan.get("unresolved", {}).get(agent_id, "UNRESOLVED"),
                "destination": str(destination.relative_to(repo_root)),
            })
            continue

        resolved_total += 1
        source_base = repo_root if checkout == "target" else external_root
        source = (source_base / str(source_path)).resolve()
        row: dict[str, Any] = {
            "agent_id": agent_id,
            "checkout": checkout,
            "source_path": source_path,
            "source_kind": source_kind,
            "destination": str(destination.relative_to(repo_root)),
        }
        try:
            if source_kind != "dir":
                raise RuntimeError("DIRECTORY_SOURCE_REQUIRED_BY_CANONICAL_MOTOR")
            source_rows, source_digest = manifest_dir(source, max_file_bytes=max_file_bytes)
            if not source_rows:
                raise RuntimeError("SOURCE_EMPTY")

            state_file = state_dir / f"{agent_id}.json"
            motor_env = gate.build_motor_env(
                source,
                destination,
                state_file,
                authorized_root=authorized_root,
                mutation_authorized=True,
            )
            motor_env["BATCH_SIZE"] = str(batch_size)
            motor_env["COLLISION_POLICY"] = "fail"
            proc = subprocess.run(
                [sys.executable, str(motor_path)],
                cwd=str(repo_root),
                env={**os.environ, **motor_env},
                capture_output=True,
                text=True,
                check=False,
            )
            motor_result = parse_motor_stdout(proc.stdout)
            if proc.returncode != 0 or motor_result.get("verdict") != "VERIFIED_CLOSED":
                raise RuntimeError(
                    f"COPY_MOTOR_NOT_VERIFIED:rc={proc.returncode}:verdict={motor_result.get('verdict')}"
                )

            dest_rows, dest_digest = manifest_dir(destination, max_file_bytes=max_file_bytes)
            if source_rows != dest_rows or source_digest != dest_digest:
                raise RuntimeError("SOURCE_DESTINATION_MANIFEST_MISMATCH")

            verified_total += 1
            row.update({
                "status": "COPIED_AND_READBACK_VERIFIED",
                "file_count": len(source_rows),
                "bytes_total": sum(item["bytes"] for item in source_rows),
                "manifest_sha256": source_digest,
                "motor_verdict": motor_result.get("verdict"),
                "motor_blob_sha": motor_lock["actual_blob_sha"],
                "state_file": str(state_file.relative_to(repo_root)),
            })
        except Exception as exc:
            failures += 1
            row.update({"status": "GAP", "detail": str(exc)})
        results.append(row)

    unresolved_total = len(plan["agents"]) - resolved_total
    if failures:
        verdict = "GAPS_PENDING"
    elif unresolved_total:
        verdict = f"PARTIAL_VERIFIED_{verified_total}_OF_{len(plan['agents'])}"
    else:
        verdict = f"VERIFIED_{verified_total}_OF_{len(plan['agents'])}"

    evidence = {
        "schema": SCHEMA,
        "verdict": verdict,
        "plan": str(plan_path.relative_to(repo_root)),
        "external_source_repo": plan["external_source_repo"],
        "external_source_commit": plan["external_source_commit"],
        "canonical_copy_motor": {
            "path": motor_lock["motor_path"],
            "blob_sha": motor_lock["actual_blob_sha"],
            "verified": motor_lock["verified"],
        },
        "agents_total": len(plan["agents"]),
        "resolved_total": resolved_total,
        "verified_total": verified_total,
        "unresolved_total": unresolved_total,
        "failures": failures,
        "presence_is_not_runtime_integration": True,
        "results": results,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA,
        "verdict": verdict,
        "verified_total": verified_total,
        "agents_total": len(plan["agents"]),
        "unresolved_total": unresolved_total,
        "failures": failures,
        "evidence": str(evidence_path.relative_to(repo_root)),
    }, ensure_ascii=False, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
