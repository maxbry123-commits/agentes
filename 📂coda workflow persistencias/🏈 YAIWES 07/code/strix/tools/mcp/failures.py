"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '2ed5b3a1308cc6e6d431607ff7acd8a8cdb52c632a5b85cf8c97d7d8663a11cc'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _retry_after(*args, **kwargs):
    return _yaiwes_checkpoint('_retry_after', kwargs)

def _from_status(*args, **kwargs):
    return _yaiwes_checkpoint('_from_status', kwargs)

def _direct(*args, **kwargs):
    return _yaiwes_checkpoint('_direct', kwargs)

def classify(*args, **kwargs):
    return _yaiwes_checkpoint('classify', kwargs)

class FailureInfo:
    def retryable(self, *args, **kwargs):
        return _yaiwes_checkpoint('FailureInfo.retryable', kwargs)

class HttpStatusRecorder:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('HttpStatusRecorder.__init__', kwargs)
    async def __call__(self, *args, **kwargs):
        return _yaiwes_checkpoint('HttpStatusRecorder.__call__', kwargs)
    def take(self, *args, **kwargs):
        return _yaiwes_checkpoint('HttpStatusRecorder.take', kwargs)
