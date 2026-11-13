"""Turn the local scan + app picks into a personalized greeting and starters.

One cheap aux call on whatever lane the user just connected; every failure path
returns the static fallback so the reveal can never be an error card.
"""

import asyncio
import json

from typeguard import typechecked

from backend.apps.agents.core.aux_llm import aux_max_tokens_for, safe_resp_text
from backend.apps.onboarding.models import PrepRequest, PrepResponse
from backend.apps.onboarding.prep.menu import build_menu
from backend.apps.onboarding.prep.parse_helpers import strip_dashes
from backend.apps.onboarding.prep.parse_prep import parse_prep
from backend.apps.onboarding.prep.prompts import PROFILE_SYSTEM, PREP_SYSTEM
from backend.apps.onboarding.prep.scan_fallback import scan_grounded_fallback
from backend.apps.settings.models import AppSettings

# Below this the usage text is just titles/memories (thin); above it there is real conversation content
# worth a distill pass. Keep the distill input bounded so the cheap call stays a couple cents.
P_PROFILE_DISTILL_THRESHOLD = 1500
P_PROFILE_INPUT_CAP = 140000


@typechecked
async def p_distill_profile(settings: AppSettings, usage_text: str) -> str:
    """One cheap aux call: raw chat content -> a tight 'who is this person' profile. "" on any failure,
    so build_prep just falls back to feeding the raw usage text (today's behavior)."""
    try:
        from backend.apps.agents.providers.registry import resolve_aux_model
        from backend.apps.settings.credentials import get_anthropic_client_for_model

        aux_model, _ = await resolve_aux_model(settings, preferred_tier="haiku")
        client = get_anthropic_client_for_model(settings, aux_model)
        resp = await client.messages.create(
            model=aux_model,
            max_tokens=aux_max_tokens_for(aux_model, base=600),
            system=PROFILE_SYSTEM,
            messages=[{"role": "user", "content": usage_text[:P_PROFILE_INPUT_CAP]}],
            timeout=45.0,
        )
        return strip_dashes(safe_resp_text(resp).strip())
    except Exception:
        return ""


@typechecked
async def build_prep(settings: AppSettings, request: PrepRequest) -> PrepResponse:
    from datetime import date

    facts = request.model_dump()
    # The aux otherwise assumes its training-cutoff year and writes stale ranges like "2024-2025"
    # into research prompts; telling it today's date keeps "current" meaning current.
    facts["today"] = date.today().isoformat()
    # If the usage text carries real conversation content, distill it to a tight profile FIRST so the
    # reveal call reasons over who this person is, not raw logs (and stays in budget). Fail-open: a blank
    # profile just leaves the raw text in place, which is today's behavior.
    usage = str(facts.get("usage_summary", ""))
    if len(usage) > P_PROFILE_DISTILL_THRESHOLD:
        profile = await p_distill_profile(settings, usage)
        if profile:
            facts["usage_summary"] = profile
    # The hero's 4x4 drill-in menu rides its own parallel aux call; build_menu never raises.
    menu_task = asyncio.create_task(build_menu(settings, facts, request.scan))
    try:
        from backend.apps.agents.providers.registry import resolve_aux_model
        from backend.apps.settings.credentials import get_anthropic_client_for_model

        aux_model, _ = await resolve_aux_model(settings, preferred_tier="haiku")
        client = get_anthropic_client_for_model(settings, aux_model)
        resp = await client.messages.create(
            model=aux_model,
            # The full shape (greeting + 4 starters w/ prompts + app + 3 automations) runs ~1.5-2K
            # tokens for a rich user; 1100 truncated the JSON mid-object so parse silently fell back.
            max_tokens=aux_max_tokens_for(aux_model, base=2200),
            system=PREP_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(facts)}],
            # Bound the wait: the SDK default is ~10min, so a wedged router/provider would hang the
            # auto-launch (which awaits this) instead of degrading to the static starters.
            timeout=45.0,
        )
        parsed = parse_prep(safe_resp_text(resp))
        if parsed is not None:
            parsed.menu = await menu_task
            parsed.used_llm = True
            return parsed
    except Exception:
        pass
    # Aux unusable (empty gemini/codex response on 0.3.60, provider down, no anthropic lane): still
    # ground the reveal in the real scan rather than shipping generic stubs.
    fallback = scan_grounded_fallback(request)
    fallback.menu = await menu_task
    return fallback
