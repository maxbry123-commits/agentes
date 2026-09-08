#!/usr/bin/env python3
"""YAIWES multi-watchdog acquisition preflight.

Base de trabajo: research-download-chain, plantilla canónica fijada en
c789e5fe635e220230ffc759d86dc3bbb8e261d4. Esta fase NO publica vendor code:
descarga cada fuente a staging del runner, valida SHA/licencia/LFS/tamaño y
produce el inventario que determina selected_paths para EXTRACTED_TREE.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path.cwd()
CONTRACT = REPO / "Core kernel Yaiwes/Backend watchdog workflow adaptativo/ACQUISITION_CONTRACT.json"
DEST = REPO / "Core kernel Yaiwes/Backend watchdog workflow adaptativo"
PREFLIGHT = DEST / "preflight"
MANIFEST = PREFLIGHT / "PREFLIGHT_MANIFEST.jsonl"
WORK = REPO / "_work/yaiwes-watchdog-backends-preflight-v1"
SRC = WORK / "src"
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
POINTER_SCAN_BYTES = 1024
GIT_BLOB_LIMIT = 100 * 1024 * 1024
README = REPO / "Readme arquitectura Yaiwes/README.md"
STATE = REPO / "Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json"
README_MARKER = "<!-- YAIWES_MULTI_WATCHDOG_BACKEND_V1 -->"


def run(cmd, cwd=None, capture=False):
    kwargs = {"cwd": cwd, "check": True, "text": True}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
    return subprocess.run(cmd, **kwargs)


def git_env_hardening():
    for key, value in (
        ("filter.lfs.clean", "cat"),
        ("filter.lfs.smudge", "cat"),
        ("filter.lfs.process", ""),
        ("filter.lfs.required", "false"),
    ):
        run(["git", "config", "--local", key, value])


def clone_pinned(url, sha, root):
    last = None
    for attempt in range(1, 4):
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        try:
            run(["git", "init", "-q"], cwd=root)
            run(["git", "config", "filter.lfs.clean", "cat"], cwd=root)
            run(["git", "config", "filter.lfs.smudge", "cat"], cwd=root)
            run(["git", "config", "filter.lfs.process", ""], cwd=root)
            run(["git", "config", "filter.lfs.required", "false"], cwd=root)
            run(["git", "remote", "add", "origin", url + ".git"], cwd=root)
            run(["git", "fetch", "--depth=1", "--no-tags", "origin", sha], cwd=root)
            run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=root)
            got = run(["git", "rev-parse", "HEAD"], cwd=root, capture=True).stdout.strip()
            if got != sha:
                raise RuntimeError(f"SOURCE_REF_MISMATCH expected={sha} got={got}")
            return
        except Exception as exc:
            last = exc
            if attempt == 3:
                break
            time.sleep(attempt * 5)
    raise last


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_lfs_pointer(path):
    try:
        if not path.is_file() or path.stat().st_size > POINTER_SCAN_BYTES:
            return False
        with path.open("rb") as f:
            return f.read(POINTER_SCAN_BYTES).startswith(LFS_PREFIX)
    except OSError:
        return False


def inventory(root):
    files = []
    top = {}
    lfs = []
    oversized = []
    licenses = []
    aggregate = hashlib.sha256()
    total_bytes = 0
    max_blob = {"path": None, "bytes": 0}
    for p in sorted(x for x in root.rglob("*") if x.is_file() and ".git" not in x.parts):
        rel = p.relative_to(root).as_posix()
        size = p.stat().st_size
        total_bytes += size
        if size > max_blob["bytes"]:
            max_blob = {"path": rel, "bytes": size}
        if size >= GIT_BLOB_LIMIT:
            oversized.append({"path": rel, "bytes": size})
        if is_lfs_pointer(p):
            lfs.append(rel)
        name_upper = p.name.upper()
        if len(p.relative_to(root).parts) == 1 and (
            name_upper.startswith("LICENSE") or name_upper.startswith("COPYING") or name_upper.startswith("NOTICE")
        ):
            licenses.append({"path": rel, "sha256": sha256_file(p), "bytes": size})
        top_name = p.relative_to(root).parts[0]
        bucket = top.setdefault(top_name, {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += size
        digest = sha256_file(p)
        aggregate.update(rel.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
        files.append((rel, size))
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "max_blob": max_blob,
        "top_level_inventory": dict(sorted(top.items())),
        "licenses": licenses,
        "lfs_pointer_count": len(lfs),
        "lfs_pointers": lfs[:100],
        "oversized_blob_count": len(oversized),
        "oversized_blobs": oversized[:100],
        "deterministic_tree_sha256": aggregate.hexdigest(),
    }


def update_architecture_pending():
    if not README.exists():
        raise RuntimeError("ARCHITECTURE_README_MISSING")
    text = README.read_text(encoding="utf-8")
    if README_MARKER in text:
        return
    block = f"""

{README_MARKER}
## Integración — Sistema adaptativo Multi-Watchdog / programación de tareas — PENDIENTE

**Estado:** `PENDIENTE` hasta descarga `EXTRACTED_TREE`, adapter/Ficha v2/WIRING, runtime real, UniversalPluginBus, health/evidence, memoria+sandbox y read-back independiente.

**Bitácora activa:** [Crack wall bitácora stated JSON / STATE.json](https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/STATE.json)

**Flujo horizontal:** `Tarea programada → Registry → Scheduler/Trigger → Priority Queue → Workflow Adapter → Worker/Sandbox → Checkpoint → Resultado/Evidence`.

**Flujo transversal:** `Agente → planifica/divide → selecciona workflow por duración/durabilidad/prioridad/paralelismo → memoria persistente → ejecución fan-out/fan-in → recovery → estado → UI event stream`.

**Backends aprobados:** Windmill · Kestra · Apache DolphinScheduler · Rundeck · Temporal · Prefect · Dagu · Cronicle · Hatchet · Trigger.dev.
"""
    README.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def update_state(summary):
    if not STATE.exists():
        return
    data = json.loads(STATE.read_text(encoding="utf-8"))
    data["multi_watchdog_backend_v1"] = {
        "status": "PENDIENTE_PREFLIGHT",
        "task_id": "YAIWES-WATCHDOG-BACKENDS-10-V1",
        "destination": "Core kernel Yaiwes/Backend watchdog workflow adaptativo",
        "components_expected": 10,
        "preflight_reports": summary,
        "next_gate": "SELECTED_PATHS_FROM_REAL_SOURCE_TREE",
        "source_of_truth": "physical_repo_state"
    }
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    git_env_hardening()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    required = ["destination_repository", "destination_branch", "destination_root", "components", "rules"]
    missing = [k for k in required if not contract.get(k)]
    if missing:
        raise RuntimeError("INPUT_GAP: " + ",".join(missing))
    PREFLIGHT.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    results = []
    MANIFEST.unlink(missing_ok=True)
    for idx, component in enumerate(contract["components"], 1):
        name = component["name"]
        slug = name.lower().replace(".", "-").replace(" ", "-")
        url = component["source_url"].rstrip("/").removesuffix(".git")
        sha = component["source_ref"]
        root = SRC / slug
        print(f"===== PREFLIGHT {idx}/10 {name} {sha} =====", flush=True)
        record = {
            "task_id": contract["task_id"],
            "index": idx,
            "name": name,
            "slug": slug,
            "source_url": url,
            "source_commit": sha,
            "mode": "DOWNLOAD",
            "delivery": "EXTRACTED_TREE_AFTER_PREFLIGHT",
        }
        try:
            clone_pinned(url, sha, root)
            inv = inventory(root)
            record.update(inv)
            if inv["lfs_pointer_count"]:
                record["status"] = "SOURCE_LFS_POINTER_GAP"
            elif inv["oversized_blob_count"]:
                record["status"] = "GIT_BLOB_LIMIT_GAP"
            elif not inv["licenses"]:
                record["status"] = "LICENSE_IDENTIFICATION_GAP"
            else:
                record["status"] = "PREFLIGHT_PASS"
        except Exception as exc:
            record["status"] = "PREFLIGHT_GAP"
            record["error"] = str(exc)
        finally:
            shutil.rmtree(root, ignore_errors=True)
        (PREFLIGHT / f"{idx:02d}-{slug}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with MANIFEST.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        results.append({"name": name, "status": record["status"]})
        print(f"{name}: {record['status']}", flush=True)
    update_architecture_pending()
    update_state(results)
    shutil.rmtree(WORK, ignore_errors=True)
    print("PREFLIGHT_SUMMARY", json.dumps(results, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
