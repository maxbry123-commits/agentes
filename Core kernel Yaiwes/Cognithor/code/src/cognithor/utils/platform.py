"""Cross-platform utility functions.

Centralizes platform detection and platform-specific defaults
so that no module needs to hardcode OS-specific values.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal


def get_platform_name() -> Literal["macos", "windows", "linux"]:
    """Return a normalized platform identifier."""
    if sys.platform == "darwin":
        return "macos"
    if sys.platform == "win32":
        return "windows"
    return "linux"


def get_user_data_dir() -> Path:
    """Return the platform-appropriate user data directory for Cognithor.

    - macOS: ~/Library/Application Support/Cognithor
    - Windows: %APPDATA%/Cognithor
    - Linux: ~/.local/share/cognithor
    """
    platform = get_platform_name()
    if platform == "macos":
        return Path.home() / "Library" / "Application Support" / "Cognithor"
    if platform == "windows":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "Cognithor"
    # Linux / other Unix
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "cognithor"


def get_max_concurrent_agents() -> int:
    """Return the default max concurrent agent count for the current platform."""
    platform = get_platform_name()
    if platform == "linux":
        return 8
    return 4  # macOS, Windows


def supports_curses() -> bool:
    """Return True if the current terminal likely supports curses."""
    if get_platform_name() == "windows":
        try:
            import curses  # noqa: F401 — windows-curses

            return True
        except ImportError:
            return False
    # Unix: curses is in stdlib
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    if term in ("dumb", ""):
        return False
    return True
