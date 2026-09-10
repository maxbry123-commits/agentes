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

MOTOR = Path("➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de moves archivos/motor_4_move_batches.py")
ROOT = Path("Agente Yaiwes principal")

COMPONENTS = [
    (1, "APScheduler", ROOT / "execution-orchestration/task-classifier-scheduler"),
    (2, "AWS-Step-Functions-DS-SDK", ROOT / "execution-orchestration/state-machine-executor/aws-step-functions-ds-sdk"),
    (3, "Ajv", ROOT / "definition-registry/schema-contracts/ajv"),
    (4, "Apache-APISIX", ROOT / "mesh-routing-collaboration/apisix-api-gateway"),
    (5, "Apache-Airflow", ROOT / "execution-orchestration/dag-executor/apache-airflow"),
    (6, "Argo-Workflows", ROOT / "execution-orchestration/dag-executor/argo-workflows"),
    (7, "Azure-Durable-Functions", ROOT / "execution-orchestration/state-machine-executor/azure-durable-functions"),
    (8, "BAML", ROOT / "definition-registry/domain-specific-contracts/baml"),
    (9, "Burr", ROOT / "execution-orchestration/state-machine-executor/burr"),
    (10, "Caddy", ROOT / "mesh-routing-collaboration/caddy-gateway"),
    (11, "Camunda", ROOT / "execution-orchestration/state-machine-executor/camunda"),
    (12, "Cedar", ROOT / "definition-registry/authorization-model/cedar"),
    (13, "Celery", ROOT / "execution-engine-pool/parallel-dispatch/celery"),
    (14, "Cerberus", ROOT / "definition-registry/schema-contracts/cerberus"),
    (15, "Cerbos", ROOT / "control-governance/policy-guardrails-permissions/cerbos"),
    (16, "Chroma", ROOT / "tools-models-memory-knowledge/memory-microservices/chroma"),
    (17, "ClawHub", ROOT / "kernel-principal/extension-kernel/capability-registry/clawhub"),
    (18, "Cloudflare-Workers-SDK", ROOT / "execution-engine-pool/adapter-layer/cloudflare-workers-sdk"),
    (19, "Coconut", ROOT / "kernel-principal/reasoning-kernel/decision-on-demand/coconut"),
    (20, "CodeUltraFeedback", ROOT / "code-programming-engine/standards-forensic/code-ultrafeedback"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def has_files(path: Path) -> bool:
    return path.is_dir() and any(p.is_file() for p in path.rglob("*"))


def source_candidates(name: str) -> list[Path]:
    return [
        Path(f"Core kernel Yaiwes/Componentes recuperados B/{name}/{name}"),
        Path(f"Core kernel Yaiwes/Componentes recuperados B/{name}"),
        Path(f"Core kernel Yaiwes/Componentes recuperados A/{name}/{name}"),
        Path(f"Core kernel Yaiwes/Componentes recuperados A/{name}"),
        Path(f"Core kernel Yaiwes/{name}"),
    ]


def find_source(name: str) -> Path | None:
    for p in source_candidates(name):
        if has_files(p):
            return p
    return None


def unique_preserve_path(base: Path, original: Path) -> Path:
    if not base.exists():
        return base
    if base.is_file() and original.is_file() and sha256_file(base) == sha256_file(original):
        return base
    suffix = sha256_file(original)[:12] if original.is_file() else "directory"
    candidate = base.with_name(base.name + "." + suffix)
    n = 1
    while candidate.exists():
        candidate = base.with_name(base.name + f".{suffix}.{n}")
        n += 1
    return candidate


def preserve_conflicts(src: Path, dest: Path, name: str) -> list[str]:
    preserve_root = dest / ".yaiwes-pre-move-preserved"
    preserved: list[str] = []
    for s in sorted((p for p in src.rglob("*") if p.is_file()), key=lambda p: p.relative_to(src).as_posix()):
        rel = s.relative_to(src)
        d = dest / rel

        # Parent type conflicts would prevent Motor4 from creating destination parents.
        parent = d.parent
        while parent != dest and parent != parent.parent:
            if parent.exists() and parent.is_file():
                parent_rel = parent.relative_to(dest)
                keep = unique_preserve_path(preserve_root / "__parent_type_conflicts__" / parent_rel, parent)
                keep.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(parent), str(keep))
                preserved.append(f"PARENT_TYPE:{parent_rel}->{keep.relative_to(dest)}")
            parent = parent.parent

        if not d.exists():
            continue
        if d.is_file() and sha256_file(d) == sha256_file(s):
            continue

        keep = unique_preserve_path(preserve_root / rel, d)
        keep.parent.mkdir(parents=True, exist_ok=True)
        if keep.exists() and keep.is_file() and d.is_file() and sha256_file(keep) == sha256_file(d):
            d.unlink()
        else:
            shutil.move(str(d), str(keep))
        preserved.append(f"{rel.as_posix()}->{keep.relative_to(dest).as_posix()}")

    for item in preserved:
        print(f"PRESERVED_DEST_CONFLICT {name} {item}")
    print(f"PRESERVED_DEST_CONFLICTS_TOTAL {name} {len(preserved)}")
    return preserved


def run_motor(number: int, name: str, src: Path, dest: Path) -> dict:
    state = Path(tempfile.gettempdir()) / f"yaiwes-motor4-{number}.json"
    if state.exists():
        state.unlink()
    env = os.environ.copy()
    env.update({
        "SOURCE_DIR": str(src),
        "DEST_DIR": str(dest),
        "STATE_FILE": str(state),
        "BATCH_SIZE": "100",
        "COLLISION_POLICY": "fail",
    })
    proc = subprocess.run([sys.executable, str(MOTOR)], env=env, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if proc.returncode != 0:
        if state.exists():
            print(state.read_text())
        raise RuntimeError(f"MOTOR4_PROCESS_FAILED:{name}:{proc.returncode}")
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    if not (
        result.get("verdict") == "VERIFIED_CLOSED"
        and result.get("failed") == 0
        and result.get("pending") == 0
        and result.get("source_files_remaining") == 0
    ):
        if state.exists():
            print(state.read_text())
        raise RuntimeError(f"MOTOR4_GAP:{name}:{result}")
    return result


def main() -> int:
    if not MOTOR.is_file():
        raise RuntimeError("CANONICAL_MOTOR4_NOT_FOUND")
    report = []
    for number, name, dest in COMPONENTS:
        src = find_source(name)
        if src is None:
            if has_files(dest):
                row = {"number": number, "name": name, "status": "DEST_ONLY_VERIFIED", "destination": str(dest)}
                report.append(row)
                print(json.dumps(row, ensure_ascii=False, sort_keys=True))
                continue
            raise RuntimeError(f"SOURCE_AND_DEST_GAP:{number}:{name}:{dest}")

        dest.mkdir(parents=True, exist_ok=True)
        preserved = preserve_conflicts(src, dest, name)
        result = run_motor(number, name, src, dest)
        row = {
            "number": number,
            "name": name,
            "status": "MOVED_OR_DEDUP_VERIFIED",
            "source": str(src),
            "destination": str(dest),
            "preserved_destination_conflicts": len(preserved),
            "motor4": result,
        }
        report.append(row)
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))

    if len(report) != 20:
        raise RuntimeError(f"REPORT_COUNT_GAP:{len(report)}")
    if any(not has_files(dest) for _, _, dest in COMPONENTS):
        raise RuntimeError("DESTINATION_READBACK_GAP")

    final = {
        "schema": "yaiwes.motor4.move-20/v1",
        "verdict": "VERIFIED_CLOSED",
        "components_total": 20,
        "components": report,
    }
    print("MOTOR4_MOVE_20_FINAL=" + json.dumps(final, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
