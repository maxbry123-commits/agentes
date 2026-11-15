"""Short-lived circuit breaker for the cascade's fixed-host tiers.

Measured on this machine over three 44-query rounds: DuckDuckGo answered the
first 7 searches, then served its bot challenge, then 403'd, then stopped
answering TCP altogether. Once that happened EVERY search paid the full 8s
DuckDuckGo tier budget before Startpage answered, so the keyless p50 went from
1.0s to 8.5s while the success rate stayed at 100%. The engine wasn't broken,
our retrying of a known-dead engine was.

A tier only opts in when "closed" is a property of the HOST rather than of the
request, which is true for a search frontend and false for a page fetch (one
404 says nothing about the next URL). State is per-process and time-boxed, so
the worst a wrong guess costs is one cooldown window of a tier we skip.
"""

import time
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

# Two failures can be one bad minute; three in a row is a closed door.
FAILURES_TO_OPEN = 3
FIRST_COOLDOWN_SECONDS = 120.0
MAX_COOLDOWN_SECONDS = 900.0


class TierHealth(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    consecutive_failures: int = 0
    open_until: float = 0.0
    cooldown: float = 0.0


p_health: Dict[str, TierHealth] = {}


@typechecked
def p_entry(name: str) -> TierHealth:
    if name not in p_health:
        p_health[name] = TierHealth()
    return p_health[name]


@typechecked
def tier_cooldown_left(name: str, now: Optional[float] = None) -> float:
    """Seconds until this tier is worth trying again; 0 when it is open for business."""
    entry = p_health.get(name)
    if entry is None:
        return 0.0
    return max(0.0, entry.open_until - (time.monotonic() if now is None else now))


@typechecked
def record_tier_failure(name: str, now: Optional[float] = None, *, conclusive: bool = False) -> None:
    """A failure. An error ANSWER is one strike of three, because a 202 or a 403 can be a bad
    minute. SILENCE is conclusive and shuts the tier at once: a frontend that returns nothing at
    all in the time a healthy one answers three times over is not having a bad minute, and making
    the user prove it three times is what put 8.8s on their first three searches after launch."""
    stamp = time.monotonic() if now is None else now
    entry = p_entry(name)
    entry.consecutive_failures += 1
    if not conclusive and entry.consecutive_failures < FAILURES_TO_OPEN:
        return
    # The half-open probe that fails again doubles the wait, so a permanently dead engine stops costing anything.
    entry.cooldown = min(max(entry.cooldown * 2, FIRST_COOLDOWN_SECONDS), MAX_COOLDOWN_SECONDS)
    entry.open_until = stamp + entry.cooldown


@typechecked
def record_tier_success(name: str) -> None:
    """The tier answered, even if the answer was 'no hits'. It is alive; forget the history."""
    if name in p_health:
        p_health[name] = TierHealth()


@typechecked
def reset_tier_health() -> None:
    p_health.clear()
