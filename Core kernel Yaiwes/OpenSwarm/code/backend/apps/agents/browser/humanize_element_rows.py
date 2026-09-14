"""Rewrite the browser subsystem's internal element-index rows into plain prose.

BrowserListInteractives hands the sub-agent rows like `[3]<button "Post">` so it can
click things by number. That shape is machine input; a human reading a chat should
never see it. Ask a sub-agent to "report the list verbatim" and it will happily copy
those rows into its summary, which is the one string that crosses out of the browser
subsystem into a person's transcript, so the summary gets laundered here.
"""

import re
from typing import Dict, Match

from typeguard import typechecked

from backend.apps.agents.browser.browser_history import PAGE_STATE_MARKER

# Exact inverse of the row the renderer builds in frontend/src/shared/browserCommandHandler.ts:
# `[index]*<role "name" ctx="..." value="...">`. test_browser_index_leak.py pins that
# template so a change over there can't quietly outrun this pattern.
P_ROW_RE = re.compile(
    r'\[\d+\]\*?<\s*(?P<role>[A-Za-z][A-Za-z0-9_-]*)\s+"(?P<name>[^"]*)"'
    r'(?P<attrs>(?:\s+[a-z]+="[^"]*")*)\s*>'
)
P_ATTR_RE = re.compile(r'\s+(?P<key>[a-z]+)="(?P<val>[^"]*)"')
# The asterisk legend and the truncation footer only mean anything next to indices, and
# the footer names a tool the person reading it cannot call.
P_LEGEND_RE = re.compile(r' *\(\* = new since your last look;[^)]*\)')
P_TRUNCATION_RE = re.compile(r'(\d+ more not shown);[^.\n]*\.')
P_MARKER_RE = re.compile(re.escape(PAGE_STATE_MARKER) + r'\n?')

# ARIA role names a normal person would not recognize.
P_ROLE_LABELS: Dict[str, str] = {
    "combobox": "dropdown",
    "textbox": "text field",
    "searchbox": "search box",
    "listbox": "list",
    "menuitem": "menu item",
    "menuitemcheckbox": "menu checkbox",
    "menuitemradio": "menu option",
    "spinbutton": "number field",
    "treeitem": "tree item",
}


@typechecked
def p_render_row(match: Match[str]) -> str:
    role: str = match.group("role").lower()
    name: str = match.group("name").strip()
    attrs: Dict[str, str] = {
        m.group("key"): m.group("val").strip()
        for m in P_ATTR_RE.finditer(match.group("attrs") or "")
    }
    value: str = attrs.get("value", "")
    role_label: str = P_ROLE_LABELS.get(role, role)
    if name and value:
        return f'"{name}" ({role_label}, currently "{value}")'
    label: str = name or value
    if not label:
        return f"an unlabeled {role_label}"
    return f'"{label}" ({role_label})'


@typechecked
def humanize_element_rows(text: str) -> str:
    """Strip the click-by-index serialization out of browser-agent-authored prose."""
    out: str = P_ROW_RE.sub(p_render_row, text)
    out = P_LEGEND_RE.sub("", out)
    out = P_TRUNCATION_RE.sub(r"\1.", out)
    return P_MARKER_RE.sub("", out)
