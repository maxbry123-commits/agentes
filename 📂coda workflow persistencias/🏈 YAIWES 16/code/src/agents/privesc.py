"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'ec5fd9e3c693aea005f45c5734640181cf8ffb49acc07deae9a2e6e1f54267ed'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class PrivescAgent:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('PrivescAgent.__init__', kwargs)
    def run(self, *args, **kwargs):
        return _yaiwes_checkpoint('PrivescAgent.run', kwargs)
    def _check_for_flags(self, *args, **kwargs):
        return _yaiwes_checkpoint('PrivescAgent._check_for_flags', kwargs)
