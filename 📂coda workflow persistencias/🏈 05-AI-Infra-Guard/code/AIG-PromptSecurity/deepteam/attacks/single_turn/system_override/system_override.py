"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'ed421369a8bce312b7a51d021775db8f178d5d53af6c7a04d972d8489fd9a120'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class SystemOverride:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('SystemOverride.__init__', kwargs)
    def enhance(self, *args, **kwargs):
        return _yaiwes_checkpoint('SystemOverride.enhance', kwargs)
    def get_name(self, *args, **kwargs):
        return _yaiwes_checkpoint('SystemOverride.get_name', kwargs)
