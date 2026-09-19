#!/usr/bin/env python3
"""
CI helper (NOT a motor): stages the curated Yaiwes scope from the `agentes`
checkout into /tmp/yaiwes-staging, so motor_3_copy_batches.py (immutable)
can then copy it verified-by-hash into the Yaiwes checkout.

This script is intentionally separate from the motors themselves: the
skill's rule is that motor source code is untouchable/copy-only. This file
is ordinary project tooling, free to edit, whose only job is to build
SOURCE_DIR before the motor runs.

Run from the repo root of the `agentes` checkout (the workflow sets cwd
to `agentes/` implicitly via the paths below being relative to it — this
script resolves paths relative to its own location instead, so it is
robust to being invoked from anywhere).
"""
from __future__ import annotations
import pathlib
import shutil
import sys

# Resolve the `agentes` checkout root: this script lives at
# agentes/scripts_ci/stage_files.py, so parent.parent is the checkout root.
AGENTES_ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGING = pathlib.Path("/tmp/yaiwes-staging")

# (source relative path under agentes/, destination name under staging/)
# Using a list of tuples avoids any shell quoting/emoji issues entirely --
# these are just Python string comparisons against the filesystem.
COPY_PLAN: list[tuple[str, str]] = [
    ("Agente Yaiwes principal", "Agente Yaiwes principal"),
    ("Core kernel Yaiwes", "Core kernel Yaiwes"),
    ("➡️\U0001f4c2 wordflow loop code Yaiwes", "wordflow loop code Yaiwes"),
    ("arquitectura wordflow loop code Yaiwes", "arquitectura wordflow loop code Yaiwes"),
    ("Skills agente", "Skills agente"),
    ("Skills", "Skills"),
    ("Conecciones router inteligente universal", "Conecciones router inteligente universal"),
    ("Documentos proyectos Yaiwes", "Documentos proyectos Yaiwes"),
    (
        "➡️\U0001f4c2motores de descarga extracción copiado movimiento archivos agentes",
        "motores de descarga extraccion copiado movimiento archivos agentes",
    ),
    ("Readme arquitectura Yaiwes", "Readme arquitectura Yaiwes"),
    (
        "\U0001f4c2coda workflow persistencias",
        "coda workflow persistencias (pendiente de integrar)",
    ),
    (".cursor", ".cursor"),
    (".github", ".github"),
    (".gitmodules", ".gitmodules"),
    ("AGENTS.md", "AGENTS.md"),
    ("\U0001f4c2 Bitácora stated JSON Craxy wall.json", "Bitacora stated JSON Craxy wall.json"),
    (
        "\U0001f4c2 Readme Handoff core integracion y wachdog.md",
        "Readme Handoff core integracion y wachdog.md",
    ),
    ("\U0001f4c2 Readme arquitectura Yaiwes.md", "Readme arquitectura Yaiwes (general).md"),
    (
        "\U0001f4c2 Readme plan wachdog y trabajo en paralelo.md",
        "Readme plan wachdog y trabajo en paralelo.md",
    ),
    (
        "PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md",
        "PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md",
    ),
]

# Known stale/duplicate files to drop AFTER staging (relative to staging/).
DROP_AFTER_STAGE: list[str] = [
    "wordflow loop code Yaiwes/➡️\U0001f4c2 README arquitectura Wordflow LOOP Yaiwes.md",
]

# Collected across the whole run: (src, dst, why) for entries copytree
# could not copy (broken symlinks, files git didn't materialize, etc).
# These are logged but never fail the build -- the read-back step at the
# end of the workflow makes any real gap visible.
COPY_ERRORS: list[tuple[str, str, str]] = []


def copy_one(src_rel: str, dst_rel: str) -> str:
    src = AGENTES_ROOT / src_rel
    dst = STAGING / dst_rel
    if not src.exists():
        return f"SKIP (not found): {src_rel}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        try:
            shutil.copytree(src, dst, dirs_exist_ok=True)
        except shutil.Error as e:
            # copytree copies everything it can and only raises at the end
            # with the full list of per-file failures (e.g. broken
            # symlinks or entries git listed but didn't materialize on
            # disk). Treat those as non-fatal: log each one and keep the
            # rest of what was actually copied, instead of aborting the
            # whole staging step.
            for failure in e.args[0]:
                # failure is (src_path, dst_path, error_str) most of the
                # time, but be defensive about shape just in case.
                if len(failure) == 3:
                    fsrc, fdst, ferr = failure
                else:
                    fsrc, ferr = str(failure), ""
                    fdst = ""
                COPY_ERRORS.append((str(fsrc), str(fdst), str(ferr)))
            return f"OK dir (with {len(e.args[0])} skipped entries): {src_rel} -> {dst_rel}"
        return f"OK dir: {src_rel} -> {dst_rel}"
    shutil.copy2(src, dst)
    return f"OK file: {src_rel} -> {dst_rel}"


def main() -> int:
    STAGING.mkdir(parents=True, exist_ok=True)
    print(f"AGENTES_ROOT={AGENTES_ROOT}")
    print(f"STAGING={STAGING}")

    missing = []
    for src_rel, dst_rel in COPY_PLAN:
        result = copy_one(src_rel, dst_rel)
        print(result)
        if result.startswith("SKIP"):
            missing.append(src_rel)

    for rel in DROP_AFTER_STAGE:
        p = STAGING / rel
        if p.exists():
            p.unlink()
            print(f"DROPPED stale: {rel}")

    print("--- staging top-level ---")
    for p in sorted(STAGING.iterdir()):
        print(" ", p.name)

    if missing:
        print("--- WARNING: sources not found (check names/encoding) ---")
        for m in missing:
            print(" ", m)
        # Non-fatal: continue, motor_3 will just have less to copy. The
        # read-back step at the end of the workflow will make gaps visible.

    if COPY_ERRORS:
        print(f"--- WARNING: {len(COPY_ERRORS)} individual entries could not be copied "
              f"(broken symlinks / files not materialized by git) ---")
        for fsrc, fdst, ferr in COPY_ERRORS:
            print(f"  SKIP: {fsrc} ({ferr})")
        # Also non-fatal, for the same reason as `missing` above.

    return 0


if __name__ == "__main__":
    sys.exit(main())
