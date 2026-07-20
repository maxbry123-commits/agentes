#!/usr/bin/env python3
"""score.py — mecanismo de scoring de memories (registry 08-memory).

score = recency * 0.3 + importance * 0.4 + reusability * 0.3
"""
import time, math

def recency(created_at_epoch: float, now: float = None) -> float:
    """1.0 si <7d, 0.5 si 7-30d, 0.2 si >30d (decae exponencial)."""
    if now is None: now = time.time()
    age_days = (now - created_at_epoch) / 86400.0
    if age_days < 7:    return 1.0
    if age_days < 30:   return 0.5
    if age_days < 90:   return 0.2
    return 0.05

def reusability(times_used: int, times_useful: int) -> float:
    """Basado en ratio + saturación logarítmica de uso."""
    if times_used == 0: return 0.0
    ratio = times_useful / times_used
    sat = min(1.0, math.log1p(times_used) / math.log1p(20))
    return round(ratio * sat, 3)

def score(memory: dict, now: float = None) -> float:
    """Calcula el score compuesto. Retorna 0..1."""
    r = recency(memory.get("created_at", time.time()), now)
    i = float(memory.get("importance", 0.5))
    re = reusability(memory.get("times_used", 0), memory.get("times_useful", 0))
    return round(r * 0.3 + i * 0.4 + re * 0.3, 4)

def retention_bucket(score_val: float) -> str:
    """Devuelve el bucket de retención según score."""
    if score_val >= 0.7: return "permanent"
    if score_val >= 0.4: return "1y"
    if score_val >= 0.1: return "90d"
    return "immediate_purge"

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    # Test
    now = time.time()
    cases = [
        ({"created_at": now, "importance": 0.9, "times_used": 10, "times_useful": 9}, 0.7),  # alta importance, fresh
        ({"created_at": now - 60*86400, "importance": 0.5, "times_used": 5, "times_useful": 5}, None),  # viejo
        ({"created_at": now, "importance": 0.1, "times_used": 0, "times_useful": 0}, None),  # baja importance, sin uso
    ]
    for mem, _ in cases:
        s = score(mem, now)
        b = retention_bucket(s)
        print(f"  ok score={s:.3f} bucket={b} (importance={mem['importance']}, age={(now-mem['created_at'])/86400:.0f}d, used={mem['times_used']})")
    print("PASS score.py")
