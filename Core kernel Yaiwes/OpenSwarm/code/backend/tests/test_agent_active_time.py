"""ENG-189: agent_active_ms means time the agent was producing, not turn wall-clock. A stalled
gap between events books at most the 30s cap, so one wedged turn can't be 92% of the metric."""

from backend.apps.agents.manager.streaming.state import TurnState


def p_feed(turn: TurnState, ts: float) -> None:
    if turn.last_event_ts is not None:
        turn.active_ms += int(min(ts - turn.last_event_ts, 30.0) * 1000)
    turn.last_event_ts = ts


def test_stalled_gap_books_the_cap_not_the_wall():
    turn = TurnState()
    p_feed(turn, 1000.0)
    p_feed(turn, 1001.0)      # 1s of work
    p_feed(turn, 4601.0)      # a 1-HOUR stall books 30s, not 3600s
    p_feed(turn, 4602.5)      # 1.5s more work
    assert turn.active_ms == 1000 + 30_000 + 1500


def test_busy_turn_books_real_time():
    turn = TurnState()
    for i in range(11):
        p_feed(turn, 100.0 + i * 0.5)
    assert turn.active_ms == 5_000
