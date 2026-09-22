#!/usr/bin/env python3
"""ACQUIRE-OS v1 — core.py — motor genérico de 28 nodos, dirigido por
Recipe. No asume ningún lenguaje, toolchain ni comando de instalación:
todo viene del diccionario `recipe` que entrega Discovery (T-005)."""
import os, sys, json, hashlib, subprocess, time
from pathlib import Path
from dataclasses import dataclass, field

COMMAND_LOG = []


@dataclass
class Context:
    recipe: dict
    checkout_path: Path
    work: Path
    final: Path
    quarantine: Path
    results: dict = field(default_factory=dict)

    def __post_init__(self):
        self.work.mkdir(parents=True, exist_ok=True)
        self.quarantine.mkdir(parents=True, exist_ok=True)
        self.journal = self.work / "journal.jsonl"
        self.manifest = self.work / "manifest.json"
        self.provenance_file = self.work / "provenance.json"
        self.src = self.checkout_path


def run(a, cwd=None, check=True):
    start = time.time()
    p = subprocess.run(a, cwd=str(cwd) if cwd else None, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    end = time.time()
    out = p.stdout or ""
    COMMAND_LOG.append({"command": a, "cwd": str(cwd) if cwd else os.getcwd(),
                         "exit_code": p.returncode, "start": start, "end": end,
                         "output_sha256": hashlib.sha256(out.encode()).hexdigest()})
    print("$", " ".join(a)); print(out, end="")
    if check and p.returncode:
        raise RuntimeError("COMMAND_FAILED:" + str(a))
    return p


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def log_event(ctx, node, status, error=None):
    with open(ctx.journal, "a") as f:
        f.write(json.dumps({"time": time.time(), "node": node, "status": status,
                             "error": error}, separators=(",", ":")) + "\n")


def checkpoint(ctx, node, nxt):
    (ctx.work / "checkpoint.json").write_text(json.dumps(
        {"node": node, "next": nxt, "time": time.time()}, indent=2))


def gate(ctx, node, nxt, fn, applicable=True):
    """Ejecuta un nodo. applicable=False -> SKIPPED_EXPECTED, no es falla."""
    if not applicable:
        ctx.results[node] = "SKIPPED_EXPECTED"
        log_event(ctx, node, "SKIPPED_EXPECTED")
        checkpoint(ctx, node, nxt)
        return
    log_event(ctx, node, "RUNNING")
    try:
        fn(ctx)
        ctx.results[node] = "PASS"
        checkpoint(ctx, node, nxt)
        log_event(ctx, node, "PASS")
    except Exception as e:
        ctx.results[node] = "FAILED"
        log_event(ctx, node, "FAILED", str(e))
        raise


# --- helpers de aplicabilidad (leen la Recipe, nunca asumen un lenguaje) ---
def is_git(ctx): return ctx.recipe.get("source_type") == "git_native"
def is_checksummable(ctx): return ctx.recipe.get("source_type") in ("release_binary", "package_manager", "hf_hub")
def has_toolchain(ctx): return bool(ctx.recipe.get("toolchain"))
def has_dependencies(ctx): return bool(ctx.recipe.get("dependencies"))
def has_build(ctx): return bool(ctx.recipe.get("build", {}).get("commands"))
def has_install(ctx): return ctx.recipe.get("install", {}).get("method", "none") != "none"
def has_verify(ctx): return bool(ctx.recipe.get("verify", {}).get("commands"))


def main(recipe, checkout_path, work_root):
    try:
        from acquire_os_core import verify as V, build as B, promote as P
    except ImportError:
        # fallback si se ejecuta core.py directo como script (sin el
        # paquete instalado ni PYTHONPATH configurado)
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from acquire_os_core import verify as V, build as B, promote as P
    ctx = Context(recipe=recipe, checkout_path=Path(checkout_path),
                  work=Path(work_root) / ".acquire",
                  final=Path(work_root) / "final",
                  quarantine=Path(work_root) / ("quarantine-" + str(int(time.time()))))
    steps = [
        ("01_RECEIVE_CHECKOUT", "02", V.receive_checkout, True),
        ("02_VERIFY_PIN_MATCH", "03", V.verify_pin_match, True),
        ("03_VERIFY_REPOSITORY_SHAPE", "04", V.verify_repository_shape, is_git(ctx)),
        ("04_VERIFY_TREE_PHYSICAL_EXACT", "05", V.verify_tree_physical_exact, is_git(ctx)),
        ("05_VERIFY_SUBMODULES", "06", V.verify_submodules, is_git(ctx)),
        ("06_VERIFY_LFS", "07", V.verify_lfs, is_git(ctx)),
        ("07_VERIFY_CHECKSUM", "08", V.verify_checksum, is_checksummable(ctx)),
        ("08_VERIFY_TOOLCHAIN_PIN", "09", V.verify_toolchain_pin, has_toolchain(ctx)),
        ("09_HASH_LOCK_BEFORE", "10", V.hash_lock_before, has_dependencies(ctx)),
        ("10_INSTALL_DEPENDENCIES", "11", V.install_dependencies, has_dependencies(ctx)),
        ("11_VERIFY_LOCK_UNCHANGED", "12", V.verify_lock_unchanged, has_dependencies(ctx)),
        ("12_BUILD", "13", B.build, has_build(ctx)),
        ("13_VERIFY_BUILD_OUTPUTS", "14", B.verify_build_outputs, has_build(ctx)),
        ("14_INDEX_ARTIFACTS", "15", B.index_artifacts, True),
        ("15_INSTALL", "16", B.install, has_install(ctx)),
        ("16_VERIFY_INSTALL_TARGET", "17", B.verify_install_target, has_install(ctx)),
        ("17_RUNTIME_VERIFY", "18", B.runtime_verify, has_verify(ctx)),
        ("18_PROVENANCE", "19", P.provenance, True),
        ("19_MANIFEST_FROM_DISK", "20", P.manifest_from_disk, True),
        ("20_SOURCE_HASH_BEFORE_PROMOTE", "21", P.source_hash_before_promote, True),
        ("21_AUDIT_DINAMICO", "22", P.audit_dinamico, True),
        ("22_LICENSE_GATE", "23", P.license_gate, True),
        ("23_SECRET_SCAN", "24", P.secret_scan, True),
        ("24_PROMOTE", "25", P.promote, True),
        ("25_SOURCE_HASH_AFTER_PROMOTE", "26", P.source_hash_after_promote, True),
        ("26_FINAL_IDENTITY", "27", P.final_identity, True),
        ("27_FINAL_HASHES", "28", P.final_hashes, True),
        ("28_DONE", "DONE", P.done, True),
    ]
    for node, nxt, fn, applicable in steps:
        gate(ctx, node, nxt, fn, applicable)
    return ctx


if __name__ == "__main__":
    recipe_arg = json.loads(Path(sys.argv[1]).read_text())
    checkout_arg = sys.argv[2]
    work_root_arg = sys.argv[3]
    try:
        main(recipe_arg, checkout_arg, work_root_arg)
        print("COMPLETE=TRUE")
    except Exception as e:
        print("COMPLETE=FALSE")
        print("FAIL=" + str(e))
        sys.exit(1)
