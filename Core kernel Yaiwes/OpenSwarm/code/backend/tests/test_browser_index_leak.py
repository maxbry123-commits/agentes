"""The browser subsystem's click-by-index rows must never reach a human.

`[1]<combobox "" value="-- pick --">` is what BrowserListInteractives hands the
browser sub-agent so it can click by number. A user asked a normal agent to list a
page's interactive elements and got those rows back verbatim in chat. The rows are
produced in the renderer (frontend/src/shared/browserCommandHandler.ts) and ride into
the transcript on the sub-agent's summary, so both the laundering and the renderer's
template are pinned here.
"""

import asyncio
import re
from pathlib import Path

from backend.apps.agents.browser import browser_agent as BA
from backend.apps.agents.browser.browser_history import PAGE_STATE_MARKER
from backend.apps.agents.browser.humanize_element_rows import humanize_element_rows

# Verbatim from the bug report: six rows the agent pasted into a normal chat, on one line.
LEAKED_REPLY = (
    '[1]<combobox "" value="-- pick --"> [2]<button "Choose File"> '
    '[3]<button "Shadow Button"> [4]<textbox "title"> [5]<button "Post"> '
    '[6]<button "Frame Button">'
)

INDEX_ROW_RE = re.compile(r'\[\d+\]\*?<')


def test_leaked_reply_loses_every_index_and_keeps_every_label():
    out = humanize_element_rows(LEAKED_REPLY)
    assert not INDEX_ROW_RE.search(out), out
    assert "<" not in out and ">" not in out, out
    for label in ("-- pick --", "Choose File", "Shadow Button", "title", "Post", "Frame Button"):
        assert label in out, f"{label} was dropped: {out}"
    assert "dropdown" in out and "text field" in out and "button" in out


def test_multiline_listing_header_legend_and_footer_are_cleaned():
    listing = (
        "3 interactive elements (* = new since your last look; same number = same "
        "element as before):\n"
        '[1]<button "Like">\n'
        '[2]*<textbox "Search" value="cats">\n'
        '[3]<button "Message" ctx="Alice Smith">\n'
        "... 25 more not shown; scroll or scope with BrowserGetElements to reach them."
    )
    out = humanize_element_rows(listing)
    assert not INDEX_ROW_RE.search(out), out
    assert "same number = same element as before" not in out
    assert "BrowserGetElements" not in out
    assert "25 more not shown." in out
    assert out.startswith("3 interactive elements:")
    assert '"Like" (button)' in out
    assert '"Search" (text field, currently "cats")' in out


def test_unlabeled_element_and_page_state_marker():
    out = humanize_element_rows(f'{PAGE_STATE_MARKER}\n[7]<checkbox "">')
    assert PAGE_STATE_MARKER not in out
    assert out.strip() == "an unlabeled checkbox"


def test_ordinary_prose_is_untouched():
    prose = "I posted the reply as Alice at 10:43 PM. The list [1] had 3 items <b>ok</b>."
    assert humanize_element_rows(prose) == prose


def test_run_browser_agents_launders_summary_and_error(monkeypatch):
    """The one funnel both delivery paths use: the MCP tool result the parent agent
    reads, and the fast path that pipes the summary straight into the user's chat."""
    async def p_fake_run_browser_agent(**kwargs):
        return {"summary": LEAKED_REPLY, "error": LEAKED_REPLY,
                "action_log": [], "final_screenshot": None}

    monkeypatch.setattr(BA, "run_browser_agent", p_fake_run_browser_agent, raising=True)
    monkeypatch.setattr(BA.ws_manager, "global_connections", [object()], raising=False)

    results = asyncio.run(BA.run_browser_agents(
        tasks=[{"task": "list the interactive elements", "browser_id": "b1"}],
        model="sonnet",
    ))

    assert not INDEX_ROW_RE.search(results[0]["summary"]), results[0]["summary"]
    assert not INDEX_ROW_RE.search(results[0]["error"]), results[0]["error"]
    assert "Choose File" in results[0]["summary"]


def test_renderer_row_template_still_matches_the_scrubber():
    """Drift pin: the rows are built in TypeScript, so a Python-only change set can
    silently stop matching. If this line moved, re-check humanize_element_rows."""
    handler = Path(__file__).resolve().parents[2] / "frontend/src/shared/browserCommandHandler.ts"
    source = handler.read_text(encoding="utf-8")
    assert 'return `[${el.index}]${el.isNew ? \'*\' : \'\'}<${el.role} "${el.name}"${ctx}${val}>`;' in source
    assert "const ctx = dup && el.context ? ` ctx=\"${el.context}\"` : '';" in source
    assert "const val = el.value ? ` value=\"${el.value}\"` : '';" in source
