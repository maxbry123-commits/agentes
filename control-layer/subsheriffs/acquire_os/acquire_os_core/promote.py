#!/usr/bin/env python3
"""ACQUIRE-OS v1 — promote.py — nodos 18-28: provenance, manifest,
LICENSE_GATE, SECRET_SCAN, promoción atómica local, hashes finales."""
import json
import re
import shutil
import time
import platform
from acquire_os_core.core import run, sha, COMMAND_LOG

OSS_LICENSES = ["MIT", "Apache-2.0", "Apache License", "BSD", "GPL", "LGPL",
                "MPL", "ISC", "Unlicense", "CC0"]

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"hf_[A-Za-z0-9]{34}"),
]


def provenance(ctx):
    x = {"source_type": ctx.recipe["source_type"], "pin": ctx.recipe["pin"],
         "results": ctx.results, "platform": platform.platform(),
         "architecture": platform.machine(), "time": time.time(),
         "commands": COMMAND_LOG}
    ctx.provenance_file.write_text(json.dumps(x, indent=2))


def manifest_from_disk(ctx):
    files = []
    for p in sorted(ctx.src.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            files.append({"path": str(p.relative_to(ctx.src)),
                          "size": p.stat().st_size, "sha256": sha(p)})
    ctx.manifest.write_text(json.dumps(
        {"source_type": ctx.recipe["source_type"], "pin": ctx.recipe["pin"],
         "source_files": files, "source_file_count": len(files),
         "status": "PENDING_FINAL_VERIFY"}, indent=2))


def source_hash_before_promote(ctx):
    listing = "\n".join(sorted(str(p.relative_to(ctx.src)) for p in ctx.src.rglob("*")
                                if p.is_file() and ".git" not in p.parts))
    (ctx.work / "listing_before.txt").write_text(listing)
    (ctx.work / "source_hash_before.txt").write_text(sha(ctx.work / "listing_before.txt"))


def audit_dinamico(ctx):
    """Devuelve DOS métricas distintas, no una sola ambigua:
    - coverage_score: % de los 28 nodos declarados que APLICARON a este
      source_type (los SKIPPED_EXPECTED no cuentan como aplicados).
    - quality_score: % de comandos ejecutados (COMMAND_LOG, incluye los
      corridos con check=False) que terminaron con exit_code==0. Mide
      qué tan "limpia" fue la corrida, independiente de cuánto aplicó."""
    aplicables = [n for n, v in ctx.results.items() if v != "SKIPPED_EXPECTED"]
    fallidos = [n for n, v in ctx.results.items() if v == "FAILED"]
    if fallidos:
        raise RuntimeError("AUDIT_FAILED:" + str(fallidos))
    if not ctx.provenance_file.exists() or not ctx.manifest.exists():
        raise RuntimeError("AUDIT_MISSING_EVIDENCE")
    comandos = COMMAND_LOG
    comandos_ok = [c for c in comandos if c["exit_code"] == 0]
    coverage_score = 100.0 * len(aplicables) / max(len(ctx.results), 1)
    quality_score = 100.0 * len(comandos_ok) / max(len(comandos), 1)
    (ctx.work / "audit_dinamico.json").write_text(json.dumps(
        {"checks_aplicables": len(aplicables), "checks_totales": len(ctx.results),
         "coverage_score": coverage_score,
         "comandos_ok": len(comandos_ok), "comandos_totales": len(comandos),
         "quality_score": quality_score}, indent=2))


def license_gate(ctx):
    for name in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]:
        p = ctx.src / name
        if p.exists():
            text = p.read_text(errors="ignore")[:2000]
            if any(lic in text for lic in OSS_LICENSES):
                (ctx.work / "license.txt").write_text(name)
                return
            raise RuntimeError("LICENSE_NOT_IN_OSS_ALLOWLIST:" + name)
    raise RuntimeError("NO_LICENSE_FILE_FOUND")


MAX_SCAN_SIZE_BYTES = 5 * 1024 * 1024  # 5MB: archivos mas grandes no son
                                        # config/codigo tipico con secretos,
                                        # y leerlos completos cuelga el nodo


def secret_scan(ctx):
    hits = []
    for p in ctx.src.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            if p.stat().st_size > MAX_SCAN_SIZE_BYTES:
                continue
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(str(p.relative_to(ctx.src)))
                break
    if hits:
        raise RuntimeError("SECRETS_DETECTED:" + str(hits[:10]))


def promote(ctx):
    tmp = ctx.final.parent / (".promote-tmp-" + str(int(time.time())))
    try:
        shutil.copytree(ctx.src, tmp / "source")
        for p in [ctx.provenance_file, ctx.manifest, ctx.work / "artifacts.json"]:
            if p.exists():
                shutil.copy2(p, tmp / p.name)
        tmp.rename(ctx.final)
    except Exception:
        if tmp.exists():
            shutil.move(str(tmp), str(ctx.quarantine / "failed-promote"))
        raise RuntimeError("PROMOTION_FAILED_QUARANTINED")


def source_hash_after_promote(ctx):
    f = ctx.final / "source"
    listing = "\n".join(sorted(str(p.relative_to(f)) for p in f.rglob("*")
                                if p.is_file() and ".git" not in p.parts))
    (ctx.work / "listing_after.txt").write_text(listing)
    before = (ctx.work / "source_hash_before.txt").read_text()
    after = sha(ctx.work / "listing_after.txt")
    if before != after:
        raise RuntimeError("SOURCE_CHANGED_DURING_PROMOTION")


def final_identity(ctx):
    f = ctx.final / "source"
    if ctx.recipe["source_type"] == "git_native":
        if run(["git", "rev-parse", "HEAD"], f).stdout.strip() != ctx.recipe["pin"]["commit"]:
            raise RuntimeError("FINAL_HEAD_MISMATCH")
        if run(["git", "status", "--porcelain"], f).stdout.strip():
            raise RuntimeError("FINAL_DIRTY")
    if not (ctx.final / "provenance.json").exists() or not (ctx.final / "manifest.json").exists():
        raise RuntimeError("FINAL_PROOF_MISSING")


def final_hashes(ctx):
    fh = {"journal_sha256": sha(ctx.journal), "manifest_sha256": sha(ctx.manifest),
          "provenance_sha256": sha(ctx.provenance_file)}
    (ctx.final / "final_hashes.json").write_text(json.dumps(fh, indent=2))


def done(ctx):
    print("COMPLETE=TRUE")
    print("SOURCE_TYPE=" + ctx.recipe["source_type"])
    print("FINAL=" + str(ctx.final))
