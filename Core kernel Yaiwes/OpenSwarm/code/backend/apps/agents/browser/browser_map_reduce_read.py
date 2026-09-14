"""
Map-reduce READ tier: answer a multi-source public read (a comparison, a
difference, a combine-across-pages) without the big-model loop. When the
single-page fast_read declined because the answer lives across TWO OR MORE
pages, one aux call decomposes the request into independent single-page
lookups, they run CONCURRENTLY (each is a fast_read-class fetch + extract), and
one aux reduce combines them.

Fail-open everywhere: not multi-source, a thin or insufficient source, or a
reduce that can't answer all return None and the caller falls to the browser
leg, so a partial read can never become a wrong answer. Lives only in the
classifier's READ branch (public pages), so it never taxes an authed read.
"""

import asyncio
import json
import logging
import os
import re
import time

from backend.apps.agents.browser import browser_fast_read as fr

logger = logging.getLogger(__name__)

P_MAX_SOURCES = 4

P_DECOMPOSE_SYSTEM = (
    "Break the user's request into the MINIMUM set of independent factual "
    "lookups, each answerable from a SINGLE public web page. Return a JSON array "
    "of objects, each {\"q\": a self-contained question, \"url\": a starting URL "
    "(a direct page like https://en.wikipedia.org/wiki/NAME, or a search URL "
    "like https://www.google.com/search?q=...)}.\n"
    "Return 2 or more entries ONLY when the request genuinely needs different "
    "pages combined: a comparison, a difference, a sum, a 'both X and Y'. If a "
    "single page could answer it, return [].\n"
    "Never invent facts; only name the lookups. Output ONLY the JSON array."
)

P_REDUCE_SYSTEM = (
    "Answer the user's original request using ONLY the sub-answers provided, "
    "each gathered from its own page.\n"
    "First state each exact value. Then show the SINGLE arithmetic step the "
    "request needs (the subtraction, sum, or comparison). Then give the final "
    "answer. Your final number MUST equal the result of that step; never state a "
    "total or difference that disagrees with your own arithmetic.\n"
    "If the sub-answers do not together contain what the request needs, reply "
    "with exactly the single word INSUFFICIENT."
)


def enabled() -> bool:
    """Fail-open additive tier; default on, kill with OSW_MAP_REDUCE_READ=0."""
    return os.environ.get("OSW_MAP_REDUCE_READ", "1") != "0"


# The aux reduce got the VALUES right but flipped the arithmetic twice in ~10 live runs ("taller
# by 360.2m" beside its own 113.2 math; "1096-1636=-540, not older" beside "540 years older"), so
# for the two shapes that are pure arithmetic the number is computed HERE and the model never
# does subtraction. Anything unparseable falls open to the aux reduce.
P_DIFF_RE = re.compile(r"\b(difference|older|younger|taller|shorter|higher|lower|farther|further|longer|heavier|lighter|bigger|smaller|faster|slower)\b", re.I)
P_SUM_RE = re.compile(r"\b(combined|total|sum|together|altogether)\b", re.I)
P_VALUE_RE = re.compile(r"VALUE:\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%]*)", re.I)
P_VALUE_LINE = (
    "\nEnd with one extra line: VALUE: <the single number the request needs from this page, "
    "digits only with no thousands separators, followed by its unit if any (m, ft, km, %, ...)>."
)


P_QUANTITY_RE = re.compile(r"\b(how much|how many|difference|by how)\b", re.I)


def op_for(prompt: str) -> str:
    """'difference' | 'sum' | '' from the request's own wording; '' = aux reduce as before.
    Difference also requires a QUANTITY cue: a bare "which is taller?" wants a name, and a
    number-only computed headline would answer the wrong question (caught in audit, not live)."""
    low = prompt or ""
    if P_SUM_RE.search(low):
        return "sum"
    if P_DIFF_RE.search(low) and P_QUANTITY_RE.search(low):
        return "difference"
    return ""


def fmt_num(n: float) -> str:
    """Human numbers: 35,842,039 not 3.5842e+07; two decimals max on non-integers."""
    return f"{n:,.0f}" if float(n).is_integer() else f"{n:,.2f}"


def computed_answer(op: str, plan: list[tuple[str, str]], subs: list) -> str:
    """The deterministic answer when every sub-answer carries a parseable VALUE in agreeing
    units; '' means fall open to the aux reduce. States both values and the computed number,
    and deliberately asserts NO direction prose (that is exactly what the aux got wrong)."""
    vals: list[tuple[float, str]] = []
    for s in subs:
        m = P_VALUE_RE.search(s or "")
        if not m:
            return ""
        vals.append((float(m.group(1)), m.group(2).lower()))
    units = {u for _, u in vals}
    if len(units) > 1:
        return ""
    unit = f" {vals[0][1]}" if vals[0][1] else ""
    shown = "\n".join(f"- {q}: {fmt_num(v)}{unit}" for (q, _), (v, _) in zip(plan, vals))
    if op == "difference" and len(vals) == 2:
        n = abs(vals[0][0] - vals[1][0])
        return (f"**Answer: {fmt_num(n)}{unit}**\n\n{shown}\n"
                f"(computed: |{fmt_num(vals[0][0])} - {fmt_num(vals[1][0])}| = {fmt_num(n)})")
    if op == "sum":
        n = sum(v for v, _ in vals)
        return (f"**Answer: {fmt_num(n)}{unit}**\n\n{shown}\n"
                f"(computed: {' + '.join(fmt_num(v) for v, _ in vals)} = {fmt_num(n)})")
    return ""


def parse_plan(text: str) -> list[tuple[str, str]]:
    """(question, url) pairs from the decompose JSON; [] on anything unparseable
    or single-source. Bounded to P_MAX_SOURCES so a runaway plan can't fan out."""
    s = (text or "").strip()
    i, j = s.find("["), s.rfind("]")
    if i < 0 or j <= i:
        return []
    try:
        arr = json.loads(s[i:j + 1])
    except (json.JSONDecodeError, ValueError):
        return []
    out: list[tuple[str, str]] = []
    for it in arr if isinstance(arr, list) else []:
        if isinstance(it, dict):
            q, url = str(it.get("q") or "").strip(), str(it.get("url") or "").strip()
            if q and url.startswith(("http://", "https://")):
                out.append((q, url))
    return out[:P_MAX_SOURCES]


async def p_fetch_and_extract(client, aux_model: str, q: str, url: str, ask_value: bool) -> str | None:
    """One source: fetch the page, aux-extract the answer to q, or None if the
    page is thin or insufficient (so the whole map-reduce fails open, never
    fabricates a missing piece). ask_value appends the machine-parseable VALUE
    line the code-side arithmetic needs."""
    try:
        raw = await fr.fetch_raw(url)
        text = fr.strip_tags(raw)
        if fr.page_is_thin(text):
            text = await fr.fetch_page_text(url, q)
        if fr.page_is_thin(text):
            return None
        ans = await fr.ask_aux(
            client, aux_model, fr.ANSWER_SYSTEM + (P_VALUE_LINE if ask_value else ""),
            f"Request: {q}\n\nPage text from {url}:\n{text[:fr.MAX_PAGE_CHARS]}")
        if not ans or ans.upper().startswith("INSUFFICIENT"):
            return None
        return ans
    except Exception:
        return None


async def try_map_reduce_read(prompt: str, settings, primary_api: str | None) -> str | None:
    """Answer text for a multi-source public read, or None (caller falls to the
    browser leg). Any missing piece returns None, so it never half-answers."""
    if not enabled():
        return None
    t0 = time.monotonic()
    try:
        from backend.apps.settings.credentials import get_anthropic_client_for_model
        from backend.apps.agents.providers.registry import resolve_aux_model

        aux_model, _ = await resolve_aux_model(
            settings, preferred_tier="haiku", primary_api=primary_api)
        client = get_anthropic_client_for_model(settings, aux_model)

        plan_text = await fr.ask_aux(client, aux_model, P_DECOMPOSE_SYSTEM, f"Request: {prompt[:1200]}")
        plan = parse_plan(plan_text)
        if len(plan) < 2:
            return None
        logger.info(f"[browser-mapreduce] {len(plan)} sources: {[u for _, u in plan]}")

        p_op = op_for(prompt)
        subs = await asyncio.gather(*[p_fetch_and_extract(client, aux_model, q, u, bool(p_op)) for q, u in plan])
        if any(s is None for s in subs):
            logger.info(f"[browser-mapreduce] a source came back thin/insufficient in "
                        f"{int((time.monotonic() - t0) * 1000)}ms; browser fallback")
            return None

        if p_op:
            p_coded = computed_answer(p_op, plan, subs)
            if p_coded:
                logger.info(f"[browser-mapreduce] {p_op} computed in code from {len(plan)} sources "
                            f"in {int((time.monotonic() - t0) * 1000)}ms")
                return f"{p_coded}\n\n(Sources: {', '.join(u for _, u in plan)})"

        joined = "\n\n".join(f"Sub-question: {q}\nAnswer (from {u}): {s}"
                             for (q, u), s in zip(plan, subs))
        final = await fr.ask_aux(client, aux_model, P_REDUCE_SYSTEM,
                                 f"Original request: {prompt}\n\n{joined}")
        if not final or final.upper().startswith("INSUFFICIENT"):
            logger.info(f"[browser-mapreduce] reduce insufficient in "
                        f"{int((time.monotonic() - t0) * 1000)}ms; browser fallback")
            return None
        logger.info(f"[browser-mapreduce] answered from {len(plan)} sources in "
                    f"{int((time.monotonic() - t0) * 1000)}ms")
        return f"{final}\n\n(Sources: {', '.join(u for _, u in plan)})"
    except Exception as e:
        logger.info(f"[browser-mapreduce] skipped ({e}); browser fallback")
        return None
