"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '52e5aa77fd9c98fc0375a33b49552124c4d455dbfdb3b4011305bc14a40545ca'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

async def probe_server(*args, **kwargs):
    return _yaiwes_checkpoint('probe_server', kwargs)

async def probe_proxy(*args, **kwargs):
    return _yaiwes_checkpoint('probe_proxy', kwargs)

def _parse(*args, **kwargs):
    return _yaiwes_checkpoint('_parse', kwargs)
