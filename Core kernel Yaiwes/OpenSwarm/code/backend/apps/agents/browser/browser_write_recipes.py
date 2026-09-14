"""Learn-on-first-write, replay-on-repeat: the repeated-write half of the API-first tier.

The first write on a site is unavoidably a DOM drive (a route can only be captured after the
site's own UI fires it, proven live in the V.8 X soak). But the moment a DOM write SUCCEEDS with
a verified receipt, the mutating route the page fired is a complete recipe: method + URL (with
its live queryId) + body, with the user's payload sitting in one JSON leaf. This module persists
that recipe with the payload slot replaced by a sentinel, and replays it with a NEW payload on
the next write to the same site, skipping the DOM entirely.

SAFETY (documented in SECURITY.md):
- A recipe is learned ONLY from a receipt-verified successful write the user's own task performed,
  so its provenance satisfies the captured-route wall (the site's UI genuinely fired it); replay
  seeds route_write's captured set from the recipe itself.
- Secret-shaped string leaves in the stored body are redacted at learn time (payload slot
  excepted); cookies/headers are never stored (route_write borrows them live per call).
- Same-origin + OSW_ROUTE_WRITE flag + typed fail-open outcomes all still apply at replay.
- Staleness self-heals: a recipe that misses MAX_MISSES times is dropped, and the next
  successful DOM write learns a fresh one (queryId rotation just re-learns).
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

logger = logging.getLogger(__name__)

SENTINEL = "__OSW_PAYLOAD__"
P_MIN_PAYLOAD_CHARS = 4
P_MAX_BODY_CHARS = 32768
MAX_MISSES = 3
P_MAX_RECIPES_ON_DISK = 200

# Same secret heuristics as the electron capture (cdp-routes.js), ported so a token-shaped
# body value can never be persisted; over-redacting is the safe direction.
P_TOKEN_PREFIX = re.compile(r"^(sk-|ghp_|gho_|pk_|xox[bap]-|AIza|eyJ|Bearer )")


@typechecked
def looks_secret_value(v: str) -> bool:
    if not v:
        return False
    if P_TOKEN_PREFIX.match(v):
        return True
    return len(v) >= 20 and bool(re.search(r"[A-Za-z]", v)) and bool(re.search(r"[0-9]", v)) and not re.search(r"\s", v)


class WriteRecipe(BaseModel):
    """One site's proven write call, payload slot replaced by the sentinel."""

    model_config = ConfigDict(validate_assignment=True)

    host: str
    method: str
    url_template: str
    url: str
    body_template: str
    payload_path: str
    learned_at: float
    wins: int = 0
    misses: int = 0


@typechecked
def p_dir() -> str:
    from backend.config.paths import DATA_ROOT
    d = os.path.join(DATA_ROOT, "browser_write_recipes")
    os.makedirs(d, mode=0o700, exist_ok=True)
    return d


@typechecked
def p_path(host: str) -> str:
    safe = re.sub(r"[^a-z0-9.-]", "_", host.lower())
    return os.path.join(p_dir(), f"{safe}.json")


@typechecked
def recipe_for(host: str) -> Optional[WriteRecipe]:
    """The persisted recipe for this host, or None. Corrupt files read as None (fail-open)."""
    try:
        with open(p_path(host)) as f:
            return WriteRecipe(**json.load(f))
    except Exception:
        return None


@typechecked
def save_recipe(recipe: WriteRecipe) -> None:
    """Atomic write, browser_skills pattern; cap the directory so it can't grow unbounded."""
    try:
        d = p_dir()
        entries = sorted(os.listdir(d), key=lambda f: os.path.getmtime(os.path.join(d, f)))
        while len(entries) >= P_MAX_RECIPES_ON_DISK:
            os.remove(os.path.join(d, entries.pop(0)))
        tmp = p_path(recipe.host) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(recipe.model_dump(mode="json"), f)
        os.replace(tmp, p_path(recipe.host))
    except Exception as e:
        logger.info(f"[write-recipe] save failed for {recipe.host}: {e}")


@typechecked
def drop_recipe(host: str) -> None:
    try:
        os.remove(p_path(host))
    except OSError:
        pass


@typechecked
def p_find_payload_leaf(obj: Any, payload: str, path: str = "$") -> Optional[str]:
    """JSON path of the leaf whose string value EQUALS the payload (exact, not substring:
    a substring hit means the site wrapped it and blind substitution would corrupt)."""
    if isinstance(obj, str):
        return path if obj == payload else None
    if isinstance(obj, dict):
        for k, v in obj.items():
            hit = p_find_payload_leaf(v, payload, f"{path}.{k}")
            if hit:
                return hit
        return None
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            hit = p_find_payload_leaf(v, payload, f"{path}[{i}]")
            if hit:
                return hit
    return None


@typechecked
def p_transform_leaves(obj: Any, payload: str) -> Any:
    """Copy with the payload leaf swapped for the sentinel and secret-shaped strings redacted."""
    if isinstance(obj, str):
        if obj == payload:
            return SENTINEL
        return "<redacted>" if looks_secret_value(obj) else obj
    if isinstance(obj, dict):
        return {k: p_transform_leaves(v, payload) for k, v in obj.items()}
    if isinstance(obj, list):
        return [p_transform_leaves(v, payload) for v in obj]
    return obj


@typechecked
def learn_recipe(host: str, payload: str, routes: List[Dict[str, Any]]) -> Optional[WriteRecipe]:
    """Distill a recipe from the captured mutating routes of a JUST-verified write. Returns the
    saved recipe, or None when no route's body carries the payload as an exact string leaf
    (then there is nothing provably replayable, so nothing is stored)."""
    if len(payload or "") < P_MIN_PAYLOAD_CHARS:
        return None
    for r in routes:
        body = str(r.get("lastBody") or "")
        method = str(r.get("method") or "").upper()
        if not body or len(body) > P_MAX_BODY_CHARS or method in ("GET", "HEAD"):
            continue
        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            continue
        slot = p_find_payload_leaf(parsed, payload)
        if not slot:
            continue
        recipe = WriteRecipe(
            host=host, method=method,
            url_template=str(r.get("template") or ""),
            url=str(r.get("example") or r.get("template") or ""),
            body_template=json.dumps(p_transform_leaves(parsed, payload)),
            payload_path=slot, learned_at=time.time(),
        )
        save_recipe(recipe)
        logger.info(f"[write-recipe] learned {host} {method} {recipe.url_template[:80]} slot={slot}")
        return recipe
    return None


@typechecked
def build_body(recipe: WriteRecipe, payload: str) -> Optional[Dict[str, Any]]:
    """The recipe body with the NEW payload in the slot; None when the template holds no
    sentinel (corrupt or hand-edited = do not replay) or redacted leaves the site requires."""
    if SENTINEL not in recipe.body_template:
        return None
    try:
        parsed = json.loads(recipe.body_template)
    except (json.JSONDecodeError, ValueError):
        return None

    def p_sub(obj: Any) -> Any:
        if isinstance(obj, str):
            return payload if obj == SENTINEL else obj
        if isinstance(obj, dict):
            return {k: p_sub(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [p_sub(v) for v in obj]
        return obj

    out = p_sub(parsed)
    return out if isinstance(out, dict) else None


@typechecked
async def replay_recipe(recipe: WriteRecipe, payload: str, origin: str) -> Dict[str, Any]:
    """Replay the recipe with a new payload via route_write (same-origin + flag + live-borrowed
    cookies all enforced there). The recipe IS the captured provenance: it was learned from a
    route the site's UI fired during a receipt-verified write, so it seeds the captured set.
    Returns {ok, receipt|error}; a miss bumps the staleness counter and MAX_MISSES drops it."""
    from backend.apps.agents.browser import route_write
    body = build_body(recipe, payload)
    if body is None:
        drop_recipe(recipe.host)
        return {"ok": False, "error": "recipe template unusable; dropped"}
    captured = [route_write.CapturedRoute(method=recipe.method, template=recipe.url_template)]
    import asyncio
    out = await asyncio.to_thread(
        route_write.replay_write, recipe.method, recipe.url, body, origin, captured)
    if out.ok:
        recipe.wins += 1
        save_recipe(recipe)
        return {"ok": True, "receipt": out.receipt, "latency_ms": out.latency_ms}
    recipe.misses += 1
    if recipe.misses >= MAX_MISSES:
        drop_recipe(recipe.host)
        logger.info(f"[write-recipe] {recipe.host} dropped after {recipe.misses} misses (stale; next DOM win re-learns)")
    else:
        save_recipe(recipe)
    return {"ok": False, "error": out.error}
