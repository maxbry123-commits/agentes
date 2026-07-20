#!/usr/bin/env python3
"""test_sync.py — offline test del sync engine."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sync import validate_agentskills_io, score, dedupe_key

cases = [
    # (skill, expected_valid, reason_if_invalid)
    ({"name": "task-manager", "description": "Gestiona TODOs."}, True, None),
    ({"name": "x", "description": "ok"}, True, None),  # 1 char name, valido
    ({"name": "BadName", "description": "mayus no permitido"}, False, "name charset"),
    ({"name": "-leading", "description": "no leading hyphen"}, False, "name leading/trailing hyphen"),
    ({"name": "trailing-", "description": "no trailing hyphen"}, False, "name leading/trailing hyphen"),
    ({"name": "a"*65, "description": "name muy largo"}, False, "name length"),
    ({"name": "ok", "description": ""}, False, "description length"),
    ({"name": "ok", "description": "x"*1025}, False, "description length"),
    ({"name": "ok", "description": "x"*1024}, True, None),
]

ok_count = 0
for skill, expected, reason in cases:
    valid, why = validate_agentskills_io(skill)
    if valid == expected:
        ok_count += 1
        print(f"  ok {skill.get('name','?')[:20]:20s} {why}")
    else:
        print(f"  FAIL {skill.get('name','?')[:20]:20s} got {valid}/{why}, want {expected}/{reason}")

assert ok_count == len(cases), f"solo {ok_count}/{len(cases)} pasaron"
print(f"  ok dedupe_key={dedupe_key({'name':'task-manager','description':'Gestiona TODOs persistentes del orquestador. Permite crear, listar, marcar y asignar tareas'})}")

# score
assert score({"trust_tier":"official"}) == 0.5
assert score({"trust_tier":"community"}) == 0.2
assert score({"trust_tier":"unknown"}) == 0.1
assert score({"trust_tier":"curated","votes":200}) == 0.6  # 0.4 + 0.2
print("  ok score tiers")

print("PASS test_sync")
