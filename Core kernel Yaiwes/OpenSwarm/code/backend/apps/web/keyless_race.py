"""Race the free search engines instead of queueing them.

Walking them in order made whether search was FAST depend on whether the first
engine happened to be alive, which is not a property we control. Measured from
a fresh backend on a machine where DuckDuckGo had stopped answering TCP: the
first three searches took 8.8s each, because each one waited out the dead
engine's whole tier budget before Startpage was allowed to try. A desktop app
starts its backend on every launch, so that was the first thing a user saw.

So the second engine no longer waits for the first to fail; it waits only for
the first to be SLOW. If the leader answers inside the hedge delay, which a
healthy frontend does with room to spare, nothing else is sent and the traffic
is exactly what it was before. If it doesn't, the next engine starts alongside
it and the first good answer wins. A dead engine now costs the hedge delay
once, instead of its full budget forever.

The breaker underneath is what makes it cost nothing on the queries after that,
but it is now an optimisation rather than the thing standing between the user
and an answer.
"""

import asyncio
from typing import Awaitable, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, InstanceOf
from typeguard import typechecked

from backend.apps.web.tier_breaker import (
    record_tier_failure,
    record_tier_success,
    tier_cooldown_left,
)

# Measured across 44 queries: a healthy DuckDuckGo answered in 0.68-1.14s and a healthy Startpage in 0.46-1.33s, so a frontend still silent at 1.5s is not about to win the race.
HEDGE_AFTER_SECONDS = 1.5


class KeylessEngine(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str
    run: InstanceOf[Callable[[], Awaitable[Optional[Dict]]]]


class RaceOutcome(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    result: Optional[Dict] = None
    errors: List[str] = Field(default_factory=list)


@typechecked
async def race_keyless(
    engines: List[KeylessEngine],
    budget: float,
    hedge_after: float = HEDGE_AFTER_SECONDS,
) -> RaceOutcome:
    """First good answer wins; a slow engine pulls in the next one rather than blocking it."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + budget
    errors: List[str] = []

    live: List[KeylessEngine] = []
    for engine in engines:
        cooling = tier_cooldown_left(engine.name)
        if cooling:
            errors.append(f"{engine.name}: skipped, still failing (retry in {cooling:.0f}s)")
        else:
            live.append(engine)
    if not live:
        return RaceOutcome(errors=errors)

    running: Dict[asyncio.Task, str] = {}
    started: Dict[str, float] = {}
    next_engine = 0

    def start_next() -> None:
        nonlocal next_engine
        engine = live[next_engine]
        next_engine += 1
        started[engine.name] = loop.time()
        running[asyncio.ensure_future(engine.run())] = engine.name

    start_next()
    result: Optional[Dict] = None

    while running and result is None:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        wait_for = remaining
        if next_engine < len(live):
            # Hedge off the engine that has been waiting longest, so a stalled leader pulls the next one in on time.
            oldest = min(started[name] for name in running.values())
            wait_for = min(wait_for, max(0.0, oldest + hedge_after - loop.time()))
        done: Set[asyncio.Task] = set()
        done, _ = await asyncio.wait(set(running), timeout=wait_for,
                                     return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            name = running.pop(task)
            try:
                answer = task.result()
            except asyncio.CancelledError:
                continue
            except Exception as exc:
                errors.append(f"{name}: {str(exc)[:150]}")
                record_tier_failure(name)
                continue
            # Answering "no hits" still proves the host is up, so it clears the failure streak.
            record_tier_success(name)
            if answer is not None and result is None:
                result = answer
        if result is None and next_engine < len(live) and (not done or not running):
            start_next()

    for task, name in running.items():
        task.cancel()
        silent_for = loop.time() - started[name]
        # It never answered in the window a healthy engine answers three times over, so stop asking it for a while.
        if silent_for >= hedge_after:
            errors.append(f"{name}: no response in {silent_for:.0f}s")
            record_tier_failure(name, conclusive=True)
    if running:
        await asyncio.gather(*running, return_exceptions=True)

    return RaceOutcome(result=result, errors=errors)
