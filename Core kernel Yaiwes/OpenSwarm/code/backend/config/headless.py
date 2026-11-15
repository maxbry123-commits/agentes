"""What the backend can still offer when nobody is sitting in front of it.

Two different absences, and they are not the same absence. `OPENSWARM_HEADLESS=1` says no
desktop shell owns this process, so no human will answer a prompt and no window arrives on
its own. A renderer that has never registered on the dashboard WebSocket says there is no
Electron window to drive a `<webview>` through. A cloud container starts as both and, once
it boots Electron under a virtual display, becomes only the first.

The browser tools therefore hang off the renderer actually being there, not off the flag,
which is what lets the same code be right on a laptop, in the runner container, and in
whatever environment attaches a renderer next.
"""

import os
from typing import Dict, FrozenSet, Set

from typeguard import typechecked

# Each of these ends at a live Electron renderer: browser and app delegation drive real <webview>s that only the frontend can serialize and click.
RENDERER_BOUND_TOOLS: FrozenSet[str] = frozenset({
    "CreateBrowserAgent",
    "BrowserAgent",
    "BrowserAgents",
    "AppAgent",
})

# Each of these ends at a person: ShowUI (the same gate AskUI rides) draws for someone to look at, and AskUserQuestion waits for someone to answer. A renderer nobody is watching does not bring them back.
HUMAN_BOUND_TOOLS: FrozenSet[str] = frozenset({
    "ShowUI",
    "AskUserQuestion",
})


@typechecked
def is_headless() -> bool:
    """True when the backend was started with OPENSWARM_HEADLESS=1. Read per call rather than
    frozen at import, so a launcher that sets it late still counts (and tests can flip it)."""
    return os.environ.get("OPENSWARM_HEADLESS") == "1"


@typechecked
def renderer_reachable() -> bool:
    """Whether an Electron renderer has ever registered on this backend's dashboard socket.

    Imported inside the call because config sits below apps in the import order; hoisting
    ws_manager to module scope would close a cycle."""
    from backend.apps.agents.core.ws_manager import ws_manager
    return ws_manager.renderer_ever_attached


@typechecked
def denied_tools() -> FrozenSet[str]:
    """Every builtin that would dead-end in this process, given who is actually attached.

    The renderer-bound set drops only when the shell that would have brought a window is
    absent AND no window ever showed up. A desktop launch keeps offering them across a
    socket blip on purpose: browser_agent's dispatch gate is what waits out a reconnect,
    and a tool pruned at session build never comes back for the life of that session.
    """
    denied: Set[str] = set()
    if is_headless():
        denied |= HUMAN_BOUND_TOOLS
        if not renderer_reachable():
            denied |= RENDERER_BOUND_TOOLS
    return frozenset(denied)


@typechecked
def apply_unreachable_denies(builtin_perms: Dict[str, str]) -> Dict[str, str]:
    """The permission map with every currently-unreachable tool forced to 'deny'. Returns a
    copy so the verdict never poisons the live snapshot."""
    denied = denied_tools()
    if not denied:
        return builtin_perms
    return {**builtin_perms, **{name: "deny" for name in denied}}
