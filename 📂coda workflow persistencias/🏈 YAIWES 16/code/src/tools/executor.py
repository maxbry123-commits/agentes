"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'bdde913853d26b9f3d1793d8f2f3514bcda313abe5c1a8ae324370cce21bc55c'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class ToolExecutor:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('ToolExecutor.__init__', kwargs)
    def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolExecutor.execute', kwargs)
    def _is_blocked(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolExecutor._is_blocked', kwargs)
    def _needs_confirmation(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolExecutor._needs_confirmation', kwargs)
