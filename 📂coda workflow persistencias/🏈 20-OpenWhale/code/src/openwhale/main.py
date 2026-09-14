"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '62f9cca38c8445d6ea7a9abc585ac595818fb7d820b7cb564068dda7115fd287'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _pick_available_port(*args, **kwargs):
    return _yaiwes_checkpoint('_pick_available_port', kwargs)

def _banner(*args, **kwargs):
    return _yaiwes_checkpoint('_banner', kwargs)

def _load_config(*args, **kwargs):
    return _yaiwes_checkpoint('_load_config', kwargs)

async def _run_agent(*args, **kwargs):
    return _yaiwes_checkpoint('_run_agent', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)
