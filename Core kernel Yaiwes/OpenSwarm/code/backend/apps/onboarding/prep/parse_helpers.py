"""Shared JSON/text salvage helpers for the onboarding aux-call parsers (prep + menu)."""

import json
import re
from typing import Dict, List

from typeguard import typechecked

from backend.apps.settings.models import PersonalizedStarter

P_CURLY_QUOTES: Dict[str, str] = {"“": '"', "”": '"', "‘": "'", "’": "'"}


@typechecked
def normalize_json_text(text: str) -> str:
    for bad, good in P_CURLY_QUOTES.items():
        text = text.replace(bad, good)
    return text


@typechecked
def strip_trailing_commas(s: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", s)


@typechecked
def strip_dashes(s: str) -> str:
    """The house style bans em/en dashes and the model slips them into the greeting anyway, so
    guarantee it in code: turn a dash-clause into a comma-clause, then tidy any doubled punctuation."""
    s = s.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", ", ")
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r",\s*,", ", ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


@typechecked
def load_json_object(text: str) -> dict:
    """Best-effort load of the outermost JSON object: strict first, then a
    trailing-comma repair. Returns {} if neither parses (salvage handles the rest)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    for candidate in (match.group(0), strip_trailing_commas(match.group(0))):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return {}


@typechecked
def salvage_flat_objects(text: str) -> List[dict]:
    """Pull every complete flat {..} object out of a truncated/malformed blob so a
    cut-off response still yields the starters it did finish (partial > generic)."""
    out: List[dict] = []
    for m in re.finditer(r"\{[^{}]*\}", text):
        try:
            obj = json.loads(strip_trailing_commas(m.group(0)))
        except Exception:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


@typechecked
def build_starters(rows: List[dict]) -> List[PersonalizedStarter]:
    return [
        PersonalizedStarter(title=strip_dashes(str(s.get("title", ""))), prompt=strip_dashes(str(s.get("prompt", ""))), reason=strip_dashes(str(s.get("reason", ""))))
        for s in rows
        if isinstance(s, dict) and str(s.get("title", "")).strip() and str(s.get("prompt", "")).strip() and "cadence" not in s
    ]
