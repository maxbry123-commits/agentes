"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'd119da9af1fa15f97f080c785a3eaa934399224afb9ea578714d53c0b63e8a9d'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def seed_cmd(*args, **kwargs):
    return _yaiwes_checkpoint('seed_cmd', kwargs)

def db_upgrade(*args, **kwargs):
    return _yaiwes_checkpoint('db_upgrade', kwargs)

def db_downgrade(*args, **kwargs):
    return _yaiwes_checkpoint('db_downgrade', kwargs)
