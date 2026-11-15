# -*- coding: utf-8 -*-
"""Tests T0q PushPing memory hooks."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.ports.memory_port import FakeHermesMemory
from extensions.wordflow.engine.push_ping_hooks import PushPingWithMemory, load_ping_policy
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestPushPingHooks(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: hook memory en ping\n"
            "success: pack opcional sin crash\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_no_port_no_crash(self):
        lock = self._lock()
        sup = PushPingWithMemory(lock, memory_port=None)
        ev = sup.post_tool_ping(
            current_step="hook memory",
            last_output="hook memory en ping ok",
        )
        self.assertNotIn("memory_pack_id", ev)
        self.assertIsNone(sup.last_memory_pack)

    def test_degraded_triggers_memory(self):
        lock = self._lock()
        port = FakeHermesMemory()
        sup = PushPingWithMemory(
            lock,
            memory_port=port,
            memory_on_focus_degraded=True,
            focus_threshold=0.9,
        )
        ev = sup.post_tool_ping(
            current_step="otro tema",
            last_output="cocinar pasta",
        )
        self.assertEqual(ev["action"], "STOP_REPLAN")
        self.assertIsNotNone(sup.last_memory_pack)
        self.assertEqual(ev.get("memory_pack_id"), sup.last_memory_pack["pack_id"])

    def test_every_n_interval(self):
        lock = self._lock()
        sup = PushPingWithMemory(
            lock,
            memory_port=FakeHermesMemory(),
            memory_every_n_interval=2,
            interval_s=1,
        )
        e1 = sup.maybe_interval_ping(
            now_mono=0.0,
            current_step="hook memory en ping",
            last_output="hook memory en ping",
        )
        self.assertIsNotNone(e1)
        # first interval count=1 → not multiple of 2
        self.assertIsNone(sup.last_memory_pack)
        e2 = sup.maybe_interval_ping(
            now_mono=10.0,
            current_step="hook memory en ping",
            last_output="hook memory en ping",
        )
        self.assertIsNotNone(e2)
        self.assertIsNotNone(sup.last_memory_pack)

    def test_load_policy(self):
        p = load_ping_policy(
            {
                "ping": {
                    "interval_s": 15,
                    "memory_refresh": {"enabled": True, "every_n_interval_pings": 4},
                }
            }
        )
        self.assertEqual(p["memory_every_n_interval"], 4)


if __name__ == "__main__":
    unittest.main()
