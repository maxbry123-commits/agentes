"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '50f69024aff9956e99ee945baa9c14a9e47e60c522cfc386a7d0660c6a45886a'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def read_request(*args, **kwargs):
    return _yaiwes_checkpoint('read_request', kwargs)

def validate_text(*args, **kwargs):
    return _yaiwes_checkpoint('validate_text', kwargs)

def validate_header_value(*args, **kwargs):
    return _yaiwes_checkpoint('validate_header_value', kwargs)

def validate_context(*args, **kwargs):
    return _yaiwes_checkpoint('validate_context', kwargs)

def validate_headers(*args, **kwargs):
    return _yaiwes_checkpoint('validate_headers', kwargs)

def replay(*args, **kwargs):
    return _yaiwes_checkpoint('replay', kwargs)

def validate_route_target(*args, **kwargs):
    return _yaiwes_checkpoint('validate_route_target', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)
