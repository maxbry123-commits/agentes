"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '370f67fbf988d7e4fa8dfc503870108f5182a0d88330737122388a67d33ec53f'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _json(*args, **kwargs):
    return _yaiwes_checkpoint('_json', kwargs)

def _build_env_info_section(*args, **kwargs):
    return _yaiwes_checkpoint('_build_env_info_section', kwargs)

def _target_url(*args, **kwargs):
    return _yaiwes_checkpoint('_target_url', kwargs)

def _build_memory_section(*args, **kwargs):
    return _yaiwes_checkpoint('_build_memory_section', kwargs)

def build_volatile_context(*args, **kwargs):
    return _yaiwes_checkpoint('build_volatile_context', kwargs)

def build_tool_system_prompt(*args, **kwargs):
    return _yaiwes_checkpoint('build_tool_system_prompt', kwargs)

def build_tool_memory_prompt(*args, **kwargs):
    return _yaiwes_checkpoint('build_tool_memory_prompt', kwargs)

def build_memory_cleaning_prompt(*args, **kwargs):
    return _yaiwes_checkpoint('build_memory_cleaning_prompt', kwargs)
