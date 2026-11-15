"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '65308b6c7cad6cf4a8ba421aa7f5a295c24914e3de26e263c675e9fbb42c63f0'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _kali_token(*args, **kwargs):
    return _yaiwes_checkpoint('_kali_token', kwargs)

async def image_exists(*args, **kwargs):
    return _yaiwes_checkpoint('image_exists', kwargs)

async def container_running(*args, **kwargs):
    return _yaiwes_checkpoint('container_running', kwargs)

def _forward_ai_keys(*args, **kwargs):
    return _yaiwes_checkpoint('_forward_ai_keys', kwargs)

async def ensure_running(*args, **kwargs):
    return _yaiwes_checkpoint('ensure_running', kwargs)

async def _seed_curl_defaults(*args, **kwargs):
    return _yaiwes_checkpoint('_seed_curl_defaults', kwargs)

async def stop(*args, **kwargs):
    return _yaiwes_checkpoint('stop', kwargs)

def _host_rewrite(*args, **kwargs):
    return _yaiwes_checkpoint('_host_rewrite', kwargs)

def _force_bash(*args, **kwargs):
    return _yaiwes_checkpoint('_force_bash', kwargs)

async def exec_command(*args, **kwargs):
    return _yaiwes_checkpoint('exec_command', kwargs)
