"""Serve-mode support (ENG-209): an open app that nobody is editing costs a whole vite dev server
(~270MB). When a FRESH built bundle exists and no agent is bound to the workspace, the runtime
serves `frontend/dist` statically through the existing workspace serve route instead of spawning
anything; vite comes back the moment an agent starts editing."""

import asyncio
import logging
import os
import subprocess
from typing import Optional

from typeguard import typechecked

logger = logging.getLogger(__name__)


@typechecked
def dist_index(workspace_path: str) -> str:
    return os.path.join(workspace_path, "frontend", "dist", "index.html")


@typechecked
def p_newest_source_mtime(workspace_path: str) -> float:
    newest = 0.0
    fe = os.path.join(workspace_path, "frontend")
    for probe in ("package.json", "vite.config.mts", "vite.config.ts", "index.html"):
        p = os.path.join(fe, probe)
        if os.path.isfile(p):
            newest = max(newest, os.path.getmtime(p))
    src = os.path.join(fe, "src")
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d != "node_modules"]
        for f in filenames:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
            except OSError:
                pass
    return newest


@typechecked
def static_fresh(workspace_path: str) -> bool:
    """A dist we can honestly serve: exists, newer than every source file, and built with RELATIVE
    asset paths (vite `base: './'`). Absolute /assets/ URLs would resolve against the backend host
    root and 404, so a dist built by an older template is refused rather than served broken."""
    idx = dist_index(workspace_path)
    if not os.path.isfile(idx):
        return False
    try:
        with open(idx, encoding="utf-8", errors="ignore") as f:
            html = f.read()
    except OSError:
        return False
    if 'src="/' in html or 'href="/' in html:
        return False
    return os.path.getmtime(idx) >= p_newest_source_mtime(workspace_path)


@typechecked
def workspace_being_edited(workspace_path: str) -> bool:
    """True when a live agent session is bound to this workspace (launch sets the chat's cwd to the
    app it edits), so serve-mode never hides an agent's in-flight changes behind a stale bundle."""
    try:
        from backend.apps.agents.agents import agent_manager
        norm = os.path.realpath(workspace_path)
        for session in agent_manager.sessions.values():
            if session.status not in ("running", "waiting_approval"):
                continue
            cwd = getattr(session, "cwd", None)
            if cwd and os.path.realpath(cwd) == norm:
                return True
    except Exception:
        logger.debug("being-edited probe failed; assuming edited (vite)", exc_info=True)
        return True
    return False


@typechecked
async def build_dist_in_background(workspace_path: str, workspace_id: str) -> Optional[int]:
    """Fire `npm run build` for a parked app so the NEXT open can serve static. Best-effort: any
    missing precondition (no node_modules, no build script) just means vite next time. Returns the
    exit code, or None when the build was skipped."""
    fe = os.path.join(workspace_path, "frontend")
    if not os.path.isdir(os.path.join(fe, "node_modules")):
        return None
    if static_fresh(workspace_path):
        return None
    node_bin = os.path.dirname(os.environ.get("OPENSWARM_NODE_PATH", "") or "")
    env = {**os.environ}
    if node_bin:
        env["PATH"] = f"{node_bin}:{env.get('PATH', '')}"
    log_path = os.path.join(workspace_path, ".openswarm", "build.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    try:
        with open(log_path, "w", encoding="utf-8") as log:
            proc = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=fe, env=env, stdout=log, stderr=subprocess.STDOUT,
            )
            code = await asyncio.wait_for(proc.wait(), timeout=180)
        logger.info("background dist build for %s exited %s", workspace_id, code)
        return code
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        logger.warning("background dist build for %s timed out", workspace_id)
        return -1
    except Exception:
        logger.debug("background dist build for %s failed to spawn", workspace_id, exc_info=True)
        return None
