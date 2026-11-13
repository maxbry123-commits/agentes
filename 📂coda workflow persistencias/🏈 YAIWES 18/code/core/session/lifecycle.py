"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0feada44faa6845342164992084c97874a664593f77967ea072fd7f909fa5a6e'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _parse_lhost(*args, **kwargs):
    return _yaiwes_checkpoint('_parse_lhost', kwargs)

def start(*args, **kwargs):
    return _yaiwes_checkpoint('start', kwargs)

def stop_pentest_containers(*args, **kwargs):
    return _yaiwes_checkpoint('stop_pentest_containers', kwargs)

def snapshot_training_bundle(*args, **kwargs):
    return _yaiwes_checkpoint('snapshot_training_bundle', kwargs)

def complete(*args, **kwargs):
    return _yaiwes_checkpoint('complete', kwargs)

def set_triage_requested(*args, **kwargs):
    return _yaiwes_checkpoint('set_triage_requested', kwargs)

def note_triage_progress(*args, **kwargs):
    return _yaiwes_checkpoint('note_triage_progress', kwargs)

def get(*args, **kwargs):
    return _yaiwes_checkpoint('get', kwargs)

def load_from_disk(*args, **kwargs):
    return _yaiwes_checkpoint('load_from_disk', kwargs)
