"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '9340a47095456f19689fa6e7ef82fa181c9baee63ae54f5289d57b80c506be66'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def looks_like_url(*args, **kwargs):
    return _yaiwes_checkpoint('looks_like_url', kwargs)

def extract_url_from_text(*args, **kwargs):
    return _yaiwes_checkpoint('extract_url_from_text', kwargs)

def looks_like_github(*args, **kwargs):
    return _yaiwes_checkpoint('looks_like_github', kwargs)

def looks_like_local_path(*args, **kwargs):
    return _yaiwes_checkpoint('looks_like_local_path', kwargs)

def looks_like_yaml(*args, **kwargs):
    return _yaiwes_checkpoint('looks_like_yaml', kwargs)

def detect_yaml_kind(*args, **kwargs):
    return _yaiwes_checkpoint('detect_yaml_kind', kwargs)

def probe_http_service(*args, **kwargs):
    return _yaiwes_checkpoint('probe_http_service', kwargs)

def looks_like_self_target(*args, **kwargs):
    return _yaiwes_checkpoint('looks_like_self_target', kwargs)

def detect_repo_kind(*args, **kwargs):
    return _yaiwes_checkpoint('detect_repo_kind', kwargs)

def build_profile(*args, **kwargs):
    return _yaiwes_checkpoint('build_profile', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)
