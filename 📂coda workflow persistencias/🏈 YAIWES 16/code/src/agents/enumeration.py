"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '8311996a9feca6d119fee3ad856133efbbb4c8bb88bf0cfca809a61fd0d2b0e4'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class EnumerationAgent:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('EnumerationAgent.__init__', kwargs)
    def run(self, *args, **kwargs):
        return _yaiwes_checkpoint('EnumerationAgent.run', kwargs)
    def _extract_attack_surface(self, *args, **kwargs):
        return _yaiwes_checkpoint('EnumerationAgent._extract_attack_surface', kwargs)
    def _check_for_flags(self, *args, **kwargs):
        return _yaiwes_checkpoint('EnumerationAgent._check_for_flags', kwargs)
