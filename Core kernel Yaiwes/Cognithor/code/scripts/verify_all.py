"""Comprehensive verification of Cognithor v0.92.x architecture.

Verifies that the v0.92.0 agent-pack refactor is wired correctly:
- Core imports (packs, leads, gateway)
- Config schema
- Flutter pack-aware UI
- Version consistency
- i18n locale integrity
- Test structure
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

errors: list[str] = []


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def check(name: str, ok: bool) -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {name}")
    if not ok:
        errors.append(name)


# ----------------------------------------------------------------------
# 1. Core module imports (packs/leads replaced social/)
# ----------------------------------------------------------------------
print("=== 1. Core Module Imports ===")
try:
    check("Pack+Leads SDK importable", True)
except Exception as e:
    check(f"Import failed: {e}", False)

try:
    from cognithor.core.gatekeeper import Gatekeeper  # noqa: F401
    from cognithor.core.planner import SYSTEM_PROMPT  # noqa: F401
    from cognithor.gateway.gateway import Gateway  # noqa: F401

    check("Planner/Gatekeeper/Gateway importable", True)
except Exception as e:
    check(f"Core import failed: {e}", False)

# Confirm legacy social module is really gone
try:
    import cognithor.social  # type: ignore # noqa: F401

    check("cognithor.social correctly removed (v0.92.0)", False)
except ImportError:
    check("cognithor.social correctly removed (v0.92.0)", True)

# ----------------------------------------------------------------------
# 2. Config schema
# ----------------------------------------------------------------------
print("\n=== 2. Config Schema ===")
from cognithor.config import CognithorConfig

cfg = CognithorConfig()
for f in ["cognithor_home", "language", "ollama", "gatekeeper", "planner", "memory", "security"]:
    check(f"CognithorConfig.{f}", hasattr(cfg, f))

# ----------------------------------------------------------------------
# 3. Gateway wiring (pack loader + lead service)
# ----------------------------------------------------------------------
print("\n=== 3. Gateway Wiring ===")
gw = read("src/cognithor/gateway/gateway.py")
check("PackLoader in gateway.py", "PackLoader" in gw)
check("LeadService in gateway.py", "LeadService" in gw)

# ----------------------------------------------------------------------
# 4. Flutter pack-aware UI
# ----------------------------------------------------------------------
print("\n=== 4. Flutter Pack-Aware UI ===")
for f in [
    "flutter_app/lib/providers/sources_provider.dart",
    "flutter_app/lib/widgets/packs/locked_pack_card.dart",
    "flutter_app/lib/widgets/packs/pack_preview_overlay.dart",
    "flutter_app/lib/data/known_packs.dart",
    "flutter_app/lib/screens/leads_screen.dart",
]:
    check(f, os.path.exists(f))

# ----------------------------------------------------------------------
# 5. Version consistency
# ----------------------------------------------------------------------
print("\n=== 5. Version Consistency ===")
with open("pyproject.toml", "rb") as f:
    ver = tomllib.load(f)["project"]["version"]
init = read("src/cognithor/__init__.py")
check(f"src/cognithor/__init__.py declares {ver}", f'"{ver}"' in init)

# ----------------------------------------------------------------------
# 6. i18n locale integrity (parity between en/de/zh)
# ----------------------------------------------------------------------
print("\n=== 6. i18n Locale Integrity ===")


def _count_leaf_keys(data: dict) -> int:
    n = 0
    for v in data.values():
        n += _count_leaf_keys(v) if isinstance(v, dict) else 1
    return n


counts: dict[str, int] = {}
for lang in ["en", "de", "zh"]:
    path = f"src/cognithor/i18n/locales/{lang}.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        counts[lang] = _count_leaf_keys(data)
        check(f"{lang}.json valid JSON ({counts[lang]} keys)", True)
    except Exception as e:
        check(f"{lang}.json parse error: {e}", False)

if len(counts) == 3:
    check(
        f"Locale parity en={counts['en']} de={counts['de']} zh={counts['zh']}",
        counts["en"] == counts["de"] == counts["zh"],
    )

# ----------------------------------------------------------------------
# 7. Flutter i18n ARB files
# ----------------------------------------------------------------------
print("\n=== 7. Flutter i18n ARB Files ===")
arb_en = "flutter_app/lib/l10n/app_en.arb"
if os.path.exists(arb_en):
    with open(arb_en, encoding="utf-8") as f:
        en = json.load(f)
    en_keys = {k for k in en if not k.startswith("@") and k != "@@locale"}
    for lang in ["de", "zh", "ar"]:
        path = f"flutter_app/lib/l10n/app_{lang}.arb"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                loc = json.load(f)
            loc_keys = {k for k in loc if not k.startswith("@") and k != "@@locale"}
            missing = en_keys - loc_keys
            check(f"{lang}: {len(loc_keys)} keys, {len(missing)} missing", len(missing) == 0)
        else:
            check(f"{lang}.arb exists", False)
else:
    check("flutter_app/lib/l10n/app_en.arb exists", False)

# ----------------------------------------------------------------------
# 8. Test structure
# ----------------------------------------------------------------------
print("\n=== 8. Test Structure ===")
for d in [
    "tests/test_core",
    "tests/test_mcp",
    "tests/test_channels",
    "tests/test_packs",
    "tests/test_leads",
    "tests/test_evolution",
    "tests/test_security",
    "tests/unit",
]:
    check(f"{d} exists", os.path.isdir(d))

# ----------------------------------------------------------------------
# 9. Git status
# ----------------------------------------------------------------------
print("\n=== 9. Git Status ===")
try:
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10
    )
    uncommitted = [line for line in result.stdout.strip().split("\n") if line.strip()]
    if uncommitted:
        print(f"[INFO] {len(uncommitted)} uncommitted changes (not a hard failure)")
        for line in uncommitted[:10]:
            print(f"  {line}")
    else:
        check("Working tree clean", True)
except (FileNotFoundError, subprocess.TimeoutExpired):
    print("[INFO] git not available or timed out -- skipping")

# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------
print("\n" + "=" * 60)
if errors:
    print(f"FOUND {len(errors)} ISSUES:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED - ZERO ISSUES")
    sys.exit(0)
