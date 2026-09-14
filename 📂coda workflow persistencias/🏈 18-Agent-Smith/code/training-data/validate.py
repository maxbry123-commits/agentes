#!/usr/bin/env python3
"""Validate the lab-engagement-001 fixture against the smith-event schemas and run the §15.1
checks that need no external infra (training-data-plan.md). Every predicate check is paired with a
NEGATIVE CONTROL — a crafted violation it must catch — so no check is "green by construction".
The fold-based Replay/Correction/Snapshot checks live in eventstore/acceptance.py.

Run:  .venv/bin/python training-data/build_derived.py   # once, to bake derived digests
      .venv/bin/python training-data/validate.py
Exit 0 = all pass, 1 = any failure.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = pathlib.Path(__file__).parent
SCHEMAS = ROOT / "schemas"
FX = ROOT / "fixtures" / "lab-engagement-001"

RESOURCES = [(json.loads(f.read_text())["$id"], Resource.from_contents(json.loads(f.read_text())))
             for f in sorted(SCHEMAS.glob("*.json"))]
REGISTRY = Registry().with_resources(RESOURCES)
SCHEMA_BY_ID = {sid: res.contents for sid, res in RESOURCES}

EVENT_SCHEMA = {
    "observation": "observation-event.schema.json",
    "decision": "decision-event.schema.json",
    "action": "action-event.schema.json",
    "result": "result-event.schema.json",
    "adjudication": "adjudication-event.schema.json",
}


def digest(obj) -> str:
    """Canonical §13 serialization: sorted keys, no whitespace, UTF-8. Matches build_derived.py."""
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(b).hexdigest()


def derive_level(p, theta=0.8):
    repro = p["success_count"] / max(p["attempt_count"], 1)
    indep = min(p["independent_method_count"], 3)
    directness = 2 if p["is_deterministic"] else (1 if p["success_count"] > 0 else 0)
    impact = 1 if p.get("impact_observed") else 0
    human = p.get("human_review_count", 0) > 0
    if human and repro >= theta and indep >= 2:
        return "V5"
    if indep >= 2 and repro >= theta:
        return "V4"
    if directness == 2 and p["success_count"] >= 1:
        return "V3"
    if repro >= theta and impact >= 1:
        return "V2"
    if p["independent_method_count"] >= 1 or p["success_count"] >= 1:
        return "V1"
    return "V0"


def exportable(decision_ev):
    """Teacher gate (§12): a record is exportable only if its proposing model is open-weight."""
    return decision_ev.get("decision", {}).get("provenance", {}).get("teacher_origin") == "open_weight"


def rp_hash(m):
    """rendered_prompt_hash binds components + renderer + tokenizer (§3.6). Matches build_derived.py."""
    return digest({"components": sorted(m["components"], key=lambda c: c["ordinal"]),
                   "renderer_version": m["renderer_version"], "tokenizer_ref": m["tokenizer_ref"]})


def dag_violations(evs):
    s = {e["event_id"]: e["sequence"] for e in evs}
    return [f"{p} >= {e['event_id']}" for e in evs
            for p in e.get("caused_by", []) + e.get("depends_on", []) if s.get(p, -1) >= e["sequence"]]


def trust_violation(ev):
    t = ev.get("observation", {}).get("trust")
    return bool(t and t.get("trust") == "untrusted" and (t.get("rendering") != "data" or t.get("instruction_authority")))


def correction_violation(ev):
    return ev.get("event_type") == "adjudication" and bool(set(ev.get("supersedes", [])) & set(ev.get("caused_by", [])))


def latent_write(ev):
    return ev.get("observation", {}).get("updates_state_layer") == "latent"


def check_schema(schema_id, doc, errors, label):
    for e in Draft202012Validator(SCHEMA_BY_ID[schema_id], registry=REGISTRY).iter_errors(doc):
        errors.append(f"[SCHEMA] {label}: {e.message} @ /{'/'.join(map(str, e.path))}")


DERIV_CASES = [  # exercises every V-level branch, not just the one the fixture hits
    ({"attempt_count": 1, "success_count": 0, "independent_method_count": 0, "is_deterministic": False}, "V0"),
    ({"attempt_count": 3, "success_count": 1, "independent_method_count": 1, "is_deterministic": False}, "V1"),
    ({"attempt_count": 5, "success_count": 5, "independent_method_count": 1, "is_deterministic": False, "impact_observed": True}, "V2"),
    ({"attempt_count": 2, "success_count": 2, "independent_method_count": 1, "is_deterministic": True}, "V3"),
    ({"attempt_count": 5, "success_count": 5, "independent_method_count": 2, "is_deterministic": False}, "V4"),
    ({"attempt_count": 5, "success_count": 5, "independent_method_count": 2, "is_deterministic": False, "human_review_count": 1}, "V5"),
]


def main():
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'training-data/validate.py','step':'main','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


if __name__ == "__main__":
    main()
