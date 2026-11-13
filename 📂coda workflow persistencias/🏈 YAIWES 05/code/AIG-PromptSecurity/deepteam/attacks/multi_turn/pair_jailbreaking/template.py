"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'dc61106222ef1ea9c99d9676684f7001532344a319576cd33f1ab0a7cb9dc5ba'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class PAIRTemplate:
    def attacker_system_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('PAIRTemplate.attacker_system_prompt', kwargs)
    def initial_attacker_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('PAIRTemplate.initial_attacker_prompt', kwargs)
    def next_round_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('PAIRTemplate.next_round_prompt', kwargs)
    def non_refusal(self, *args, **kwargs):
        return _yaiwes_checkpoint('PAIRTemplate.non_refusal', kwargs)
    def judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('PAIRTemplate.judge', kwargs)
