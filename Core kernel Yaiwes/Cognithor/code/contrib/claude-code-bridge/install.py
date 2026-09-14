#!/usr/bin/env python3
"""Idempotent installer for the Cognithor <-> Claude Code hook bridge.

Merges a ``hooks`` block into ``~/.claude/settings.json`` (or the path you
pass with ``--settings``). Existing hooks are preserved -- the installer
only adds its own entries, identified by the ``_cognithor_bridge`` tag.

Run ``install.py --uninstall`` to remove the Cognithor hooks again.

Run ``install.py --dry-run`` to see the merged JSON without writing.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import sys
import time
from pathlib import Path

DEFAULT_URL = "http://localhost:8741"
TAG_KEY = "_cognithor_bridge"
TAG_VALUE = "cognithor-hook-bridge"

HOOK_BLUEPRINT = {
    "PreToolUse": {"path": "/api/claude-hooks/pre-tool-use", "timeout": 30, "matcher": ""},
    "PostToolUse": {"path": "/api/claude-hooks/post-tool-use", "timeout": 30, "matcher": ""},
    "Stop": {"path": "/api/claude-hooks/stop", "timeout": 60, "matcher": ""},
    "SessionStart": {
        "path": "/api/claude-hooks/session-start",
        "timeout": 10,
        "matcher": "startup|resume",
    },
    "SessionEnd": {"path": "/api/claude-hooks/session-end", "timeout": 10, "matcher": ""},
}


def default_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON: {exc}")


def build_hook_entry(
    *, event: str, base_url: str, token_env: str | None
) -> dict:
    info = HOOK_BLUEPRINT[event]
    http_hook: dict = {
        "type": "http",
        "url": f"{base_url.rstrip('/')}{info['path']}",
        "timeout": info["timeout"],
        TAG_KEY: TAG_VALUE,
    }
    if token_env:
        http_hook["headers"] = {"Authorization": f"Bearer ${token_env}"}
        http_hook["allowedEnvVars"] = [token_env]
    return {
        "matcher": info["matcher"],
        "hooks": [http_hook],
        TAG_KEY: TAG_VALUE,
    }


def strip_cognithor_blocks(hooks_section: dict) -> dict:
    """Remove prior Cognithor-tagged entries so re-install is clean."""
    cleaned: dict[str, list] = {}
    for event, groups in hooks_section.items():
        if not isinstance(groups, list):
            continue
        keep = [g for g in groups if not (isinstance(g, dict) and g.get(TAG_KEY) == TAG_VALUE)]
        if keep:
            cleaned[event] = keep
    return cleaned


def install(
    settings: dict, *, base_url: str, token_env: str | None
) -> dict:
    result = dict(settings)
    hooks_section = dict(result.get("hooks") or {})
    hooks_section = strip_cognithor_blocks(hooks_section)

    for event in HOOK_BLUEPRINT:
        entry = build_hook_entry(event=event, base_url=base_url, token_env=token_env)
        hooks_section.setdefault(event, []).append(entry)

    result["hooks"] = hooks_section
    return result


def uninstall(settings: dict) -> dict:
    result = dict(settings)
    hooks_section = result.get("hooks")
    if not isinstance(hooks_section, dict):
        return result
    cleaned = strip_cognithor_blocks(hooks_section)
    if cleaned:
        result["hooks"] = cleaned
    else:
        result.pop("hooks", None)
    return result


def diff(before: dict, after: dict) -> str:
    a = json.dumps(before, indent=2, sort_keys=True).splitlines(keepends=True)
    b = json.dumps(after, indent=2, sort_keys=True).splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(a, b, fromfile="before", tofile="after", n=3)
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--settings",
        type=Path,
        default=default_settings_path(),
        help="Path to Claude Code settings.json (default: ~/.claude/settings.json).",
    )
    p.add_argument(
        "--url",
        default=os.environ.get("COGNITHOR_URL", DEFAULT_URL),
        help="Cognithor gateway base URL (default: env COGNITHOR_URL or %(default)s).",
    )
    p.add_argument(
        "--token-env",
        default=None,
        help=(
            "If set, the hook sends 'Authorization: Bearer $<TOKEN_ENV>'. "
            "Needed when the gateway is not loopback-only."
        ),
    )
    p.add_argument("--dry-run", action="store_true", help="Print diff, do not write.")
    p.add_argument("--uninstall", action="store_true", help="Remove Cognithor hook entries.")
    args = p.parse_args()

    settings_path: Path = args.settings
    before = load(settings_path)

    if args.uninstall:
        after = uninstall(before)
        action = "uninstall"
    else:
        after = install(before, base_url=args.url, token_env=args.token_env)
        action = "install"

    d = diff(before, after)
    if not d:
        print(f"no changes needed ({action}).")
        return 0

    print(d)
    if args.dry_run:
        print(f"(dry-run) {action} preview only. re-run without --dry-run to apply.")
        return 0

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        backup = settings_path.with_suffix(f".json.bak-{int(time.time())}")
        shutil.copy2(settings_path, backup)
        print(f"backed up existing settings -> {backup}")

    settings_path.write_text(json.dumps(after, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{action} complete -> {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
