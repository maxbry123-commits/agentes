"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '5ac49aa4d2c3cc27369fb04f5afe618bed864f91412cae1200f9254a33607df2'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class PromptInjection:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('PromptInjection.__init__', kwargs)
    def enhance(self, *args, **kwargs):
        return _yaiwes_checkpoint('PromptInjection.enhance', kwargs)
    def get_name(self, *args, **kwargs):
        return _yaiwes_checkpoint('PromptInjection.get_name', kwargs)
