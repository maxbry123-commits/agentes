#!/usr/bin/env python3
"""TEAM SEALS · Deterministic Agent Acquisition v2

Primary goal: DOWNLOAD → CONSERVE → PIN → VERIFY → REPRODUCE

Captures TWO layers when the project publishes them:
  CAPA 1 SOURCE         → agents/<id>/source/complete-source/
  CAPA 2 DISTRIBUTION   → agents/<id>/distribution/official/

Determinism = immutable identity (URL + version/tag/commit + SHA256 + platform/arch).
Never pin to main/master/latest/HEAD.

Usage:
  python scripts/acquire_agent.py \\
    --id Hermes \\
    --repo https://github.com/NousResearch/hermes-agent \\
    --ref v2026.8.3 \\
    --commit 3c27eb6234bf91b8ceee9e9071591b31e9b148cb
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
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
    "Makefile", "justfile", "build.sh", "pyproject.toml", "setup.py",
    "Cargo.toml", "go.mod", "package.json", "flake.nix", "BUILD.bazel",
]

FLOATING = {"main", "master", "latest", "head"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path: Path) -> str:
    h = hashlib.sha256()
    files = sorted(p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts)
    for p in files:
        rel = str(p.relative_to(path)).replace("\\", "/")
        h.update(rel.encode()); h.update(b"\0")
        h.update(sha256_file(p).encode()); h.update(b"\0")
    return h.hexdigest()


def http_get(url: str, dest: Path | None = None) -> bytes | str:
    req = urllib.request.Request(url, headers={"User-Agent": "TEAM-SEALS-acquire/2.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return sha256_file(dest)
    return data


def http_json(url: str) -> Any:
    try:
        raw = http_get(url)
        return json.loads(raw.decode())
    except Exception as e:
        return {"_error": str(e)}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def parse_github(repo: str) -> tuple[str, str]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", repo.rstrip("/"))
    if not m:
        raise ValueError(f"not a github repo url: {repo}")
    return m.group(1), m.group(2)


# ── CAPA 1: SOURCE ────────────────────────────────────────────────────

def acquire_source(agent_dir: Path, repo: str, ref: str, commit: str | None) -> dict[str, Any]:
    """Download full source tree for immutable pin into source/complete-source/."""
    src_root = agent_dir / "source"
    complete = src_root / "complete-source"
    if complete.exists():
        shutil.rmtree(complete)
    complete.mkdir(parents=True)

    pin = commit or ref
    if commit:
        url = f"{repo.rstrip('/')}/archive/{commit}.tar.gz"
    else:
        url = f"{repo.rstrip('/')}/archive/refs/tags/{ref}.tar.gz"

    print(f"[SOURCE] downloading {url}")
    with tempfile.TemporaryDirectory() as td:
        tar = Path(td) / "src.tar.gz"
        archive_sha = http_get(url, tar)
        run(["tar", "-xzf", str(tar), "-C", str(complete), "--strip-components=1"])

    tree_sha = sha256_dir(complete)
    (src_root / "commit.txt").write_text((commit or "UNKNOWN") + "\n")
    (src_root / "release.txt").write_text(ref + "\n")
    (src_root / "repo.txt").write_text(repo + "\n")
    (src_root / "archive.url").write_text(url + "\n")
    (src_root / "archive.sha256").write_text(str(archive_sha) + "\n")
    (src_root / "tree.sha256").write_text(tree_sha + "\n")

    meta = {
        "available": True,
        "repo": repo,
        "ref": ref,
        "commit": commit or "UNKNOWN",
        "url": url,
        "archive_sha256": archive_sha,
        "tree_sha256": tree_sha,
        "path": "source/complete-source",
    }
    print(f"[SOURCE] tree_sha256={tree_sha}")
    return meta


# ── CAPA 2: DISTRIBUTION (search systematically) ────────────────────────

def detect_github_release_assets(owner: str, name: str, ref: str) -> list[dict[str, Any]]:
    data = http_json(f"https://api.github.com/repos/{owner}/{name}/releases/tags/{ref}")
    if isinstance(data, dict) and data.get("_error"):
        # try by name without v prefix variants
        return []
    assets = []
    for a in (data.get("assets") or []):
        assets.append({
            "source": "github_release",
            "name": a["name"],
            "url": a["browser_download_url"],
            "size": a.get("size"),
            "content_type": a.get("content_type"),
            "platform": _guess_platform(a["name"]),
            "architecture": _guess_arch(a["name"]),
        })
    return assets


def detect_npm_package(source_dir: Path, ref: str) -> list[dict[str, Any]]:
    """If package.json has a publishable name, record npm tarball URL for that version."""
    pkg_path = source_dir / "package.json"
    if not pkg_path.is_file():
        return []
    try:
        pkg = json.loads(pkg_path.read_text())
    except Exception:
        return []
    name = pkg.get("name")
    if not name or str(name).startswith("."):
        return []
    version = pkg.get("version") or ref.lstrip("v")
    # npm registry tarball
    safe = str(name).replace("@", "").replace("/", "-")
    url = f"https://registry.npmjs.org/{name}/-/{Path(str(name)).name}-{version}.tgz"
    # scoped packages: @scope/name -> registry.npmjs.org/@scope/name/-/name-version.tgz
    if str(name).startswith("@"):
        scope, short = str(name).split("/", 1)
        url = f"https://registry.npmjs.org/{name}/-/{short}-{version}.tgz"
    return [{
        "source": "npm_registry",
        "name": f"{Path(str(name)).name}-{version}.tgz",
        "url": url,
        "package": name,
        "version": version,
        "platform": "any",
        "architecture": "any",
    }]


def detect_pypi_package(source_dir: Path, ref: str) -> list[dict[str, Any]]:
    pyproject = source_dir / "pyproject.toml"
    setup = source_dir / "setup.py"
    name = None
    if pyproject.is_file():
        text = pyproject.read_text(errors="ignore")
        m = re.search(r'(?m)^name\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            name = m.group(1)
    if not name:
        return []
    version = ref.lstrip("v")
    # PyPI simple API JSON
    data = http_json(f"https://pypi.org/pypi/{name}/{version}/json")
    if isinstance(data, dict) and data.get("_error"):
        data = http_json(f"https://pypi.org/pypi/{name}/json")
        if isinstance(data, dict) and "releases" in data:
            files = data["releases"].get(version) or []
        else:
            return []
    else:
        files = data.get("urls") or []
    out = []
    for f in files:
        out.append({
            "source": "pypi",
            "name": f.get("filename") or Path(f.get("url", "pkg")).name,
            "url": f["url"],
            "package": name,
            "version": version,
            "packagetype": f.get("packagetype"),
            "platform": _guess_platform(f.get("filename", "")),
            "architecture": _guess_arch(f.get("filename", "")),
        })
    return out


def detect_docker_from_source(source_dir: Path, owner: str, name: str, ref: str) -> list[dict[str, Any]]:
    """Record official image references if Dockerfiles / known registries present.
    Does NOT pull multi-GB images by default; records the pin for later docker pull.
    """
    found = []
    for df in list(source_dir.glob("Dockerfile*")) + list(source_dir.glob("**/Dockerfile")):
        if df.is_file() and ".git" not in df.parts:
            text = df.read_text(errors="ignore")[:4000]
            # FROM lines as base images (for build env, not product)
            for m in re.finditer(r"(?m)^FROM\s+(\S+)", text):
                img = m.group(1)
                if img == "scratch" or img.startswith("$"):
                    continue
                found.append({
                    "source": "dockerfile_from",
                    "name": img.replace("/", "_").replace(":", "_"),
                    "image": img,
                    "url": f"docker://{img}",
                    "kind": "base_image_ref",
                    "platform": "container",
                    "architecture": "multi",
                    "download": False,  # ref only unless --pull-images
                })
    # Common GHCR / docker hub product image guesses
    for image in (
        f"ghcr.io/{owner}/{name}:{ref}",
        f"ghcr.io/{owner}/{name}:{ref.lstrip('v')}",
        f"{owner}/{name}:{ref}",
        f"{owner}/{name}:{ref.lstrip('v')}",
    ):
        found.append({
            "source": "registry_candidate",
            "name": image.replace("/", "_").replace(":", "_"),
            "image": image,
            "url": f"docker://{image}",
            "kind": "product_image_candidate",
            "platform": "container",
            "architecture": "multi",
            "download": False,
            "note": "candidate — verify exists before pull",
        })
    return found


def _guess_platform(name: str) -> str:
    n = name.lower()
    if "windows" in n or n.endswith(".exe") or "win" in n:
        return "windows"
    if "darwin" in n or "macos" in n or "osx" in n:
        return "macos"
    if "linux" in n or n.endswith(".appimage") or ".deb" in n or ".rpm" in n:
        return "linux"
    if n.endswith(".dmg"):
        return "macos"
    return "unknown"


def _guess_arch(name: str) -> str:
    n = name.lower()
    if "arm64" in n or "aarch64" in n:
        return "arm64"
    if "x86_64" in n or "amd64" in n or "x64" in n:
        return "amd64"
    if "i686" in n or "x86" in n:
        return "x86"
    return "unknown"


def download_distribution_assets(assets: list[dict[str, Any]], dest: Path) -> list[dict[str, Any]]:
    """Download all downloadable distribution assets; skip pure refs (docker candidates)."""
    dest.mkdir(parents=True, exist_ok=True)
    results = []
    sums = []
    for a in assets:
        if a.get("download") is False:
            # keep metadata only
            results.append({**a, "status": "REF_ONLY_NOT_PULLED"})
            continue
        url = a.get("url")
        if not url or url.startswith("docker://"):
            results.append({**a, "status": "REF_ONLY_NOT_PULLED"})
            continue
        out = dest / a["name"]
        print(f"[DIST] downloading {url}")
        try:
            digest = http_get(url, out)
            rec = {
                **a,
                "status": "DOWNLOADED",
                "sha256": digest,
                "path": str(out.relative_to(dest.parent.parent)) if False else f"distribution/official/{a['name']}",
                "local_path": f"distribution/official/{a['name']}",
            }
            results.append(rec)
            sums.append(f"{digest}  {a['name']}")
            print(f"[DIST] sha256={digest}  {a['name']}")
        except Exception as e:
            results.append({**a, "status": "FAILED", "error": str(e)})
            print(f"[DIST] FAILED {a['name']}: {e}")
    if sums:
        (dest / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    (dest / "assets.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


# ── DEPS / BUILD / RUNTIME ──────────────────────────────────────────────

def collect_deps(source_dir: Path, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    found = []
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
    for df in source_dir.rglob("Dockerfile*"):
        if df.is_file() and ".git" not in df.parts:
            rel = df.relative_to(source_dir)
            t = dest / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(df, t)
            info["dockerfiles"].append(str(rel))
    wf = source_dir / ".github" / "workflows"
    if wf.is_dir():
        for f in wf.rglob("*"):
            if f.is_file():
                rel = f.relative_to(source_dir)
                t = dest / rel
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, t)
                info["workflows"].append(str(rel))
    (dest / "toolchain.notes").write_text(
        "# Fill from CI: compiler, runtime, package manager, base image digest\n"
    )
    return info


def write_manifest(agent_dir: Path, meta: dict[str, Any]) -> Path:
    path = agent_dir / "manifest.json"
    doc = {
        "protocol": "TEAM-SEALS-ACQUIRE-v2",
        "goal": "DOWNLOAD_CONSERVE_PIN_VERIFY_REPRODUCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": meta["id"],
        "identity": {
            "repository": meta["source"]["repo"],
            "ref": meta["source"]["ref"],
            "commit": meta["source"]["commit"],
        },
        "source": meta["source"],
        "distribution": {
            "official": meta.get("distribution", []),
            "rebuilt": meta.get("rebuilt", []),
            "search_performed": meta.get("search_log", []),
        },
        "dependencies_lockfiles": meta.get("deps", []),
        "build": meta.get("build", {}),
        "reproducibility": {
            "official_sha256_list": [
                x.get("sha256") for x in meta.get("distribution", [])
                if x.get("status") == "DOWNLOADED"
            ],
            "rebuilt_sha256_list": [],
            "bit_for_bit": False,
            "status": meta.get("repro_status", "PENDING_OR_NO_OFFICIAL_DIST"),
        },
        "layers": {
            "source": "CAPTURED" if meta["source"].get("available") else "NOT_FOUND_AFTER_SEARCH",
            "distribution": (
                "CAPTURED" if any(x.get("status") == "DOWNLOADED" for x in meta.get("distribution", []))
                else (
                    "NOT_PUBLISHED_AFTER_SEARCH"
                    if meta.get("search_done")
                    else "SEARCH_INCOMPLETE"
                )
            ),
        },
    }
    path.write_text(json.dumps(doc, indent=2) + "\n")
    # also keep under manifests/ for compatibility
    mdir = agent_dir / "manifests"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "manifest.json").write_text(path.read_text())
    return path


def acquire(args: argparse.Namespace) -> int:
    agent_id = args.id
    agent_dir = AGENTS / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    owner, name = parse_github(args.repo)

    print(f"=== ACQUIRE {agent_id} ===")
    print(f"repo={args.repo} ref={args.ref} commit={args.commit or 'N/A'}")

    # 1 SOURCE
    source_meta = acquire_source(agent_dir, args.repo, args.ref, args.commit)
    source_dir = agent_dir / "source" / "complete-source"

    # 2 DISTRIBUTION discovery (systematic)
    search_log = []
    candidates: list[dict[str, Any]] = []

    gh_assets = detect_github_release_assets(owner, name, args.ref)
    search_log.append({"where": "github_releases", "count": len(gh_assets)})
    candidates.extend(gh_assets)

    npm_assets = detect_npm_package(source_dir, args.ref)
    search_log.append({"where": "npm_registry", "count": len(npm_assets)})
    candidates.extend(npm_assets)

    pypi_assets = detect_pypi_package(source_dir, args.ref)
    search_log.append({"where": "pypi", "count": len(pypi_assets)})
    candidates.extend(pypi_assets)

    docker_refs = detect_docker_from_source(source_dir, owner, name, args.ref)
    search_log.append({"where": "docker_refs", "count": len(docker_refs)})
    candidates.extend(docker_refs)

    print(f"[SEARCH] candidates={len(candidates)} log={search_log}")

    dist_dir = agent_dir / "distribution" / "official"
    dist_results = download_distribution_assets(candidates, dist_dir)

    # rebuilt placeholder
    (agent_dir / "distribution" / "rebuilt").mkdir(parents=True, exist_ok=True)
    (agent_dir / "distribution" / "rebuilt" / "STATUS.txt").write_text(
        "PENDING_REBUILD\nRequires fixed toolchain from build/ and CI.\n"
    )

    # 3 DEPS + BUILD
    deps = collect_deps(source_dir, agent_dir / "dependencies")
    build_info = collect_build(source_dir, agent_dir / "build")

    # 4 placeholders for optional layers
    for d in ("models", "runtime", "tools", "plugins", "provenance"):
        p = agent_dir / d
        p.mkdir(parents=True, exist_ok=True)
        if not any(p.iterdir()):
            (p / "STATUS.txt").write_text(
                "EMPTY_AFTER_SEARCH\nFill only if official distribution requires it.\n"
            )

    # 5 HASHES rollup
    hashes = agent_dir / "hashes"
    hashes.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{source_meta['tree_sha256']}  source/complete-source/",
        f"{source_meta['archive_sha256']}  source/archive.tar.gz",
    ]
    for r in dist_results:
        if r.get("sha256"):
            lines.append(f"{r['sha256']}  distribution/official/{r['name']}")
    (hashes / "SHA256SUMS").write_text("\n".join(lines) + "\n")

    meta = {
        "id": agent_id,
        "source": source_meta,
        "distribution": dist_results,
        "deps": deps,
        "build": build_info,
        "search_log": search_log,
        "search_done": True,
        "repro_status": "PENDING",
        "rebuilt": [],
    }
    manifest = write_manifest(agent_dir, meta)
    print(f"[MANIFEST] {manifest}")
    downloaded = sum(1 for x in dist_results if x.get("status") == "DOWNLOADED")
    print(f"[SUMMARY] source=CAPTURED distribution_downloaded={downloaded}")
    print("=== DONE ===")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic agent acquisition v2")
    ap.add_argument("--id", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", required=True, help="Immutable tag/release")
    ap.add_argument("--commit", default=None, help="Full commit SHA preferred")
    args = ap.parse_args()
    if args.ref.lower() in FLOATING:
        print("ERROR: floating ref forbidden", file=sys.stderr)
        return 2
    return acquire(args)


if __name__ == "__main__":
    sys.exit(main())
