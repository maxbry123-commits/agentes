from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import canonical_motor_gate as gate
from agent_source_copy_runner import manifest_dir, parse_motor_stdout

SOURCE_REPO = "aaif-goose/goose"
SOURCE_COMMIT = "a23a8cd5b138954bc8962cba623c2d8ecd375512"
DOWNLOAD_ENGINE_EXPECTED_BLOB = "91e6e4486692eab314be5c7130d8310d3c855397"
COPY_MOTOR_EXPECTED_BLOB = "3689924361ce4a1a9fde4ae2b6f6009c37a6042d"
SCHEMA = "yaiwes.goose-official-acquisition/v1"
NORMALIZATION_STRATEGY = "TRACKED_INTERNAL_SYMLINKS_MATERIALIZED_TO_REGULAR_FILES"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_IMPORT_GAP:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_bytes(source: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(source),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stdout[-1000:] + proc.stderr[-1000:]
        raise RuntimeError(
            f"GOOSE_GIT_COMMAND_GAP:{args[0]}:{proc.returncode}:"
            f"{detail.decode('utf-8', errors='replace')}"
        )
    return proc.stdout


def normalize_tracked_source(source: Path, destination: Path) -> dict[str, Any]:
    """Build a regular-file-only view of the exact tracked Goose commit.

    The canonical YAIWES download/copy motors intentionally reject symlinks.
    Goose's official Hermit toolchain tracks symlinks under ``bin/``.  This
    adapter does not weaken either motor: it accepts only Git-tracked regular
    files and relative symlinks whose fully resolved target remains inside the
    checkout and is itself a tracked regular file.  Symlinks are materialized
    as regular files for the source-inspection mirror; the original link map is
    retained as evidence and runtime integration remains explicitly unclaimed.
    """
    source = source.resolve()
    if destination.exists():
        raise RuntimeError("GOOSE_NORMALIZED_DESTINATION_EXISTS")

    raw = _git_bytes(source, "ls-files", "-s", "-z")
    entries: list[tuple[str, str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            meta, path_raw = record.split(b"\t", 1)
            mode, blob_sha, stage = meta.decode("ascii").split()
            rel = path_raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RuntimeError("GOOSE_GIT_INDEX_PARSE_GAP") from exc
        if stage != "0":
            raise RuntimeError(f"GOOSE_GIT_INDEX_STAGE_GAP:{rel}:{stage}")
        q = PurePosixPath(rel)
        if q.is_absolute() or not q.parts or ".." in q.parts:
            raise RuntimeError(f"GOOSE_TRACKED_PATH_GAP:{rel}")
        if mode not in {"100644", "100755", "120000"}:
            raise RuntimeError(f"GOOSE_TRACKED_MODE_GAP:{rel}:{mode}")
        entries.append((rel, mode, blob_sha))

    if not entries:
        raise RuntimeError("GOOSE_TRACKED_TREE_EMPTY")

    tracked_modes = {rel: mode for rel, mode, _ in entries}
    git_tree_sha = _git_bytes(source, "rev-parse", "HEAD^{tree}").decode("ascii").strip()
    destination.mkdir(parents=True)
    materialized: list[dict[str, str]] = []

    for rel, mode, blob_sha in entries:
        q = PurePosixPath(rel)
        src = source.joinpath(*q.parts)
        out = destination.joinpath(*q.parts)
        out.parent.mkdir(parents=True, exist_ok=True)

        if mode in {"100644", "100755"}:
            try:
                src_mode = src.lstat().st_mode
            except FileNotFoundError as exc:
                raise RuntimeError(f"GOOSE_TRACKED_FILE_MISSING:{rel}") from exc
            if src.is_symlink() or not src.is_file():
                raise RuntimeError(f"GOOSE_TRACKED_REGULAR_TYPE_GAP:{rel}")
            shutil.copyfile(src, out)
            out.chmod(0o755 if mode == "100755" else 0o644)
            continue

        if not src.is_symlink():
            raise RuntimeError(f"GOOSE_TRACKED_SYMLINK_TYPE_GAP:{rel}")
        link_target = os.readlink(src)
        target_path = PurePosixPath(link_target)
        if target_path.is_absolute():
            raise RuntimeError(f"GOOSE_SYMLINK_ABSOLUTE_TARGET_GAP:{rel}:{link_target}")
        try:
            resolved = (src.parent / link_target).resolve(strict=True)
            resolved_rel = resolved.relative_to(source).as_posix()
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise RuntimeError(f"GOOSE_SYMLINK_RESOLUTION_GAP:{rel}:{link_target}") from exc
        resolved_mode = tracked_modes.get(resolved_rel)
        if resolved_mode not in {"100644", "100755"}:
            raise RuntimeError(
                f"GOOSE_SYMLINK_TARGET_NOT_TRACKED_REGULAR:{rel}:{resolved_rel}:"
                f"{resolved_mode}"
            )
        if resolved.is_symlink() or not resolved.is_file():
            raise RuntimeError(f"GOOSE_SYMLINK_FINAL_TYPE_GAP:{rel}:{resolved_rel}")
        shutil.copyfile(resolved, out)
        out.chmod(0o755 if resolved_mode == "100755" else 0o644)
        materialized.append(
            {
                "path": rel,
                "blob_sha": blob_sha,
                "link_target": link_target,
                "resolved_tracked_path": resolved_rel,
            }
        )

    link_payload = json.dumps(materialized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "strategy": NORMALIZATION_STRATEGY,
        "official_git_tree_sha": git_tree_sha,
        "tracked_entries": len(entries),
        "materialized_symlinks": len(materialized),
        "materialization_map_sha256": hashlib.sha256(link_payload.encode("utf-8")).hexdigest(),
        "materialization_map": materialized,
        "runtime_semantics_claimed": False,
    }


def update_aggregate(aggregate_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    if aggregate.get("verified_total") != 17 or aggregate.get("unresolved_total") != 1:
        raise RuntimeError("AGGREGATE_PRECONDITION_NOT_17_OF_18")
    rows = aggregate.get("results", [])
    goose_rows = [i for i, row in enumerate(rows) if row.get("agent_id") == "goose"]
    if len(goose_rows) != 1:
        raise RuntimeError("GOOSE_AGGREGATE_ROW_GAP")
    idx = goose_rows[0]
    if rows[idx].get("status") != "UNRESOLVED_SOURCE":
        raise RuntimeError("GOOSE_AGGREGATE_NOT_UNRESOLVED")
    rows[idx] = result
    aggregate["resolved_total"] = 18
    aggregate["verified_total"] = 18
    aggregate["unresolved_total"] = 0
    aggregate["failures"] = 0
    aggregate["verdict"] = "VERIFIED_18_OF_18"
    aggregate["goose_official_source"] = {
        "repo": SOURCE_REPO,
        "commit": SOURCE_COMMIT,
        "acquisition": "LOCKED_DOWNLOAD_EXTRACT_ENGINE_THEN_CANONICAL_COPY_MOTOR",
        "source_normalization": NORMALIZATION_STRATEGY,
    }
    aggregate_path.write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return aggregate


def update_registry(registry_path: Path, aggregate: dict[str, Any]) -> None:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    by_id = {row["agent_id"]: row for row in aggregate["results"]}
    if set(by_id) != {row["agent_id"] for row in registry.get("agents", [])}:
        raise RuntimeError("REGISTRY_AGGREGATE_AGENT_SET_MISMATCH")
    for agent in registry["agents"]:
        evidence = by_id[agent["agent_id"]]
        if evidence.get("status") != "COPIED_AND_READBACK_VERIFIED":
            raise RuntimeError(f"LOCAL_MIRROR_NOT_VERIFIED:{agent['agent_id']}")
        agent["local_source_path"] = evidence["destination"]
        agent["local_source_manifest_sha256"] = evidence["manifest_sha256"]
        agent["local_source_copy_status"] = "COPIED_AND_READBACK_VERIFIED"
        agent["local_source_runtime_claim"] = False
        if agent["agent_id"] == "goose":
            agent["official_source_repo"] = SOURCE_REPO
            agent["official_source_commit"] = SOURCE_COMMIT
            agent["source_status"] = "OFFICIAL_SOURCE_MIRRORED_VERIFIED_RUNTIME_UNCHANGED"
            agent["source_normalization"] = NORMALIZATION_STRATEGY
    registry["source_traceability_status"] = (
        "18_OF_18_LOCAL_SOURCE_MIRRORS_VERIFIED_RUNTIME_STATUS_UNCHANGED"
    )
    registry["local_source_evidence"] = (
        "➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/AGENT_SOURCE_COPY_2026-09-15.json"
    )
    registry_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    authorized_root = (repo_root / "➡️📂 Wordflow LOOP Yaiwes").resolve()
    destination = authorized_root / "wordflow_loop" / "agent_sources" / "goose"
    evidence_dir = authorized_root / "wordflow_loop" / "evidence"
    state_file = evidence_dir / "agent-source-copy-state" / "goose.json"
    aggregate_path = evidence_dir / "AGENT_SOURCE_COPY_2026-09-15.json"
    registry_path = (
        authorized_root
        / "wordflow_loop"
        / "wordflow_loop"
        / "agent_fleet"
        / "agent_fleet_registry.json"
    )
    evidence_path = evidence_dir / "GOOSE_OFFICIAL_ACQUISITION_2026-09-15.json"
    engine_path = (
        repo_root
        / "➡️📂motores de descarga extracción copiado movimiento archivos agentes"
        / "📂Motor descarga de componentes y extracción de zip"
        / "hf_download_extract_engine.py"
    )

    if gate.git_blob_sha(engine_path) != DOWNLOAD_ENGINE_EXPECTED_BLOB:
        raise RuntimeError("DOWNLOAD_EXTRACT_MOTOR_CODE_LOCK_GAP")
    copy_lock = gate.verify_motor(repo_root, "copy")
    if copy_lock["actual_blob_sha"] != COPY_MOTOR_EXPECTED_BLOB:
        raise RuntimeError("COPY_MOTOR_CODE_LOCK_GAP")
    copy_motor = repo_root / str(copy_lock["motor_path"])

    if destination.exists():
        raise RuntimeError("GOOSE_DESTINATION_ALREADY_EXISTS")

    old_env = {key: os.environ.get(key) for key in ("SOURCE_REPO", "SOURCE_REF", "SLUG", "PUBLISH")}
    os.environ["SOURCE_REPO"] = SOURCE_REPO
    os.environ["SOURCE_REF"] = SOURCE_COMMIT
    os.environ["SLUG"] = "goose"
    os.environ["PUBLISH"] = "0"
    try:
        engine = load_module(engine_path, "yaiwes_locked_download_extract_engine")
        with tempfile.TemporaryDirectory(prefix="yaiwes-goose-official-") as td:
            work = Path(td)
            source, resolved_commit = engine.acquire(work)
            if resolved_commit != SOURCE_COMMIT:
                raise RuntimeError(
                    f"SOURCE_COMMIT_MISMATCH:{resolved_commit}:{SOURCE_COMMIT}"
                )

            normalized = work / "source-normalized"
            normalization = normalize_tracked_source(source, normalized)
            rows, source_bytes = engine.scan_tree(normalized)
            source_tree = engine.tree_hash(normalized)
            bundle = work / "goose.bundle.zip"
            engine.make_zip(rows, bundle)
            bundle_sha256 = engine.sha256(bundle)
            parts_dir = work / "parts"
            parts = engine.split_bundle(bundle, parts_dir, "goose")
            rebuilt = engine.rebuild(parts_dir, parts, bundle_sha256)
            extracted = work / "extracted"
            engine.safe_extract(rebuilt, extracted)
            extracted_tree = engine.tree_hash(extracted)
            if extracted_tree != source_tree:
                raise RuntimeError("SOURCE_EXTRACTED_TREE_MISMATCH")

            source_manifest, source_manifest_sha = manifest_dir(
                extracted, max_file_bytes=95 * 1024 * 1024
            )
            state_file.parent.mkdir(parents=True, exist_ok=True)
            motor_env = gate.build_motor_env(
                extracted,
                destination,
                state_file,
                authorized_root=authorized_root,
                mutation_authorized=True,
            )
            motor_env["BATCH_SIZE"] = "100"
            motor_env["COLLISION_POLICY"] = "fail"
            proc = subprocess.run(
                [sys.executable, str(copy_motor)],
                cwd=str(repo_root),
                env={**os.environ, **motor_env},
                capture_output=True,
                text=True,
                check=False,
            )
            motor_result = parse_motor_stdout(proc.stdout)
            if proc.returncode != 0 or motor_result.get("verdict") != "VERIFIED_CLOSED":
                raise RuntimeError(
                    f"COPY_MOTOR_NOT_VERIFIED:rc={proc.returncode}:"
                    f"verdict={motor_result.get('verdict')}"
                )
            dest_manifest, dest_manifest_sha = manifest_dir(
                destination, max_file_bytes=95 * 1024 * 1024
            )
            if source_manifest != dest_manifest or source_manifest_sha != dest_manifest_sha:
                raise RuntimeError("GOOSE_SOURCE_DESTINATION_MANIFEST_MISMATCH")

            result = {
                "agent_id": "goose",
                "checkout": "official_download_extract",
                "source_repo": SOURCE_REPO,
                "source_commit": resolved_commit,
                "source_kind": "dir",
                "source_path": ".",
                "destination": str(destination.relative_to(repo_root)),
                "status": "COPIED_AND_READBACK_VERIFIED",
                "file_count": len(dest_manifest),
                "bytes_total": sum(row["bytes"] for row in dest_manifest),
                "manifest_sha256": dest_manifest_sha,
                "source_tree_sha256": source_tree["sha256"],
                "official_git_tree_sha": normalization["official_git_tree_sha"],
                "source_normalization": normalization["strategy"],
                "materialized_symlinks": normalization["materialized_symlinks"],
                "materialization_map_sha256": normalization["materialization_map_sha256"],
                "download_extract_engine_blob_sha": DOWNLOAD_ENGINE_EXPECTED_BLOB,
                "download_extract_verified": True,
                "bundle_sha256": bundle_sha256,
                "bundle_parts": len(parts),
                "reconstruction_verified": True,
                "extraction_verified": True,
                "motor_blob_sha": copy_lock["actual_blob_sha"],
                "motor_verdict": motor_result["verdict"],
                "state_file": str(state_file.relative_to(repo_root)),
                "runtime_integration_claimed": False,
            }
            aggregate = update_aggregate(aggregate_path, result)
            update_registry(registry_path, aggregate)

            evidence = {
                "schema": SCHEMA,
                "verdict": "VERIFIED_CLOSED",
                "official_source": {
                    "repo": SOURCE_REPO,
                    "pinned_commit": SOURCE_COMMIT,
                    "resolved_commit": resolved_commit,
                    "git_tree_sha": normalization["official_git_tree_sha"],
                },
                "source_normalization": normalization,
                "download_extract_motor": {
                    "path": str(engine_path.relative_to(repo_root)),
                    "blob_sha": DOWNLOAD_ENGINE_EXPECTED_BLOB,
                    "verified": True,
                },
                "download_extract": {
                    "source_files": len(rows),
                    "source_bytes": source_bytes,
                    "source_tree": source_tree,
                    "bundle_sha256": bundle_sha256,
                    "parts": len(parts),
                    "reconstruction_verified": True,
                    "extraction_verified": True,
                    "extracted_tree": extracted_tree,
                },
                "canonical_copy_motor": {
                    "path": copy_lock["motor_path"],
                    "blob_sha": copy_lock["actual_blob_sha"],
                    "verdict": motor_result["verdict"],
                },
                "destination": result["destination"],
                "destination_manifest_sha256": dest_manifest_sha,
                "destination_files": len(dest_manifest),
                "destination_bytes": result["bytes_total"],
                "aggregate_verdict": aggregate["verdict"],
                "runtime_integration_claimed": False,
            }
            evidence_path.write_text(
                json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({
                "schema": SCHEMA,
                "verdict": "VERIFIED_CLOSED",
                "source_commit": resolved_commit,
                "official_git_tree_sha": normalization["official_git_tree_sha"],
                "materialized_symlinks": normalization["materialized_symlinks"],
                "destination_manifest_sha256": dest_manifest_sha,
                "destination_files": len(dest_manifest),
                "aggregate_verdict": aggregate["verdict"],
                "evidence": str(evidence_path.relative_to(repo_root)),
            }, ensure_ascii=False, sort_keys=True))
            return 0
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
