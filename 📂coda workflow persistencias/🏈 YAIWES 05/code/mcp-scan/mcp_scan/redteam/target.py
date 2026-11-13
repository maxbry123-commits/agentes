"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '361af8d96c7bcf9fc012b23396eeb7aa3de5bdbd9ecff76678fc83e84d6fa379'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def gather_code_context(*args, **kwargs):
    return _yaiwes_checkpoint('gather_code_context', kwargs)

class TargetRunner:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('TargetRunner.__init__', kwargs)
    def set_repo(self, *args, **kwargs):
        return _yaiwes_checkpoint('TargetRunner.set_repo', kwargs)
    def _get_context(self, *args, **kwargs):
        return _yaiwes_checkpoint('TargetRunner._get_context', kwargs)
    def _build_messages(self, *args, **kwargs):
        return _yaiwes_checkpoint('TargetRunner._build_messages', kwargs)
    async def respond_to_attack(self, *args, **kwargs):
        return _yaiwes_checkpoint('TargetRunner.respond_to_attack', kwargs)
