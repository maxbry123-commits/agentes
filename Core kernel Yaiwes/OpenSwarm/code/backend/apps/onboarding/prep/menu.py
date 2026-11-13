"""Build the hero's two-level menu: 4 general categories x 4 starters tailored to this user.

Runs as its own cheap aux call BESIDE the main prep call, so a failure here can never cost
the reveal, and every failure path fills from scan-grounded + static rows, so the menu the
dashboard hero drills into is always complete.
"""

import json
from typing import List, Optional

from typeguard import typechecked

from backend.apps.agents.core.aux_llm import aux_max_tokens_for, safe_resp_text
from backend.apps.onboarding.models import ScanResult
from backend.apps.onboarding.prep.parse_helpers import build_starters, load_json_object, normalize_json_text
from backend.apps.settings.models import AppSettings, PersonalizedMenu, PersonalizedStarter

MENU_CATEGORIES = ("computer", "research", "web", "build")
MENU_SIZE = 4

P_MENU_SYSTEM = (
    "You write starter tasks for OpenSwarm, a desktop AI agent platform that can organize local files, "
    "browse the web in a real browser, build small apps, and run agents in parallel. Given facts about the "
    "user (their machine scan, picked apps, and usage_summary, a profile distilled from their real AI "
    "conversations, the STRONGEST signal), respond with STRICT JSON only: "
    '{"computer": [{"title": string, "prompt": string}], "research": [{"title": string, "prompt": string}], '
    '"web": [{"title": string, "prompt": string}], "build": [{"title": string, "prompt": string}]}. '
    "EXACTLY 4 items per category, 16 total, every one tailored to THIS person. "
    "computer: tasks on THIS machine's real files and folders (use their actual folder names and file kinds "
    "from the scan); each READS real files and writes ONE new artifact, and must NEVER modify or delete an "
    "existing file. "
    "research: live web research on topics THIS user actually cares about (from usage_summary); each demands "
    "current information with dated sources and produces an actual answer or comparison, never a plan. "
    "web: the agent OPENS a named real public website and does a genuinely multi-step task there (navigate, "
    "search, click through, compare, report); read-only public browsing, never log in, buy, post, or act on "
    "the user's behalf. "
    "build: small working tools for this person's real needs; each prompt starts with 'Build me', is fully "
    "client-side and self-contained with deterministic logic only (math, parsing, formatting, charts), and "
    "must NEVER call an AI model or any network API. "
    "Span the person's DISTINCT life threads: within each category at most ONE item may touch their work or "
    "company; the rest come from their other real threads (sport, food, hobbies, curiosities, practical "
    "needs) actually present in the input. "
    "Titles are 2-5 plain words saying what the task does, never clever or punny. Prompts are concrete, "
    "immediately runnable instructions; never invent facts not in the input. "
    "Never use em-dashes or en-dashes. No markdown, no commentary, JSON only."
)

P_STATIC_MENU: dict[str, List[PersonalizedStarter]] = {
    "computer": [
        PersonalizedStarter(title="Clean up Downloads", prompt="Sort my Downloads folder into tidy subfolders. Show me the plan before moving anything."),
        PersonalizedStarter(title="Find my biggest files", prompt="Scan my home folder for the largest files and folders and write me a reviewable page listing them with sizes. Do not delete anything."),
        PersonalizedStarter(title="Index my documents", prompt="Look through my Documents folder and build one searchable index page listing files by name and date so I can find things fast. Write only the new page."),
        PersonalizedStarter(title="Find duplicate files", prompt="Look for duplicate files across my Downloads and Desktop and write a report listing them side by side. Never delete anything without my review."),
    ],
    "research": [
        PersonalizedStarter(title="Compare before I buy", prompt="Ask me what I'm shopping for, then research current options and give me a tight comparison table with dated sources."),
        PersonalizedStarter(title="What's new in AI", prompt="Search the web for the most useful AI tools and model releases from the past month and summarize the ones worth my time, with dated sources."),
        PersonalizedStarter(title="Settle a question", prompt="Ask me one question I've been meaning to look into, then research it properly and give me a current, sourced answer."),
        PersonalizedStarter(title="Plan a weekend trip", prompt="Ask me where I'd like to go, then research a realistic 3-day itinerary with current prices and opening hours, and turn it into a printable page."),
    ],
    "web": [
        PersonalizedStarter(title="Find a table tonight", prompt="Open OpenTable and find three well-reviewed restaurants near me with availability tonight, compare them, and report back."),
        PersonalizedStarter(title="Watch a flight price", prompt="Ask me for a route, then open Google Flights, search it, compare dates and airlines across a few pages, and report the best current options."),
        PersonalizedStarter(title="Best rated near me", prompt="Open Google Maps, search for the best-rated coffee shops nearby, read through reviews on a few of them, and tell me which one to try and why."),
        PersonalizedStarter(title="Catch me up on tech", prompt="Open Hacker News, read through today's top discussions, and give me the three most interesting threads with what people are actually saying."),
    ],
    "build": [
        PersonalizedStarter(title="Habit tracker", prompt="Build me a simple habit tracker app I can use right now."),
        PersonalizedStarter(title="Bill splitter", prompt="Build me a tool where I enter a bill total, tip, and the people involved, and it computes exactly who owes what."),
        PersonalizedStarter(title="CSV instant charts", prompt="Build me a tool where I paste CSV data and it instantly renders clean charts I can screenshot."),
        PersonalizedStarter(title="Countdown to a date", prompt="Build me a countdown page for a date that matters to me; ask me the date and label, then make it look great."),
    ],
}


@typechecked
def p_scan_grounded_rows(category: str, scan: Optional[ScanResult]) -> List[PersonalizedStarter]:
    """No-LLM personalization: ground a couple of rows per category in the real scan."""
    if scan is None:
        return []
    out: List[PersonalizedStarter] = []
    if category == "computer":
        shots = next((f for f in scan.folders if f.screenshot_count > 2), None)
        if shots:
            out.append(PersonalizedStarter(
                title="Frame my screenshots",
                prompt=f"Find the screenshot images in my {shots.name} folder and build one browsable gallery web page showing them as a neat scrollable grid. Write only the new page; never move or delete the originals.",
            ))
        if scan.git_repo_count > 0:
            out.append(PersonalizedStarter(
                title="Recap my projects",
                prompt="Look at the code projects on my computer, read each one's README and recent activity, and write me one short page summarizing what each project is and where it stands. Write only the summary; change nothing.",
            ))
    if category == "research" and scan.signal_apps:
        out.append(PersonalizedStarter(
            title=f"{scan.signal_apps[0]} tips",
            prompt=f"Search the web right now for the most useful current tips, shortcuts, and workflows for {scan.signal_apps[0]}, and give me a tight summary with dated sources.",
        ))
    return out


@typechecked
def fill_menu(parsed: Optional[PersonalizedMenu], scan: Optional[ScanResult]) -> PersonalizedMenu:
    """Guarantee 4 rows per category: LLM rows first, then scan-grounded, then static."""
    menu = PersonalizedMenu()
    for category in MENU_CATEGORIES:
        rows: List[PersonalizedStarter] = list(getattr(parsed, category)) if parsed is not None else []
        for extra in [*p_scan_grounded_rows(category, scan), *P_STATIC_MENU[category]]:
            if len(rows) >= MENU_SIZE:
                break
            if all(extra.title != existing.title for existing in rows):
                rows.append(extra)
        setattr(menu, category, rows[:MENU_SIZE])
    return menu


@typechecked
def parse_menu(text: str) -> Optional[PersonalizedMenu]:
    data = load_json_object(normalize_json_text(text))
    if not data:
        return None
    menu = PersonalizedMenu()
    got_any = False
    for category in MENU_CATEGORIES:
        rows = data.get(category)
        starters = build_starters(rows) if isinstance(rows, list) else []
        if starters:
            got_any = True
        setattr(menu, category, starters[:MENU_SIZE])
    return menu if got_any else None


@typechecked
async def build_menu(settings: AppSettings, facts: dict, scan: Optional[ScanResult]) -> PersonalizedMenu:
    """One cheap aux call -> 16 tailored starters; any failure fills from scan + static rows."""
    parsed: Optional[PersonalizedMenu] = None
    try:
        from backend.apps.agents.providers.registry import resolve_aux_model
        from backend.apps.settings.credentials import get_anthropic_client_for_model

        aux_model, _ = await resolve_aux_model(settings, preferred_tier="haiku")
        client = get_anthropic_client_for_model(settings, aux_model)
        resp = await client.messages.create(
            model=aux_model,
            max_tokens=aux_max_tokens_for(aux_model, base=1800),
            system=P_MENU_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(facts)}],
            timeout=45.0,
        )
        parsed = parse_menu(safe_resp_text(resp))
    except Exception:
        parsed = None
    return fill_menu(parsed, scan)
