"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'c80154c002e6ad9c6ef5a33285c085f107d4573c7e508aac5ec424ad183b6158'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class ActorAttackTemplate:
    def generate_actor_network(self, *args, **kwargs):
        return _yaiwes_checkpoint('ActorAttackTemplate.generate_actor_network', kwargs)
    def next_probe_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('ActorAttackTemplate.next_probe_prompt', kwargs)
    def non_refusal(self, *args, **kwargs):
        return _yaiwes_checkpoint('ActorAttackTemplate.non_refusal', kwargs)
    def judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('ActorAttackTemplate.judge', kwargs)
