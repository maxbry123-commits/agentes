"""Tests for ATL ActionQueue."""

from __future__ import annotations

from cognithor.evolution.action_queue import ActionQueue, ATLAction


def test_enqueue_and_dequeue():
    q = ActionQueue(max_actions=3)
    a1 = ATLAction(type="research", params={"query": "test"}, priority=2, rationale="test")
    a2 = ATLAction(type="notification", params={}, priority=1, rationale="urgent")
    q.enqueue(a1)
    q.enqueue(a2)
    # Higher priority (lower number) dequeued first
    assert q.dequeue().type == "notification"
    assert q.dequeue().type == "research"


def test_max_limit():
    q = ActionQueue(max_actions=2)
    for i in range(5):
        q.enqueue(ATLAction(type="research", params={}, priority=3, rationale=f"r{i}"))
    count = 0
    while not q.empty():
        q.dequeue()
        count += 1
    assert count == 2  # Only 2 kept


def test_empty():
    q = ActionQueue(max_actions=3)
    assert q.empty()
    q.enqueue(ATLAction(type="research", params={}, priority=3, rationale=""))
    assert not q.empty()


def test_blocked_types():
    q = ActionQueue(max_actions=3, blocked_types={"shell_exec"})
    result = q.enqueue(ATLAction(type="shell_exec", params={}, priority=1, rationale=""))
    assert result is False
    assert q.empty()


def test_size():
    q = ActionQueue(max_actions=5)
    q.enqueue(ATLAction(type="research", params={}, priority=3, rationale="a"))
    q.enqueue(ATLAction(type="research", params={}, priority=3, rationale="b"))
    assert q.size() == 2


def test_clear():
    q = ActionQueue(max_actions=5)
    q.enqueue(ATLAction(type="research", params={}, priority=3, rationale="a"))
    q.clear()
    assert q.empty()
