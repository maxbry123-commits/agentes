#!/usr/bin/env python3
"""TEAM SEALS · Deterministic Agent Acquisition v2.1

DOWNLOAD → CONSERVE → PIN → VERIFY → REPRODUCE

CAPA 1 SOURCE       → agents/<id>/source/complete-source/
CAPA 2 DISTRIBUTION → agents/<id>/distribution/official/
  - files <= GIT_MAX_BYTES stay in git
  - files >  GIT_MAX_BYTES written to distribution/staging/
    (workflow uploads staging to GitHub Release on agentes)

Every asset always gets: URL + size + platform + arch + SHA256 in assets.json
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
GIT_MAX_BYTES = 90 * 1024 * 1024  # stay under GitHub 100MB hard limit

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


def http_headers() -> dict[str, str]:
    h = {"User-Agent": "TEAM-SEALS-acquire/2.1", "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def http_get(url: str, dest: Path | None = None) -> bytes | str:
    req = urllib.request.Request(url, headers=http_headers())
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return sha256_file(dest)
    return data


def http_json(url: str) -> Any:
    try:
        raw = http_get(url)
        return json.loads(raw.decode() if isinstance(raw, bytes) else raw)
    except Exception as e:
        return {"_error": str(e)}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def parse_github(repo: str) -> tuple[str, str]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", repo.rstrip("/"))
    if not m:
        raise ValueError(f"not a github repo url: {repo}")
    return m.group(1), m.group(2)


def acquire_source(agent_dir: Path, repo: str, ref: str, commit: str | None) -> dict[str, Any]:
    src_root = agent_dir / "source"
    complete = src_root / "complete-source"
    if complete.exists():
        shutil.rmtree(complete)
    complete.mkdir(parents=True)
    url = (
        f"{repo.rstrip('/')}/archive/{commit}.tar.gz"
        if commit
        else f"{repo.rstrip('/')}/archive/refs/tags/{ref}.tar.gz"
    )
    print(f"[SOURCE] {url}")
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
    print(f"[SOURCE] tree={tree_sha}")
    return {
        "available": True,
        "repo": repo,
        "ref": ref,
        "commit": commit or "UNKNOWN",
        "url": url,
        "archive_sha256": archive_sha,
        "tree_sha256": tree_sha,
        "path": "source/complete-source",
    }


def detect_github_release_assets(owner: str, name: str, ref: str) -> list[dict[str, Any]]:
    data = http_json(f"https://api.github.com/repos/{owner}/{name}/releases/tags/{ref}")
    if not isinstance(data, dict) or data.get("_error") or data.get("message"):
        print(f"[SEARCH] release lookup failed: {data}")
        return []
    out = []
    for a in data.get("assets") or []:
        out.append({
            "source": "github_release",
            "name": a["name"],
            "url": a["browser_download_url"],
            "size": a.get("size"),
            "content_type": a.get("content_type"),
            "platform": _guess_platform(a["name"]),
            "architecture": _guess_arch(a["name"]),
        })
    return out


def detect_npm_package(source_dir: Path, ref: str) -> list[dict[str, Any]]:
    # root + common subdirs
    candidates = [source_dir / "package.json", source_dir / "codex-cli" / "package.json"]
    for pkg_path in candidates:
        if not pkg_path.is_file():
            continue
        try:
            pkg = json.loads(pkg_path.read_text())
        except Exception:
            continue
        name = pkg.get("name")
        if not name or str(name).startswith("."):
            continue
        version = pkg.get("version") or ref.lstrip("v").replace("rust-", "")
        short = Path(str(name)).name
        if str(name).startswith("@"):
            url = f"https://registry.npmjs.org/{name}/-/{short}-{version}.tgz"
        else:
            url = f"https://registry.npmjs.org/{name}/-/{short}-{version}.tgz"
        return [{
            "source": "npm_registry",
            "name": f"{short}-{version}.tgz",
            "url": url,
            "package": name,
            "version": version,
            "platform": "any",
            "architecture": "any",
        }]
    return []


def detect_pypi_package(source_dir: Path, ref: str) -> list[dict[str, Any]]:
    pyproject = source_dir / "pyproject.toml"
    if not pyproject.is_file():
        return []
    text = pyproject.read_text(errors="ignore")
    m = re.search(r'(?m)^name\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        return []
    name = m.group(1)
    version = ref.lstrip("v").replace("rust-", "")
    data = http_json(f"https://pypi.org/pypi/{name}/{version}/json")
    files = []
    if isinstance(data, dict) and not data.get("_error"):
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
    found = []
    for df in source_dir.rglob("Dockerfile*"):
        if not df.is_file() or ".git" in df.parts:
            continue
        text = df.read_text(errors="ignore")[:4000]
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
                "download": False,
            })
    return found


def _guess_platform(name: str) -> str:
    n = name.lower()
    if "windows" in n or n.endswith(".exe") or "win" in n:
        return "windows"
    if "darwin" in n or "macos" in n or "osx" in n or n.endswith(".dmg"):
        return "macos"
    if "linux" in n or n.endswith(".appimage") or ".deb" in n or ".rpm" in n:
        return "linux"
    return "unknown"


def _guess_arch(name: str) -> str:
    n = name.lower()
    if "arm64" in n or "aarch64" in n:
        return "arm64"
    if "x86_64" in n or "amd64" in n or "x64" in n:
        return "amd64"
    if "i686" in n or re.search(r"(?<![a-z])x86(?![_64])", n):
        return "x86"
    return "unknown"


def download_distribution_assets(assets: list[dict[str, Any]], dest: Path, staging: Path) -> list[dict[str, Any]]:
    """Download every downloadable asset. Store in git dest if <= GIT_MAX_BYTES else staging."""
    dest.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    results = []
    sums = []
    for a in assets:
        if a.get("download") is False:
            results.append({**a, "status": "REF_ONLY_NOT_PULLED"})
            continue
        url = a.get("url")
        if not url or str(url).startswith("docker://"):
            results.append({**a, "status": "REF_ONLY_NOT_PULLED"})
            continue
        tmp = staging / f".tmp-{a['name']}"
        print(f"[DIST] download {url}")
        try:
            digest = http_get(url, tmp)
            size = tmp.stat().st_size
            if size <= GIT_MAX_BYTES:
                final = dest / a["name"]
                shutil.move(str(tmp), str(final))
                storage = "git"
                local_path = f"distribution/official/{a['name']}"
                status = "DOWNLOADED_GIT"
            else:
                final = staging / a["name"]
                shutil.move(str(tmp), str(final))
                storage = "release_staging"
                local_path = f"distribution/staging/{a['name']}"
                status = "DOWNLOADED_STAGING"
                # pin sidecar always in git
                pin = dest / f"{a['name']}.PIN.json"
                pin.write_text(json.dumps({
                    "name": a["name"],
                    "url": url,
                    "sha256": digest,
                    "size": size,
                    "platform": a.get("platform"),
                    "architecture": a.get("architecture"),
                    "storage": "github_release_on_agentes",
                }, indent=2) + "\n")
            rec = {
                **a,
                "status": status,
                "storage": storage,
                "sha256": digest,
                "size": size,
                "local_path": local_path,
            }
            results.append(rec)
            sums.append(f"{digest}  {a['name']}")
            print(f"[DIST] {status} sha256={digest} size={size} {a['name']}")
        except Exception as e:
            results.append({**a, "status": "FAILED", "error": str(e)})
            print(f"[DIST] FAILED {a['name']}: {e}")
            if tmp.exists():
                tmp.unlink()
    if sums:
        (dest / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    (dest / "assets.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


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
    (dest / "toolchain.notes").write_text("# Fill from CI: compiler, runtime, PM, base digest\n")
    return info


def write_manifest(agent_dir: Path, meta: dict[str, Any]) -> Path:
    path = agent_dir / "manifest.json"
    dist = meta.get("distribution", [])
    git_n = sum(1 for x in dist if x.get("status") == "DOWNLOADED_GIT")
    stg_n = sum(1 for x in dist if x.get("status") == "DOWNLOADED_STAGING")
    fail_n = sum(1 for x in dist if x.get("status") == "FAILED")
    layer_dist = "CAPTURED" if (git_n + stg_n) > 0 else (
        "NOT_PUBLISHED_AFTER_SEARCH" if meta.get("search_done") else "SEARCH_INCOMPLETE"
    )
    if fail_n and (git_n + stg_n) == 0:
        layer_dist = "FAILED"
    doc = {
        "protocol": "TEAM-SEALS-ACQUIRE-v2.1",
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
            "official": dist,
            "rebuilt": [],
            "search_performed": meta.get("search_log", []),
            "counts": {"git": git_n, "staging": stg_n, "failed": fail_n},
            "release_tag": meta.get("release_tag"),
        },
        "dependencies_lockfiles": meta.get("deps", []),
        "build": meta.get("build", {}),
        "reproducibility": {
            "official_sha256_list": [x.get("sha256") for x in dist if x.get("sha256")],
            "rebuilt_sha256_list": [],
            "bit_for_bit": False,
            "status": "PENDING",
        },
        "layers": {
            "source": "CAPTURED" if meta["source"].get("available") else "NOT_FOUND_AFTER_SEARCH",
            "distribution": layer_dist,
        },
    }
    path.write_text(json.dumps(doc, indent=2) + "\n")
    mdir = agent_dir / "manifests"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "manifest.json").write_text(path.read_text())
    return path


def acquire(args: argparse.Namespace) -> int:
    agent_id = args.id
    agent_dir = AGENTS / agent_id
    if agent_dir.exists():
        shutil.rmtree(agent_dir)
    agent_dir.mkdir(parents=True)
    owner, name = parse_github(args.repo)
    release_tag = f"agent-{agent_id}-{args.ref}".replace("/", "-")

    print(f"=== ACQUIRE {agent_id} ===")
    print(f"repo={args.repo} ref={args.ref} commit={args.commit or 'N/A'}")

    source_meta = acquire_source(agent_dir, args.repo, args.ref, args.commit)
    source_dir = agent_dir / "source" / "complete-source"

    search_log = []
    candidates: list[dict[str, Any]] = []

    gh = detect_github_release_assets(owner, name, args.ref)
    search_log.append({"where": "github_releases", "count": len(gh)})
    candidates.extend(gh)

    npm = detect_npm_package(source_dir, args.ref)
    search_log.append({"where": "npm_registry", "count": len(npm)})
    candidates.extend(npm)

    pypi = detect_pypi_package(source_dir, args.ref)
    search_log.append({"where": "pypi", "count": len(pypi)})
    candidates.extend(pypi)

    docker = detect_docker_from_source(source_dir, owner, name, args.ref)
    search_log.append({"where": "docker_refs", "count": len(docker)})
    candidates.extend(docker)

    print(f"[SEARCH] {search_log}")

    dist_dir = agent_dir / "distribution" / "official"
    staging = agent_dir / "distribution" / "staging"
    dist_results = download_distribution_assets(candidates, dist_dir, staging)

    (agent_dir / "distribution" / "rebuilt").mkdir(parents=True, exist_ok=True)
    (agent_dir / "distribution" / "rebuilt" / "STATUS.txt").write_text("PENDING_REBUILD\n")

    deps = collect_deps(source_dir, agent_dir / "dependencies")
    build_info = collect_build(source_dir, agent_dir / "build")

    for d in ("models", "runtime", "tools", "plugins", "provenance"):
        p = agent_dir / d
        p.mkdir(parents=True, exist_ok=True)
        (p / "STATUS.txt").write_text("EMPTY_AFTER_SEARCH\n")

    hashes = agent_dir / "hashes"
    hashes.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{source_meta['tree_sha256']}  source/complete-source/",
        f"{source_meta['archive_sha256']}  source/archive.tar.gz",
    ]
    for r in dist_results:
        if r.get("sha256"):
            lines.append(f"{r['sha256']}  {r.get('local_path', r['name'])}")
    (hashes / "SHA256SUMS").write_text("\n".join(lines) + "\n")

    meta = {
        "id": agent_id,
        "source": source_meta,
        "distribution": dist_results,
        "deps": deps,
        "build": build_info,
        "search_log": search_log,
        "search_done": True,
        "release_tag": release_tag,
    }
    write_manifest(agent_dir, meta)
    git_n = sum(1 for x in dist_results if x.get("status") == "DOWNLOADED_GIT")
    stg_n = sum(1 for x in dist_results if x.get("status") == "DOWNLOADED_STAGING")
    print(f"[SUMMARY] source=OK dist_git={git_n} dist_staging={stg_n} release_tag={release_tag}")
    print("=== DONE ===")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--commit", default=None)
    args = ap.parse_args()
    if args.ref.lower() in FLOATING:
        print("ERROR: floating ref forbidden", file=sys.stderr)
        return 2
    return acquire(args)


if __name__ == "__main__":
    sys.exit(main())
