"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0d047e31219c6af812aa3142abd23caa79f6a50f0de51cc7b5cb404bc8379563'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _build_probe_script(*args, **kwargs):
    return _yaiwes_checkpoint('_build_probe_script', kwargs)

def _parse_probe_output(*args, **kwargs):
    return _yaiwes_checkpoint('_parse_probe_output', kwargs)

def probe_environment(*args, **kwargs):
    return _yaiwes_checkpoint('probe_environment', kwargs)

def detect_new_installations(*args, **kwargs):
    return _yaiwes_checkpoint('detect_new_installations', kwargs)

def format_env_context(*args, **kwargs):
    return _yaiwes_checkpoint('format_env_context', kwargs)
