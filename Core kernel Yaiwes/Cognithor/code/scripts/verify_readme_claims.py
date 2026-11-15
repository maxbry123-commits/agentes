"""Verify README numeric claims against codebase reality."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def count_test_files() -> int:
    return len(list((ROOT / "tests").rglob("test_*.py")))


def count_test_functions() -> int:
    count = 0
    for f in (ROOT / "tests").rglob("test_*.py"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        count += len(re.findall(r"^\s*(?:async\s+)?def test_", text, re.MULTILINE))
    return count


def count_mcp_tools() -> int:
    """Count tool registrations across the codebase."""
    seen_files: set[str] = set()
    count = 0
    # MCP directory
    for f in (ROOT / "src" / "cognithor" / "mcp").rglob("*.py"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        count += text.count("register_builtin_handler(")
        seen_files.add(str(f))
    # Other tool sources outside mcp/
    for pattern in ["*_tools.py", "**/tools.py"]:
        for f in (ROOT / "src" / "cognithor").rglob(pattern):
            if str(f) in seen_files:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            count += text.count("register_builtin_handler(")
            seen_files.add(str(f))
    # Skills generator
    gen = ROOT / "src" / "cognithor" / "skills" / "generator.py"
    if gen.exists() and str(gen) not in seen_files:
        text = gen.read_text(encoding="utf-8", errors="ignore")
        count += text.count("register_builtin_handler(")
    return count


def count_channels() -> int:
    channels_dir = ROOT / "src" / "cognithor" / "channels"
    # Exclude utility/base files that are not channels themselves
    exclude = {
        "__init__.py",
        "base.py",
        "config_routes.py",
        "commands.py",
        "connectors.py",
        "interactive.py",
        "talk_mode.py",
        "tts_elevenlabs.py",
        "voice_bridge.py",
        "voice_ws_bridge.py",
        "wake_word.py",
        "vscode_routes.py",
    }
    count = 0
    for f in channels_dir.glob("*.py"):
        if f.name in exclude or f.name.startswith("_"):
            continue
        count += 1
    # webchat directory counts as one channel (webui already counted)
    return count


def count_providers() -> int:
    """Count LLM provider options from config.py Literal type."""
    config = (ROOT / "src" / "cognithor" / "config.py").read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"llm_backend_type:\s*Literal\[(.*?)\]", config, re.DOTALL)
    if match:
        return len(re.findall(r'"(\w[\w-]*)"', match.group(1)))
    return 0


def main() -> int:
    print("\n  README Claims Verification\n")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    issues: list[str] = []

    # Counts
    test_files = count_test_files()
    test_funcs = count_test_functions()
    tools = count_mcp_tools()
    channels = count_channels()
    providers = count_providers()

    print(f"  Test files:      {test_files}")
    print(f"  Test functions:  {test_funcs}")
    print(f"  MCP tools:       {tools}")
    print(f"  Channels:        {channels}")
    print(f"  LLM providers:   {providers}")
    print()

    # Verify README claims
    checks = [
        (r"(\d[\d,]+)\+?\s*tests", test_funcs, "tests"),
        (r"(\d+)\+?\s*(?:MCP\s+)?[Tt]ools", tools, "tools"),
        (r"(\d+)\s*[Cc]hannels", channels, "channels"),
        (r"(\d+)\s*(?:LLM\s+)?[Pp]roviders", providers, "providers"),
    ]

    for pattern, actual, label in checks:
        match = re.search(pattern, readme)
        if match:
            claimed = int(match.group(1).replace(",", ""))
            if actual < claimed * 0.9:  # >10% under-delivery
                issues.append(f"{label}: README claims {claimed}, actual {actual}")
                print(f"  [WARN] {label}: claimed={claimed}, actual={actual}")
            elif actual > claimed * 1.15:  # >15% understated
                print(f"  [INFO] {label}: claimed={claimed}, actual={actual} (consider updating)")
            else:
                print(f"  [OK]   {label}: claimed={claimed}, actual={actual}")
        else:
            print(f"  [SKIP] {label}: no claim found in README")

    if issues:
        print(f"\n  {len(issues)} claim(s) need updating")
        return 1

    print("\n  All claims verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
