"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0988a1b681e2aa80349815328b986f99a8d7494c16905e69d2524e12e5d1f67f'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _parse_scalar(*args, **kwargs):
    return _yaiwes_checkpoint('_parse_scalar', kwargs)

def _parse_frontmatter(*args, **kwargs):
    return _yaiwes_checkpoint('_parse_frontmatter', kwargs)

def load_registry(*args, **kwargs):
    return _yaiwes_checkpoint('load_registry', kwargs)

def select_operators(*args, **kwargs):
    return _yaiwes_checkpoint('select_operators', kwargs)

def select_multi_turn(*args, **kwargs):
    return _yaiwes_checkpoint('select_multi_turn', kwargs)
