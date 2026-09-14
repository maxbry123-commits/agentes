"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '821c4efa3fee5ecebdf26b4c918ad900543c6cb7a75cdf2e948f024fff4939dd'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def load_rows(*args, **kwargs):
    return _yaiwes_checkpoint('load_rows', kwargs)

def validate_row(*args, **kwargs):
    return _yaiwes_checkpoint('validate_row', kwargs)

def aggregate(*args, **kwargs):
    return _yaiwes_checkpoint('aggregate', kwargs)

def _count(*args, **kwargs):
    return _yaiwes_checkpoint('_count', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)
