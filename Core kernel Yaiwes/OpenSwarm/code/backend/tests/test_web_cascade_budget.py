"""The /api/web cascade is bounded by ONE wall-clock budget.

Seals the class of bug where the cascade's own leashes summed to 244s (search)
/ 270s (fetch) while the MCP shim gave up at 45s, so the later tiers were
unreachable and search "worked" only when an early tier won the race.
"""

import asyncio
import time

import pytest

import backend.apps.web.cascade as C
from backend.apps.web.cascade import CascadeTier, run_cascade


@pytest.fixture
def p_tiny_floor(monkeypatch):
    """Shrink the honest-slice floor so budget tests run in milliseconds, not seconds."""
    monkeypatch.setattr(C, "MIN_TIER_SECONDS", 0.05)


def p_tier(name, budget, fn):
    return CascadeTier(name=name, run=fn, budget=budget)


async def p_hangs():
    await asyncio.sleep(60)


async def p_none():
    return None


@pytest.mark.asyncio
async def test_first_result_short_circuits():
    async def p_hit():
        return {"backend": "one"}

    async def p_boom():
        raise AssertionError("later tiers must not run once a tier answers")

    out = await run_cascade([p_tier("a", 5, p_hit), p_tier("b", 5, p_boom)], 10.0)
    assert out.result == {"backend": "one"}
    assert out.errors == []


@pytest.mark.asyncio
async def test_total_budget_bounds_the_whole_cascade(p_tiny_floor):
    # Four tiers each willing to burn 60s: without a shared deadline this runs for minutes.
    tiers = [p_tier(f"t{i}", 60.0, p_hangs) for i in range(4)]
    t0 = time.monotonic()
    out = await run_cascade(tiers, 1.0)
    elapsed = time.monotonic() - t0
    assert elapsed < 2.0, f"cascade overran its budget: {elapsed:.2f}s"
    assert out.result is None
    assert any("timed out" in e for e in out.errors)


@pytest.mark.asyncio
async def test_a_slow_tier_cannot_starve_the_ones_behind_it(p_tiny_floor):
    # A hanging tier is cut at ITS OWN budget, so the tier behind it still gets its turn and wins.
    async def p_hit():
        return {"backend": "rescue"}

    out = await run_cascade([p_tier("slow", 0.4, p_hangs), p_tier("fast", 5.0, p_hit)], 3.0)
    assert out.result == {"backend": "rescue"}
    assert any("slow" in e and "timed out" in e for e in out.errors)


@pytest.mark.asyncio
async def test_unreachable_tiers_are_reported_not_silently_dropped():
    async def p_slow():
        await asyncio.sleep(0.6)
        return None

    out = await run_cascade(
        [p_tier("burn", 5.0, p_slow), p_tier("never_a", 5.0, p_none), p_tier("never_b", 5.0, p_none)],
        0.6 + C.MIN_TIER_SECONDS - 0.1,
    )
    assert out.result is None
    tail = out.errors[-1]
    assert "budget spent" in tail
    assert "never_a" in tail and "never_b" in tail


@pytest.mark.asyncio
async def test_a_tier_slice_never_drops_below_the_honest_floor():
    # A tier handed 0.2s would "time out" on a hair trigger; we must say the budget ran out instead.
    async def p_slow():
        await asyncio.sleep(0.5)
        return None

    out = await run_cascade([p_tier("burn", 5.0, p_slow), p_tier("squeezed", 5.0, p_hangs)], 0.5 + 1.0)
    assert out.result is None
    assert not any("squeezed" in e and "timed out" in e for e in out.errors)
    assert any("budget spent" in e for e in out.errors)


@pytest.mark.asyncio
async def test_tier_exception_is_recorded_and_the_chain_continues():
    async def p_boom():
        raise RuntimeError("provider down")

    async def p_hit():
        return {"backend": "next"}

    out = await run_cascade([p_tier("bad", 5.0, p_boom), p_tier("good", 5.0, p_hit)], 10.0)
    assert out.result == {"backend": "next"}
    assert out.errors == ["bad: provider down"]


def test_mcp_shim_waits_longer_than_the_server_budget():
    """The shim must outlast the cascade, or the later tiers are unreachable again."""
    from backend.apps.agents.web_mcp_server import TOOL_TIMEOUT
    from backend.apps.web.web import FETCH_BUDGET_SECONDS, SEARCH_BUDGET_SECONDS

    assert TOOL_TIMEOUT > SEARCH_BUDGET_SECONDS
    assert TOOL_TIMEOUT > FETCH_BUDGET_SECONDS


def test_search_tier_budgets_leave_room_for_the_grounded_tier():
    """The free rungs must not eat the whole budget before a paid backend is tried."""
    import backend.apps.web.web as W

    # A grounded native call needs ~30-42s, so the free rungs must leave it a usable slice.
    grounded_floor = 20.0
    search_cheap = 2 * W.KEYLESS_TIER_SECONDS + W.BROWSER_TIER_SECONDS
    assert W.SEARCH_BUDGET_SECONDS - search_cheap >= grounded_floor
    fetch_cheap = W.LOCAL_FETCH_TIER_SECONDS + W.BROWSER_TIER_SECONDS + W.ARCHIVE_TIER_SECONDS
    assert W.FETCH_BUDGET_SECONDS - fetch_cheap >= grounded_floor
