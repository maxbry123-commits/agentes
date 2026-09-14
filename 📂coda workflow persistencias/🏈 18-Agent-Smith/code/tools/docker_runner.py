"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '1e68f0faf4878e6e739ceb60b69dd5d80ee8cfcd5fd7c9de40605ef7cff78290'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

async def image_exists(*args, **kwargs):
    return _yaiwes_checkpoint('image_exists', kwargs)

async def _ensure_image(*args, **kwargs):
    return _yaiwes_checkpoint('_ensure_image', kwargs)

async def run_container(*args, **kwargs):
    return _yaiwes_checkpoint('run_container', kwargs)
