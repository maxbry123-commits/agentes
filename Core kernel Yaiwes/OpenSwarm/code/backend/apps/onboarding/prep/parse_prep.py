"""Parse the prep aux response into a PrepResponse, salvaging what it can from malformed JSON."""

import re
from typing import List, Optional

from typeguard import typechecked

from backend.apps.onboarding.models import PrepResponse
from backend.apps.onboarding.prep.parse_helpers import build_starters, load_json_object, normalize_json_text, salvage_flat_objects, strip_dashes
from backend.apps.settings.models import PersonalizedAutomation

VALID_CADENCE = {"daily", "weekday", "weekly"}


@typechecked
def p_extract_string_field(text: str, name: str) -> str:
    """Pull a top-level "name": "value" string straight out of the raw blob, for the fields that
    aren't objects (greeting, app_*) so they survive when the strict JSON load failed and we salvage."""
    m = re.search(rf'"{name}"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    return m.group(1).strip() if m else ""


@typechecked
def p_build_automations(rows: List[dict]) -> List[PersonalizedAutomation]:
    return [
        PersonalizedAutomation(
            title=strip_dashes(str(a.get("title", ""))),
            prompt=strip_dashes(str(a.get("prompt", ""))),
            cadence=(str(a.get("cadence", "weekly")).strip().lower() if str(a.get("cadence", "")).strip().lower() in VALID_CADENCE else "weekly"),
        )
        for a in rows
        if isinstance(a, dict) and str(a.get("title", "")).strip() and str(a.get("prompt", "")).strip()
    ]


@typechecked
def parse_prep(text: str) -> Optional[PrepResponse]:
    text = normalize_json_text(text)
    data = load_json_object(text)
    starters = build_starters(data.get("starters") if isinstance(data.get("starters"), list) else [])
    automations = p_build_automations(data.get("automations") if isinstance(data.get("automations"), list) else [])
    headline = str(data.get("headline", "")).strip()
    epithets = [strip_dashes(str(x)).strip() for x in (data.get("epithets") or []) if str(x).strip()][:3]
    greeting = str(data.get("greeting", "")).strip()
    app_title = str(data.get("app_title", "")).strip()
    app_prompt = str(data.get("app_prompt", "")).strip()
    app_reason = str(data.get("app_reason", "")).strip()
    research_title = str(data.get("research_title", "")).strip()
    research_prompt = str(data.get("research_prompt", "")).strip()
    research_reason = str(data.get("research_reason", "")).strip()
    browser_title = str(data.get("browser_title", "")).strip()
    browser_prompt = str(data.get("browser_prompt", "")).strip()
    browser_reason = str(data.get("browser_reason", "")).strip()

    # Truncation / trailing comma / smart quotes broke the strict load: salvage the complete pieces
    # rather than throwing the whole personalized reveal away for one bad character.
    if not starters or not automations:
        objs = salvage_flat_objects(text)
        if not starters:
            starters = build_starters([o for o in objs if "cadence" not in o])
        if not automations:
            automations = p_build_automations([o for o in objs if "cadence" in o])
    # Top-level string fields don't live in the flat objects above, so recover them by name when the
    # strict load dropped them (a malformed response was still yielding starters but a blank app).
    if not headline:
        headline = p_extract_string_field(text, "headline")
    if not greeting:
        greeting = p_extract_string_field(text, "greeting")
    if not app_title:
        app_title = p_extract_string_field(text, "app_title")
    if not app_prompt:
        app_prompt = p_extract_string_field(text, "app_prompt")
    if not app_reason:
        app_reason = p_extract_string_field(text, "app_reason")
    if not research_title:
        research_title = p_extract_string_field(text, "research_title")
    if not research_prompt:
        research_prompt = p_extract_string_field(text, "research_prompt")
    if not research_reason:
        research_reason = p_extract_string_field(text, "research_reason")
    if not browser_title:
        browser_title = p_extract_string_field(text, "browser_title")
    if not browser_prompt:
        browser_prompt = p_extract_string_field(text, "browser_prompt")
    if not browser_reason:
        browser_reason = p_extract_string_field(text, "browser_reason")

    if not starters:
        return None
    return PrepResponse(
        headline=strip_dashes(headline),
        epithets=epithets,
        greeting=strip_dashes(greeting),
        starters=starters[:4],
        app_title=strip_dashes(app_title),
        app_prompt=strip_dashes(app_prompt),
        app_reason=strip_dashes(app_reason),
        research_title=strip_dashes(research_title),
        research_prompt=strip_dashes(research_prompt),
        research_reason=strip_dashes(research_reason),
        browser_title=strip_dashes(browser_title),
        browser_prompt=strip_dashes(browser_prompt),
        browser_reason=strip_dashes(browser_reason),
        automations=automations[:3],
    )
