#!/usr/bin/env python3
"""test_score.py — valida score.py + retention_bucket."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "registries", "08-memory"))
from score import score, recency, reusability, retention_bucket

now = time.time()

# recency
assert recency(now, now) == 1.0
assert recency(now - 15*86400, now) == 0.5
assert recency(now - 60*86400, now) == 0.2
assert recency(now - 365*86400, now) == 0.05
print("  ok recency buckets")

# reusability
assert reusability(0, 0) == 0.0
assert reusability(10, 10) > 0.5
assert reusability(10, 5) < reusability(10, 10)
print("  ok reusability monotonic en useful")

# score compuesto + retention
assert retention_bucket(0.9) == "permanent"
assert retention_bucket(0.7) == "permanent"
assert retention_bucket(0.5) == "1y"
assert retention_bucket(0.3) == "90d"
assert retention_bucket(0.05) == "immediate_purge"
print("  ok retention buckets")

# score concreto: alta importance + fresh + usado = high
high = score({"created_at": now, "importance": 0.9, "times_used": 10, "times_useful": 10}, now)
assert high >= 0.7, f"esperaba >=0.7, got {high}"
print(f"  ok score high={high:.3f}")

# score concreto: baja importance + viejo + sin uso = low
low = score({"created_at": now - 60*86400, "importance": 0.1, "times_used": 0, "times_useful": 0}, now)
assert low < 0.2, f"esperaba <0.2, got {low}"
print(f"  ok score low={low:.3f}")

print("PASS test_score")
