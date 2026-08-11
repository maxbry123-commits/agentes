#!/usr/bin/env python3
"""ACQUIRE-OS v1 — build.py — nodos 12-17: build, install, verificación
de runtime. Ningún comando está escrito aquí: todos vienen de la Recipe
(recipe.build.commands, recipe.install, recipe.verify.commands)."""
import json
from acquire_os_core.core import run, sha


def build(ctx):
    for cmd in ctx.recipe["build"]["commands"]:
        run(cmd, ctx.src)


def verify_build_outputs(ctx):
    for out in ctx.recipe["build"].get("outputs", []):
        if not (ctx.src / out).exists():
            raise RuntimeError("BUILD_OUTPUT_MISSING:" + out)


def index_artifacts(ctx):
    out = []
    build_cfg = ctx.recipe.get("build") or {}   # build puede ser null explícito, no solo ausente
    for root in build_cfg.get("outputs", []):
        base = ctx.src / root
        if base.is_dir():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    out.append({"path": str(p.relative_to(ctx.src)),
                                "size": p.stat().st_size, "sha256": sha(p)})
        elif base.is_file():
            out.append({"path": root, "size": base.stat().st_size, "sha256": sha(base)})
    (ctx.work / "artifacts.json").write_text(json.dumps(out, indent=2))


def install(ctx):
    inst = ctx.recipe["install"]
    if inst["method"] == "none":
        return
    local_artifact = ctx.recipe.get("pin", {}).get("local_artifact_path")
    for cmd in inst.get("commands", []):
        # sustituye el placeholder por el archivo YA verificado en
        # 07_VERIFY_CHECKSUM — nunca se vuelve a buscar en vivo en el
        # registro (decisión: estricto, confirmada por el Director)
        resolved = [local_artifact if tok == "${LOCAL_ARTIFACT}" else tok for tok in cmd]
        if "${LOCAL_ARTIFACT}" in cmd and not local_artifact:
            raise RuntimeError("LOCAL_ARTIFACT_REQUIRED_BUT_NOT_SET_BY_SOURCE_ADAPTER")
        run(resolved, ctx.src)


def verify_install_target(ctx):
    inst = ctx.recipe["install"]
    check_cmd = inst.get("verify_target_command")
    if not check_cmd:
        return
    p = run(check_cmd, None, False)
    if p.returncode != 0:
        raise RuntimeError("INSTALL_TARGET_NOT_FOUND")
    target = p.stdout.strip()
    expected_root = str(ctx.src.resolve())
    if expected_root not in target:
        raise RuntimeError("INSTALL_POINTS_TO_WRONG_LOCATION:" + target)


def runtime_verify(ctx):
    results = []
    for cmd in ctx.recipe["verify"]["commands"]:
        p = run(cmd, ctx.src, False)
        results.append({"command": cmd, "exit_code": p.returncode})
        if p.returncode != 0:
            raise RuntimeError("RUNTIME_VERIFY_FAILED:" + str(cmd))
    (ctx.work / "runtime_verify.json").write_text(json.dumps(results, indent=2))
