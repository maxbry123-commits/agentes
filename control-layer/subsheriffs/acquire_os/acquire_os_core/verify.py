#!/usr/bin/env python3
"""ACQUIRE-OS v1 — verify.py — nodos 01-11: recepción del checkout,
integridad física (condicional según source_type), toolchain y
dependencias. Nada aquí asume Git, Node ni ningún lenguaje específico."""
import json
import shutil
from acquire_os_core.core import run, sha


def receive_checkout(ctx):
    if not ctx.src.exists():
        raise RuntimeError("CHECKOUT_PATH_MISSING")


def verify_pin_match(ctx):
    pin = ctx.recipe["pin"]
    st = ctx.recipe["source_type"]
    if st == "git_native":
        head = run(["git", "rev-parse", "HEAD"], ctx.src).stdout.strip()
        if head != pin["commit"]:
            raise RuntimeError("PIN_MISMATCH:" + head)
    elif st == "hf_hub":
        marker = ctx.src / ".hf_revision"
        if not marker.exists() or marker.read_text().strip() != pin["revision"]:
            raise RuntimeError("HF_REVISION_MISMATCH")
    elif st in ("release_binary", "package_manager"):
        pass  # el pin real se valida en 07_VERIFY_CHECKSUM
    else:
        raise RuntimeError("UNKNOWN_SOURCE_TYPE:" + str(st))


def verify_repository_shape(ctx):
    if (ctx.src / ".git" / "shallow").exists():
        raise RuntimeError("SHALLOW_CHECKOUT")
    if run(["git", "config", "--get", "core.sparseCheckout"], ctx.src, False).stdout.strip() == "true":
        raise RuntimeError("SPARSE_CHECKOUT")
    if run(["git", "config", "--get", "remote.origin.promisor"], ctx.src, False).stdout.strip() == "true":
        raise RuntimeError("PROMISOR_CHECKOUT")


def verify_tree_physical_exact(ctx):
    entries = run(["git", "ls-tree", "-r", "--full-tree", "HEAD"], ctx.src).stdout.splitlines()
    tracked = set()
    for line in entries:
        mode, typ, rest = line.split(None, 2)
        obj, path = rest.split("\t", 1)
        tracked.add(path)
        if typ != "blob":
            continue
        p = ctx.src / path
        if mode == "120000":
            if not p.is_symlink():
                raise RuntimeError("EXPECTED_SYMLINK:" + path)
            continue
        if not p.is_file() or p.is_symlink():
            raise RuntimeError("BLOB_TYPE_MISMATCH:" + path)
        actual = run(["git", "hash-object", "--no-filters", str(p)], ctx.src).stdout.strip()
        if actual != obj:
            raise RuntimeError("BLOB_HASH_MISMATCH:" + path)
    physical = {str(p.relative_to(ctx.src)) for p in ctx.src.rglob("*")
                if ".git" not in p.parts and p.is_file()}
    generated = {"node_modules", ".venv", "vendor", "target", "dist"}
    extra = [x for x in physical if x not in tracked
             and not any(x == g or x.startswith(g + "/") for g in generated)]
    if extra:
        raise RuntimeError("UNEXPECTED_SOURCE_FILES:" + str(extra[:20]))


def verify_submodules(ctx):
    if not (ctx.src / ".gitmodules").exists():
        return
    run(["git", "submodule", "sync", "--recursive"], ctx.src)
    run(["git", "submodule", "update", "--init", "--recursive"], ctx.src)
    for line in run(["git", "submodule", "status", "--recursive"], ctx.src).stdout.splitlines():
        if line.strip() and line[0] in "-+":
            raise RuntimeError("SUBMODULE_SHA_MISMATCH:" + line)


def verify_lfs(ctx):
    found = False
    for p in ctx.src.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            b = p.read_bytes()[:200]
        except Exception:
            continue
        if b.startswith(b"version https://git-lfs.github.com/spec/v1"):
            found = True
            break
    if found:
        if shutil.which("git-lfs") is None:
            raise RuntimeError("LFS_REQUIRED_BUT_UNAVAILABLE")
        run(["git", "lfs", "pull"], ctx.src)
        if "missing" in run(["git", "lfs", "status"], ctx.src).stdout.lower():
            raise RuntimeError("LFS_OBJECT_MISSING")


def verify_checksum(ctx):
    expected = ctx.recipe["pin"].get("checksum_sha256")
    if not expected:
        raise RuntimeError("CHECKSUM_REQUIRED_BUT_MISSING_IN_RECIPE")
    target_file = ctx.recipe["pin"].get("checksum_target")
    p = (ctx.src / target_file) if target_file else ctx.src
    if p.is_dir():
        raise RuntimeError("CHECKSUM_TARGET_MUST_BE_A_FILE")
    if sha(p) != expected:
        raise RuntimeError("CHECKSUM_MISMATCH")


def verify_toolchain_pin(ctx):
    tc = ctx.recipe["toolchain"]
    actual = run(tc["version_check_command"]).stdout.strip()
    if tc["expected_version"] not in actual:
        raise RuntimeError(f"TOOLCHAIN_MISMATCH:{actual}!={tc['expected_version']}")
    (ctx.work / "toolchain.json").write_text(json.dumps(
        {"manager": tc["manager"], "actual": actual, "expected": tc["expected_version"]}, indent=2))


def hash_lock_before(ctx):
    lockfile = ctx.src / ctx.recipe["dependencies"]["lockfile_path"]
    if not lockfile.exists():
        raise RuntimeError("LOCKFILE_DECLARED_BUT_MISSING:" + str(lockfile))
    (ctx.work / "lock.before").write_text(sha(lockfile))


def install_dependencies(ctx):
    run(ctx.recipe["dependencies"]["install_command"], ctx.src)


def verify_lock_unchanged(ctx):
    lockfile = ctx.src / ctx.recipe["dependencies"]["lockfile_path"]
    if sha(lockfile) != (ctx.work / "lock.before").read_text():
        raise RuntimeError("LOCK_CHANGED")
