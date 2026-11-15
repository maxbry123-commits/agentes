"""Pre-release validation. Run: python scripts/prepare_release.py"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    print("\n  Cognithor Release Readiness Check\n")
    failed = []

    # 1. Version sync
    with open(ROOT / "pyproject.toml", "rb") as f:
        toml_ver = tomllib.load(f)["project"]["version"]
    init_text = (ROOT / "src" / "cognithor" / "__init__.py").read_text()
    init_ver = ""
    for line in init_text.splitlines():
        if line.startswith("__version__"):
            init_ver = line.split('"')[1]
            break
    ok = toml_ver == init_ver
    print(f"  {'[OK]' if ok else '[FAIL]'} Version sync: pyproject={toml_ver}, init={init_ver}")
    if not ok:
        failed.append("version sync")

    # 2. Ruff lint
    r = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/"], cwd=ROOT, capture_output=True
    )
    ok = r.returncode == 0
    print(f"  {'[OK]' if ok else '[FAIL]'} Ruff lint")
    if not ok:
        failed.append("ruff lint")

    # 3. Ruff format
    r = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "src/"],
        cwd=ROOT,
        capture_output=True,
    )
    ok = r.returncode == 0
    print(f"  {'[OK]' if ok else '[FAIL]'} Ruff format")
    if not ok:
        failed.append("ruff format")

    # 4. CHANGELOG has entry
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    ok = f"[{toml_ver}]" in changelog
    print(f"  {'[OK]' if ok else '[FAIL]'} CHANGELOG entry for v{toml_ver}")
    if not ok:
        failed.append("changelog")

    # 5. Wheel builds
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", td],
            cwd=ROOT,
            capture_output=True,
            timeout=120,
        )
    ok = r.returncode == 0
    print(f"  {'[OK]' if ok else '[FAIL]'} Wheel build")
    if not ok:
        failed.append("wheel build")

    # Summary
    print()
    if failed:
        print(f"  BLOCKED: {len(failed)} check(s) failed: {', '.join(failed)}")
        return 1
    print("  RELEASE READY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
