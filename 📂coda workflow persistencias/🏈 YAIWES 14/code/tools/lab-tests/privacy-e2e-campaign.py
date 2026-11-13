"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'e935f51b2cbd077e5ab9ece4f3e80f2364a5fc75515d84733f34bbe4d277a8c5'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def ip_of(*args, **kwargs):
    return _yaiwes_checkpoint('ip_of', kwargs)

def first_match(*args, **kwargs):
    return _yaiwes_checkpoint('first_match', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)

def write_report(*args, **kwargs):
    return _yaiwes_checkpoint('write_report', kwargs)

class Campaign:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('Campaign.__init__', kwargs)
    def protect(self, *args, **kwargs):
        return _yaiwes_checkpoint('Campaign.protect', kwargs)
    def observe(self, *args, **kwargs):
        return _yaiwes_checkpoint('Campaign.observe', kwargs)
    def run(self, *args, **kwargs):
        return _yaiwes_checkpoint('Campaign.run', kwargs)
