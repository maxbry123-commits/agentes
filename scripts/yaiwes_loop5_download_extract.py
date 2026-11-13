# Adapted from skill-locked research_download_chain.py
# source blob: 1504bbc7ec780a351beb105df884180c9ae2c666
# Allowed surgical edits only: task id, sources, refs, selected paths, destination, manifest/checkpoint.
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

TASK_ID = "YAIWES-LOOP5-20260907"
DEST = Path("➡️📂 Wordflow LOOP Yaiwes/📂 archivos download/📂 LOOP open source 5").resolve()
WORK = Path("_work/yaiwes-loop5").resolve()
SRC = WORK / "src"
MANIFEST = DEST / "LOOP5_MANIFEST.jsonl"
CHECKPOINT = DEST / "LOOP5_CHECKPOINT.json"
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
MAX_BLOB = 100 * 1024 * 1024

COMPONENTS = [
    {
        "name": "LangGraph",
        "url": "https://github.com/langchain-ai/langgraph.git",
        "ref": "81bf17b23123e4ef8b9d5f49fa09a0122fc2edd1",
        "paths": ["libs/langgraph/langgraph", "libs/checkpoint/langgraph/checkpoint"],
    },
    {
        "name": "Temporal-Python-SDK",
        "url": "https://github.com/temporalio/sdk-python.git",
        "ref": "22a9e41fd857261ee0a9bb5ce57f439d93e7f88d",
        "paths": ["temporalio"],
    },
    {
        "name": "Prefect",
        "url": "https://github.com/PrefectHQ/prefect.git",
        "ref": "6a6fe4e24cc456be30dd570aeeb1dbb6b6bef286",
        "paths": ["src/prefect"],
    },
    {
        "name": "Hatchet-Python-SDK",
        "url": "https://github.com/hatchet-dev/hatchet.git",
        "ref": "086a63f2245416296de288a944aad1b8357e63e9",
        "paths": ["sdks/python/hatchet_sdk"],
    },
    {
        "name": "redun",
        "url": "https://github.com/insitro/redun.git",
        "ref": "49a299b223bc345b999aaa40daa6876f105089e1",
        "paths": ["redun"],
    },
]

def run(cmd, cwd=None, capture=False):
    if capture:
        return subprocess.check_output(cmd, cwd=cwd, text=True).strip()
    subprocess.run(cmd, cwd=cwd, check=True)

def retry_clone(component, root):
    for attempt in range(1, 4):
        shutil.rmtree(root, ignore_errors=True)
        try:
            run([
                "git", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.clean=cat",
                "-c", "filter.lfs.process=", "-c", "filter.lfs.required=false",
                "clone", "--filter=blob:none", "--no-checkout", "--no-tags",
                component["url"], str(root),
            ])
            run(["git", "sparse-checkout", "init", "--cone"], cwd=root)
            sparse = list(component["paths"])
            sparse.extend(["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "NOTICE"])
            subprocess.run(["git", "sparse-checkout", "set", *sparse], cwd=root, check=False)
            run(["git", "checkout", "--detach", component["ref"]], cwd=root)
            actual = run(["git", "rev-parse", "HEAD"], cwd=root, capture=True)
            if actual != component["ref"]:
                raise RuntimeError(f"REF_MISMATCH {component['name']} {actual}")
            return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt * 5)

def source_files(root, selected_paths):
    files = []
    for selected in selected_paths:
        p = root / selected
        if not p.exists():
            raise RuntimeError(f"SOURCE_PATH_MISSING {selected}")
        if p.is_file():
            files.append(p)
        else:
            files.extend(x for x in p.rglob("*") if x.is_file())
    return sorted(set(files))

def tree_digest(root):
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file() and x.name != "SOURCE_SHA256SUMS.txt"):
        rel = p.relative_to(root).as_posix().encode()
        h.update(rel + b"\0")
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()

def guard_files(files):
    for p in files:
        size = p.stat().st_size
        if size >= MAX_BLOB:
            raise RuntimeError(f"GIT_BLOB_LIMIT_GAP {p} {size}")
        if size <= 1024:
            with p.open("rb") as f:
                if f.read(1024).startswith(LFS_PREFIX):
                    raise RuntimeError(f"SOURCE_LFS_POINTER_GAP {p}")

def license_path(root):
    candidates = []
    for p in root.iterdir():
        if p.is_file() and p.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")):
            candidates.append(p)
    return sorted(candidates)[0] if candidates else None

def write_provenance(out, component, license_file, source_tree_hash):
    (out / "SOURCE_URL.txt").write_text(component["url"].removesuffix(".git") + "\n")
    (out / "SOURCE_COMMIT.txt").write_text(component["ref"] + "\n")
    (out / "SOURCE_PATHS.txt").write_text("\n".join(component["paths"]) + "\n")
    (out / "SOURCE_LICENSE.txt").write_text((license_file.name if license_file else "LICENSE_NOT_FOUND_GAP") + "\n")
    (out / "SOURCE_TREE_SHA256.txt").write_text(source_tree_hash + "\n")
    if license_file:
        shutil.copy2(license_file, out / ("UPSTREAM_" + license_file.name))
    sums = []
    for p in sorted(x for x in out.rglob("*") if x.is_file() and x.name != "SOURCE_SHA256SUMS.txt"):
        sums.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}")
    (out / "SOURCE_SHA256SUMS.txt").write_text("\n".join(sums) + "\n")

def copy_component(component):
    root = SRC / component["name"]
    retry_clone(component, root)
    files = source_files(root, component["paths"])
    guard_files(files)
    if not files:
        raise RuntimeError(f"EMPTY_SELECTED_TREE {component['name']}")
    staging = WORK / "staging" / component["name"]
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    for selected in component["paths"]:
        src = root / selected
        dst = staging / selected
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    source_hash = tree_digest(staging)
    out = DEST / component["name"]
    if out.exists():
        existing = out / "SOURCE_TREE_SHA256.txt"
        if existing.exists() and existing.read_text().strip() == source_hash:
            return {"name": component["name"], "status": "VERIFIED_EXISTING", "tree_sha256": source_hash}
        raise RuntimeError(f"COLLISION_BLOCKED {out}")
    shutil.move(str(staging), str(out))
    write_provenance(out, component, license_path(root), source_hash)
    return {"name": component["name"], "status": "EXTRACTED_TREE", "tree_sha256": source_hash}

def main():
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    DEST.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    results = []
    for component in COMPONENTS:
        print(f"===== {TASK_ID}: {component['name']} =====", flush=True)
        result = copy_component(component)
        results.append(result)
        with MANIFEST.open("a") as f:
            f.write(json.dumps({**result, "task_id": TASK_ID, "source": component["url"], "source_commit": component["ref"], "selected_paths": component["paths"]}, sort_keys=True) + "\n")
    CHECKPOINT.write_text(json.dumps({"task_id": TASK_ID, "expected": 5, "processed": len(results), "results": results}, indent=2, sort_keys=True) + "\n")
    run(["git", "config", "user.name", "github-actions[bot]"])
    run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    run(["git", "add", "--", str(DEST.relative_to(Path.cwd()))])
    staged = run(["git", "diff", "--cached", "--name-only"], capture=True).splitlines()
    if not staged:
        print("NO_CHANGES VERIFIED_EXISTING")
        return
    for rel in staged:
        p = Path(rel)
        if p.is_file():
            if p.stat().st_size >= MAX_BLOB:
                raise RuntimeError(f"GIT_BLOB_LIMIT_GAP staged {rel}")
            if p.stat().st_size <= 1024 and p.read_bytes().startswith(LFS_PREFIX):
                raise RuntimeError(f"ZERO_LFS_POINTERS_FAIL {rel}")
    run(["git", "commit", "-m", "build(yaiwes): acquire 5 LOOP code roots via skill chain"])
    run(["git", "fetch", "origin", "main"])
    remote = run(["git", "rev-parse", "origin/main"], capture=True)
    parent = run(["git", "rev-parse", "HEAD^"], capture=True)
    if remote != parent:
        raise RuntimeError(f"CONCURRENT_WRITE_GAP remote={remote} parent={parent}")
    run(["git", "push", "--no-verify", "origin", "HEAD:main"])
    print("LOOP5_DOWNLOAD_EXTRACT=PASS 5/5")

if __name__ == "__main__":
    main()
