"""Detect the AV-quarantine failure class at boot: the claude-agent-sdk's bundled
CLI binary deleted out from under an installed app (Windows-only in field data;
22 of 25 affected installs never produced another agent reply). Returns the
expected path when the binary is gone so the health pill can tell the user how
to repair, None when it's present or there is nothing to verify."""
import platform
from pathlib import Path
from typing import Optional
from typeguard import typechecked


@typechecked
def bundled_cli_missing() -> Optional[str]:
    try:
        import claude_agent_sdk
        p_pkg = Path(claude_agent_sdk.__file__).parent
    except Exception:
        return None
    p_name = "claude.exe" if platform.system() == "Windows" else "claude"
    p_bundled = p_pkg / "_bundled" / p_name
    # No _bundled dir at all = a source install running the PATH CLI; nothing to verify (quarantine removes the file, not the dir).
    if not p_bundled.parent.is_dir():
        return None
    if p_bundled.is_file():
        return None
    return str(p_bundled)
