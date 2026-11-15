#!/usr/bin/env python3
"""YAIWES deterministic evolution planner. It never mutates repositories."""
from __future__ import annotations
import argparse, hashlib, json, re
from dataclasses import dataclass, asdict
from pathlib import Path

TRIGGERS = ("evolucionar", "evolución", "evolucion", "evolve", "incorporar", "mejorar capacidad")
TARGETS = ("extension-kernel", "new-workflow", "tools-pool", "knowledge-skill-dataset")
INPUT_GOALS = (
 "identity","requested-capability","current-capability","source-provenance","license",
 "security-history","network-behavior","public-contract","dependencies","reproducibility",
 "observability","rollback-plan")
OUTPUT_GOALS = (
 "capability-gap","reuse-candidate","integration-mode","target-layer","pruned-boundary",
 "abi-contract","passport","sandbox-plan","verification-plan","download-plan",
 "risk-score","director-decision")
CONSILIO = (
 "Is it already native?","Is the source authoritative?","Is the license compatible?",
 "Can network egress be denied?","Is the API stable?","Can decision logic be removed?",
 "Is a workflow enough?","Does it require autonomous memory?","Is it knowledge-only?",
 "Are effects idempotent?","Can it be rolled back?","What evidence would reject it?")

@dataclass(frozen=True)
class Proposal:
    state: str; fingerprint: str; deterministic_score: int; llm_budget: int
    target: str; mode: str; input_goals: tuple[str,...]; output_goals: tuple[str,...]
    ask_consilio: tuple[str,...]; director_authorization_required: bool
    download_skill: str; evidence: dict

def awakened(order: str) -> bool:
    value = order.casefold()
    return any(t in value for t in TRIGGERS)

def classify(facts: dict) -> tuple[str,str]:
    if facts.get("knowledge_only"): return TARGETS[3], "retain-as-knowledge"
    if facts.get("fixed_sequence") and not facts.get("autonomous_memory"): return TARGETS[1], "workflow-dag"
    if facts.get("autonomous_memory") or facts.get("independent_reasoning"): return TARGETS[2], "isolated-subagent"
    return TARGETS[0], "prune-decision-layer-and-wrap-abi"

def plan(order: str, facts: dict) -> Proposal:
    if not awakened(order): raise ValueError("watchdog trigger absent")
    missing=[g for g in INPUT_GOALS if g not in facts]
    target, mode=classify(facts)
    penalties=min(45, 5*len(missing)) + (20 if not facts.get("source_provenance") else 0)
    score=max(0,95-penalties)
    evidence={"facts":facts,"missing":missing,"rule":"deterministic-95-llm-max-5"}
    fp=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
    return Proposal("AWAITING_DIRECTOR",fp,score,5,target,mode,INPUT_GOALS,OUTPUT_GOALS,
                    CONSILIO,True,"skills/research-download-chain/SKILL.md",evidence)

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("order"); p.add_argument("facts_json",type=Path)
    p.add_argument("--out",type=Path,default=Path("evolution-proposal.json")); a=p.parse_args()
    proposal=plan(a.order,json.loads(a.facts_json.read_text(encoding="utf-8")))
    a.out.write_text(json.dumps(asdict(proposal),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(a.out); return 0
if __name__ == "__main__": raise SystemExit(main())
