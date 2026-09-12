"""YAIWES adapter for moved SakanaAI AI-Scientist seed-idea capability."""
from __future__ import annotations
import importlib
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID='yaiwes.agent.ai_scientist'
ROLE='scientific_research_agent'
UPSTREAM_RELATIVE=Path('Agente Yaiwes principal/agent-fleet-parallelism/ai-scientist/AI-Scientist')

def run_seed_idea_microtest(repo_root: str | Path) -> dict[str, Any]:
    root=Path(repo_root).resolve()
    upstream=root/UPSTREAM_RELATIVE
    template=upstream/'templates'/'grokking'
    if not (template/'seed_ideas.json').is_file():
        raise RuntimeError('AI_SCIENTIST_REAL_SEED_MISSING')
    sys.path.insert(0,str(upstream))
    mod=importlib.import_module('ai_scientist.generate_ideas')
    result=mod.generate_next_idea(str(template), client=None, model='gpt-4o-mini', prev_idea_archive=[], num_reflections=1, max_attempts=1)
    if not isinstance(result,list) or len(result)!=1:
        raise RuntimeError(f'AI_SCIENTIST_BAD_ARCHIVE:{result!r}')
    idea=result[0]
    expected={'Name':'batch_size_grokking','Interestingness':6,'Feasibility':4,'Novelty':4}
    for k,v in expected.items():
        if idea.get(k)!=v: raise RuntimeError(f'AI_SCIENTIST_SEED_MISMATCH:{k}:{idea.get(k)!r}')
    return {'status':'PASS','capability':'generate_next_idea_seed_path','idea_name':idea['Name'],'interestingness':idea['Interestingness'],'feasibility':idea['Feasibility'],'novelty':idea['Novelty']}
