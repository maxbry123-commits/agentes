"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '96130830fd002cbc5f14446fbfba6e08af7c2f11a1481267d8c8e34d0604bfe8'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _client_with_response(*args, **kwargs):
    return _yaiwes_checkpoint('_client_with_response', kwargs)

def test_redteam_requests_omit_temperature(*args, **kwargs):
    return _yaiwes_checkpoint('test_redteam_requests_omit_temperature', kwargs)
