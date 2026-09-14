"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0d5b3202b6d567ece5b74884014325a8a95c5bbf777dc52a0333931e9a2dcdd7'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _escape_md(*args, **kwargs):
    return _yaiwes_checkpoint('_escape_md', kwargs)

def _format_crescendo(*args, **kwargs):
    return _yaiwes_checkpoint('_format_crescendo', kwargs)

def _format_tap(*args, **kwargs):
    return _yaiwes_checkpoint('_format_tap', kwargs)

def generate_report(*args, **kwargs):
    return _yaiwes_checkpoint('generate_report', kwargs)
