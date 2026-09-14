"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '16c3ed20e2b51d1fdf82759d88812729ae6b6d5e09df5def4ae0584bad943234'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _connected_client_candidates(*args, **kwargs):
    return _yaiwes_checkpoint('_connected_client_candidates', kwargs)

def _detect_smith_caller(*args, **kwargs):
    return _yaiwes_checkpoint('_detect_smith_caller', kwargs)

def _connected_pids(*args, **kwargs):
    return _yaiwes_checkpoint('_connected_pids', kwargs)

def _resolve_client_for_pid(*args, **kwargs):
    return _yaiwes_checkpoint('_resolve_client_for_pid', kwargs)

def _persist_smith_caller(*args, **kwargs):
    return _yaiwes_checkpoint('_persist_smith_caller', kwargs)
