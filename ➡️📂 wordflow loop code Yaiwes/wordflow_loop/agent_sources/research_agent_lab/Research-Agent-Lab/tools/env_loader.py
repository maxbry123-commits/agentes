from __future__ import annotations

from pathlib import Path
import os


def load_env_file(path: Path | str = ".env", override: bool = False) -> dict[str, str]:
    env_path = Path(path)
    loaded: dict[str, str] = {}
    if not env_path.exists():
        return loaded
    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded


def mask_secret(value: str) -> str:
    if not value:
        return "<empty>"
    if len(value) <= 12:
        return "<too_short>"
    return f"{value[:6]}...{value[-4:]}"
