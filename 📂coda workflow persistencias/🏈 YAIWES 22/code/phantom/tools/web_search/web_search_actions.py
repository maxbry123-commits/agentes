"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'c2e6d868ed64f1436f6a38dfb7939a274daf3d7394ca05b8cb109e7e22127466'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _duckduckgo_search_fallback(*args, **kwargs):
    return _yaiwes_checkpoint('_duckduckgo_search_fallback', kwargs)

def _search_cve_fallback(*args, **kwargs):
    return _yaiwes_checkpoint('_search_cve_fallback', kwargs)

def _smart_search_router(*args, **kwargs):
    return _yaiwes_checkpoint('_smart_search_router', kwargs)

async def web_search(*args, **kwargs):
    return _yaiwes_checkpoint('web_search', kwargs)
