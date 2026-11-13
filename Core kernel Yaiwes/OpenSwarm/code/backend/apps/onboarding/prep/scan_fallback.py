"""The no-LLM reveal: starters grounded in the real local scan when the aux call can't run."""

from typing import List

from typeguard import typechecked

from backend.apps.onboarding.models import PrepRequest, PrepResponse, ScanResult
from backend.apps.settings.models import PersonalizedStarter

FALLBACK_STARTERS: List[PersonalizedStarter] = [
    PersonalizedStarter(title="Clean up Downloads", prompt="Sort my Downloads folder into tidy subfolders. Show me the plan before moving anything."),
    PersonalizedStarter(title="Research something", prompt="Research the best noise-cancelling headphones under $300 and give me a comparison table."),
    PersonalizedStarter(title="Build a tiny app", prompt="Build me a simple habit tracker app I can use right now."),
    PersonalizedStarter(title="Plan a trip", prompt="Plan a 3-day weekend trip itinerary and turn it into a printable page."),
]


@typechecked
def p_scan_grounded_starters(scan: ScanResult) -> List[PersonalizedStarter]:
    """Build starters from the REAL scan (no LLM): each references something concrete on this machine, a
    screenshot pile, a content-heavy folder, the app they lean on, their code projects. Every one produces
    a keepable artifact and never modifies an existing file, so even the no-LLM path is genuinely tailored."""
    out: List[PersonalizedStarter] = []
    apps = scan.signal_apps[:3]
    # Screenshots -> a browsable gallery page (real deliverable from their real files).
    shots = next((f for f in scan.folders if f.screenshot_count > 2), None)
    if shots:
        out.append(PersonalizedStarter(
            title="Frame my screenshots",
            prompt=f"Find the screenshot images in my {shots.name} folder and build one browsable gallery web page showing them as a neat scrollable grid. Write only the new page; never move or delete the originals.",
            reason=f"{shots.screenshot_count} screenshots sitting in {shots.name}.",
        ))
    # A content-heavy folder -> a searchable index page of what's in it.
    docs = next((f for f in scan.folders if f.name in ("Documents", "Downloads", "Desktop") and f.entry_count > 5 and f.top_extensions), None)
    if docs:
        ext = docs.top_extensions[0].lstrip(".") or "file"
        out.append(PersonalizedStarter(
            title=f"Index my {ext} files",
            prompt=f"Look through my {docs.name} folder and build one searchable index page listing my {ext} files with their names and dates so I can find things fast. Write only the new page; do not move or delete anything.",
            reason=f"{docs.entry_count} files in {docs.name}, lots of .{ext}.",
        ))
    # Top signal app -> live web research for current tips (a real answer, not a plan).
    if apps:
        out.append(PersonalizedStarter(
            title=f"{apps[0]} tips",
            prompt=f"Search the web right now for the most useful current tips, shortcuts, and workflows for {apps[0]}, and give me a tight summary with dated sources.",
            reason=f"You lean on {apps[0]} a lot.",
        ))
    # Code projects -> a plain-English recap of where each stands.
    if scan.git_repo_count > 0:
        out.append(PersonalizedStarter(
            title="Recap my projects",
            prompt="Look at the code projects on my computer, read each one's README and recent activity, and write me one short page summarizing what each project is and where it stands. Write only the summary; change nothing.",
            reason=f"{scan.git_repo_count} code projects on your machine.",
        ))
    return out


@typechecked
def scan_grounded_fallback(request: PrepRequest) -> PrepResponse:
    """When the aux call can't be made (a sole gemini/codex lane returns empty on 0.3.60, provider
    down, no anthropic-reachable model), still ground the reveal in the REAL scan via a template so a
    cross-provider user gets their-Mac-specific starters, not generic stubs. No LLM, so it never fails."""
    scan = request.scan
    if scan is None:
        return PrepResponse(greeting="", starters=list(FALLBACK_STARTERS))
    apps = scan.signal_apps[:3]
    starters = p_scan_grounded_starters(scan)
    # Backfill from the generic list ONLY to reach four, and only when the machine was too sparse to
    # ground three real ones. On a normal Mac all four come from the scan, so 3-of-4 stays tailored.
    for s in FALLBACK_STARTERS:
        if len(starters) >= 4:
            break
        if all(s.title != existing.title for existing in starters):
            starters.append(s)
    downloads = next((f for f in scan.folders if f.name == "Downloads" and f.entry_count > 0), None)
    bits: List[str] = []
    if downloads:
        bits.append(f"{downloads.entry_count} files in Downloads")
    if apps:
        bits.append(", ".join(apps))
    greeting = f"I took a look around your Mac: {'; '.join(bits)}. Here is where I would start." if bits else ""
    # Ground the research card on their top tool so the "looked into this" card still appears cross-provider.
    research_title = ""
    research_prompt = ""
    research_reason = ""
    if apps:
        research_title = f"{apps[0]} Tips"
        research_prompt = f"Search the web right now for the most useful current tips, shortcuts, and workflows for {apps[0]}, and give me a tight summary with sources."
        research_reason = f"You have {apps[0]} installed and use it a lot."
    return PrepResponse(
        greeting=greeting,
        starters=starters[:4],
        research_title=research_title,
        research_prompt=research_prompt,
        research_reason=research_reason,
    )
