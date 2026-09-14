"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '19d20bfe392cc0dfdc0e94ca59aa12c816fbf15c1d435110b93fc6f94f14c269'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class GoatTemplate:
    def planner_system_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('GoatTemplate.planner_system_prompt', kwargs)
    def first_turn_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('GoatTemplate.first_turn_prompt', kwargs)
    def next_turn_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('GoatTemplate.next_turn_prompt', kwargs)
    def non_refusal(self, *args, **kwargs):
        return _yaiwes_checkpoint('GoatTemplate.non_refusal', kwargs)
    def judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('GoatTemplate.judge', kwargs)
