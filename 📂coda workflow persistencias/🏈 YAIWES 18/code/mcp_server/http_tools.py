"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'b009ba34bec598cd22a5eb5e7eef8186257532d5ae3ef4aa13f03c93cf5ab6bc'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _write_text(*args, **kwargs):
    return _yaiwes_checkpoint('_write_text', kwargs)

async def http(*args, **kwargs):
    return _yaiwes_checkpoint('http', kwargs)

async def http_probe(*args, **kwargs):
    return _yaiwes_checkpoint('http_probe', kwargs)

async def _do_request(*args, **kwargs):
    return _yaiwes_checkpoint('_do_request', kwargs)

async def _do_save_poc(*args, **kwargs):
    return _yaiwes_checkpoint('_do_save_poc', kwargs)
