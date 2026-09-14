"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '20315490d23a1e22e0836ffae1a1a799a7ccb2b555579721bd6106e3ec0b3e8a'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def severity_to_label(*args, **kwargs):
    return _yaiwes_checkpoint('severity_to_label', kwargs)

def run(*args, **kwargs):
    return _yaiwes_checkpoint('run', kwargs)

def resolve_data_dirs(*args, **kwargs):
    return _yaiwes_checkpoint('resolve_data_dirs', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)
