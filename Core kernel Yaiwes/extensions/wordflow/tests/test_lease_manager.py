# -*- coding: utf-8 -*-
"""Tests T17 LeaseManager."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.lease_manager import LeaseError, LeaseManager


class FakeClock:
    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class TestLeaseManager(unittest.TestCase):
    def test_issue_alive(self):
        clk = FakeClock(0.0)
        lm = LeaseManager(default_ttl_s=10.0, clock=clk)
        lease = lm.issue(subject_id="task_1", ttl_s=10.0)
        self.assertTrue(lm.is_alive(lease["lease_id"]))

    def test_expire(self):
        clk = FakeClock(0.0)
        lm = LeaseManager(default_ttl_s=5.0, clock=clk)
        lease = lm.issue(subject_id="t", ttl_s=5.0)
        clk.advance(6.0)
        self.assertFalse(lm.is_alive(lease["lease_id"]))
        self.assertEqual(lm.get(lease["lease_id"])["status"], "EXPIRED")

    def test_renew(self):
        clk = FakeClock(0.0)
        lm = LeaseManager(clock=clk)
        lease = lm.issue(subject_id="t", ttl_s=5.0)
        clk.advance(4.0)
        lm.renew(lease["lease_id"], ttl_s=10.0)
        clk.advance(6.0)
        self.assertTrue(lm.is_alive(lease["lease_id"]))

    def test_sweep(self):
        clk = FakeClock(0.0)
        lm = LeaseManager(clock=clk)
        a = lm.issue(subject_id="a", ttl_s=1.0)
        b = lm.issue(subject_id="b", ttl_s=100.0)
        clk.advance(2.0)
        expired = lm.sweep_expired()
        self.assertIn(a["lease_id"], expired)
        self.assertNotIn(b["lease_id"], expired)

    def test_release(self):
        lm = LeaseManager()
        lease = lm.issue(subject_id="x")
        lm.release(lease["lease_id"])
        self.assertFalse(lm.is_alive(lease["lease_id"]))


if __name__ == "__main__":
    unittest.main()
