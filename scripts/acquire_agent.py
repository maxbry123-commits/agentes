#!/usr/bin/env python3
"""TEAM SEALS · Deterministic Agent Acquisition Pipeline
Protocol §1-15 · Generic · Verifiable · Reusable

Usage:
  python scripts/acquire_agent.py --id OpenCode \\
    --repo https://github.com/anomalyco/opencode \\
    --ref v1.18.15 \\
    --commit d7b115f

Pipeline:
  DISCOVER → PIN → DOWNLOAD → VERIFY → STORE → HASH
  → BINARY → DEPS → TOOLCHAIN → PROVENANCE → REBUILD?
  → COMPARE → SNAPSHOT
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"

LOCKFILES = [
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock",
    "Cargo.lock", "poetry.lock", "uv.lock", "requirements.txt",
    "go.sum", "go.mod", "Gemfile.lock", "composer.lock",
    "MODULE.bazel.lock", "flake.lock", "Pipfile.lock",
]

BUILD_MARKERS = [
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows", "Makefile", "justfile", "build.sh",
    "pyproject.toml", "setup.py", "Cargo.toml", "go.mod",
    "package.json", "flake.nix", "BUILD.bazel",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path: Path) -> str:
    """Deterministic tree hash: sorted relative paths + content hashes."""
    h = hashlib.sha256()
    files = sorted(
        p for p in path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )
    for p in files:
        rel = str(p.relative_to(path)).replace("\\", "/")
        h.update(rel.encode())
        h.update(b"\0")
        h.update(sha256_file(p).encode())
        h.update(b"\0")
    return h.hexdigest()


def download(url: str, dest: Path) -> str:
    print(f"  download: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    digest = sha256_file(dest)
    print(f"  sha256:   {digest}")
    return digest


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def pin_source(agent_dir: Path, repo: str, ref: str, commit: str | None) -> dict[str, Any]:
    """Download source archive for exact ref; extract to source/repository."""
    source_dir = agent_dir / "source" / "repository"
    if source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True)

    # Prefer commit archive if provided (immutable)
    if commit:
        url = f"{repo.rstrip('/')}/archive/{commit}.tar.gz"
        pin_label = commit
    else:
        url = f"{repo.rstrip('/')}/archive/refs/tags/{ref}.tar.gz"
        pin_label = ref

    with tempfile.TemporaryDirectory() as td:
        tar = Path(td) / "src.tar.gz"
        archive_sha = download(url, tar)
        run(["tar", "-xzf", str(tar), "-C", str(source_dir), "--strip-components=1"])

    tree_sha = sha256_dir(source_dir)
    (agent_dir / "source" / "commit.txt").write_text((commit or ref) + "\n")
    (agent_dir / "source" / "release.txt").write_text(ref + "\n")
    (agent_dir / "source" / "source.sha256").write_text(tree_sha + "\n")
    (agent_dir / "source" / "archive.sha256").write_text(archive_sha + "\n")
    (agent_dir / "source" / "repo.txt").write_text(repo + "\n")

    return {
        "repo": repo,
        "ref": ref,
        "commit": commit or "UNKNOWN",
        "archive_url": url,
        "archive_sha256": archive_sha,
        "tree_sha256": tree_sha,
        "status": "PINNED",
    }


def collect_deps(source_dir: Path, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    found: list[str] = []
    for name in LOCKFILES:
        for p in source_dir.rglob(name):
            if ".git" in p.parts:
                continue
            rel = p.relative_to(source_dir)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            found.append(str(rel))
    return found


def collect_build(source_dir: Path, dest: Path) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    info: dict[str, Any] = {"markers": [], "dockerfiles": [], "workflows": []}
    for name in BUILD_MARKERS:
        p = source_dir / name
        if p.is_file():
            shutil.copy2(p, dest / p.name)
            info["markers"].append(name)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(source_dir)
                    t = dest / rel
                    t.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, t)
                    info["workflows"].append(str(rel))
    for df in source_dir.rglob("Dockerfile*"):
        if df.is_file() and ".git" not in df.parts:
            rel = df.relative_to(source_dir)
            t = dest / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(df, t)
            info["dockerfiles"].append(str(rel))
    (dest / "toolchain.txt").write_text(
        "# Fill after inspection: OS, arch, compiler, runtime, package manager\n"
        "status: INSUFFICIENT_DATA\n"
    )
    (dest / "environment.txt").write_text(
        "# Fixed build environment notes\nstatus: INSUFFICIENT_DATA\n"
    )
    return info


def fetch_release_binaries(repo: str, ref: str, dest: Path) -> list[dict[str, Any]]:
    """Best-effort: list GitHub release assets and download them."""
    dest.mkdir(parents=True, exist_ok=True)
    api = repo.rstrip("/").replace("https://github.com/", "https://api.github.com/repos/")
    url = f"{api}/releases/tags/{ref}"
    assets_meta: list[dict[str, Any]] = []
    try:
        with urllib.request.urlopen(url) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        (dest / "STATUS.txt").write_text(f"NOT_PUBLISHED_OR_NO_RELEASE\n{e}\n")
        return assets_meta

    sums_lines: list[str] = []
    for asset in data.get("assets") or []:
        name = asset["name"]
        dl = asset["browser_download_url"]
        out = dest / name
        try:
            digest = download(dl, out)
        except Exception as e:
            assets_meta.append({"filename": name, "status": "FAILED", "error": str(e)})
            continue
        sums_lines.append(f"{digest}  {name}")
        assets_meta.append({
            "filename": name,
            "url": dl,
            "size": asset.get("size"),
            "sha256": digest,
            "status": "VERIFIED",
        })
    if sums_lines:
        (dest / "SHA256SUMS").write_text("\n".join(sums_lines) + "\n")
    else:
        (dest / "STATUS.txt").write_text("NO_ASSETS\n")
    return assets_meta


def write_snapshot(agent_dir: Path, meta: dict[str, Any]) -> Path:
    manifests = agent_dir / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    snap = {
        "protocol": "TEAM-SEALS-DETERMINISTIC-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": meta["id"],
        "identity": {
            "repository": meta["source"]["repo"],
            "ref": meta["source"]["ref"],
            "commit": meta["source"]["commit"],
        },
        "source": meta["source"],
        "binaries_official": meta.get("binaries", []),
        "dependencies_lockfiles": meta.get("deps", []),
        "build": meta.get("build", {}),
        "reproducibility": {
            "status": meta.get("repro_status", "INSUFFICIENT_DATA"),
            "official_sha256": None,
            "rebuilt_sha256": None,
            "bit_for_bit": False,
        },
        "provenance": {
            "status": meta.get("provenance_status", "NOT_VERIFIED"),
            "notes": "Classify VERIFIED / PARTIALLY_VERIFIED / NOT_VERIFIED after CI inspection",
        },
        "classification": {
            "source": "VERIFIED" if meta["source"].get("tree_sha256") else "NOT_PUBLISHED",
            "binary": meta.get("binary_class", "NOT_PUBLISHED"),
            "reproducible": meta.get("repro_status", "INSUFFICIENT_DATA"),
        },
    }
    path = manifests / "snapshot.json"
    path.write_text(json.dumps(snap, indent=2) + "\n")
    (manifests / "source.json").write_text(json.dumps(meta["source"], indent=2) + "\n")
    (manifests / "binary.json").write_text(json.dumps(meta.get("binaries", []), indent=2) + "\n")
    return path


def acquire(args: argparse.Namespace) -> int:
    agent_id = args.id
    agent_dir = AGENTS / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== ACQUIRE {agent_id} ===")
    print(f"repo={args.repo} ref={args.ref} commit={args.commit or 'N/A'}")

    # PIN + DOWNLOAD SOURCE
    source_meta = pin_source(agent_dir, args.repo, args.ref, args.commit)
    source_dir = agent_dir / "source" / "repository"

    # DEPS
    deps = collect_deps(source_dir, agent_dir / "dependencies")
    print(f"  lockfiles: {len(deps)}")

    # BUILD ENV markers
    build_info = collect_build(source_dir, agent_dir / "build")
    print(f"  build markers: {build_info.get('markers')}")

    # BINARIES (official release assets)
    binaries = fetch_release_binaries(args.repo, args.ref, agent_dir / "binaries" / "official")
    binary_class = "VERIFIED" if binaries else "NOT_PUBLISHED"
    print(f"  binaries: {len(binaries)} ({binary_class})")

    # HASHES rollup
    hashes_dir = agent_dir / "hashes"
    hashes_dir.mkdir(parents=True, exist_ok=True)
    (hashes_dir / "SHA256SUMS").write_text(
        f"{source_meta['tree_sha256']}  source/tree\n"
        f"{source_meta['archive_sha256']}  source/archive.tar.gz\n"
    )

    # Placeholders for models/plugins/tools/provenance/rebuilt
    for d in ("models", "plugins", "tools", "provenance", "binaries/rebuilt"):
        p = agent_dir / d
        p.mkdir(parents=True, exist_ok=True)
        (p / "STATUS.txt").write_text("NOT_PUBLISHED_OR_PENDING\n")

    meta = {
        "id": agent_id,
        "source": source_meta,
        "deps": deps,
        "build": build_info,
        "binaries": binaries,
        "binary_class": binary_class,
        "repro_status": "INSUFFICIENT_DATA",
        "provenance_status": "NOT_VERIFIED",
    }
    snap_path = write_snapshot(agent_dir, meta)
    print(f"  snapshot: {snap_path}")
    print("=== DONE ===")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic agent acquisition")
    ap.add_argument("--id", required=True, help="Agent folder name under agents/")
    ap.add_argument("--repo", required=True, help="GitHub repo URL")
    ap.add_argument("--ref", required=True, help="Immutable tag or release name")
    ap.add_argument("--commit", default=None, help="Full commit SHA (preferred)")
    args = ap.parse_args()

    # Reject floating refs
    if args.ref.lower() in {"main", "master", "latest", "head"}:
        print("ERROR: floating ref forbidden (main/master/latest/HEAD)", file=sys.stderr)
        return 2
    return acquire(args)


if __name__ == "__main__":
    sys.exit(main())
