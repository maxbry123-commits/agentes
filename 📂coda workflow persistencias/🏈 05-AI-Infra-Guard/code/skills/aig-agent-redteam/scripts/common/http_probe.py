"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'c6140f16f0da7e8e712cfbb74a18daafc2dfc1cf77b91ecc3831a4f6a1f8fb4b'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def normalize_target(*args, **kwargs):
    return _yaiwes_checkpoint('normalize_target', kwargs)

def is_reachable(*args, **kwargs):
    return _yaiwes_checkpoint('is_reachable', kwargs)

def _make_session(*args, **kwargs):
    return _yaiwes_checkpoint('_make_session', kwargs)

def http_get(*args, **kwargs):
    return _yaiwes_checkpoint('http_get', kwargs)

def http_get_json(*args, **kwargs):
    return _yaiwes_checkpoint('http_get_json', kwargs)

class ProbeResult:
    def matched(self, *args, **kwargs):
        return _yaiwes_checkpoint('ProbeResult.matched', kwargs)
    def to_dict(self, *args, **kwargs):
        return _yaiwes_checkpoint('ProbeResult.to_dict', kwargs)
