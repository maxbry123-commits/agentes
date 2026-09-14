"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '266ca0ab8aa9f596c005e513d3fe459b5df014deb82316a55f277916cc4444d7'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class Overload:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('Overload.__init__', kwargs)
    def enhance(self, *args, **kwargs):
        return _yaiwes_checkpoint('Overload.enhance', kwargs)
    def _generate_mapping(self, *args, **kwargs):
        return _yaiwes_checkpoint('Overload._generate_mapping', kwargs)
    def _build_charset(self, *args, **kwargs):
        return _yaiwes_checkpoint('Overload._build_charset', kwargs)
    def get_name(self, *args, **kwargs):
        return _yaiwes_checkpoint('Overload.get_name', kwargs)
