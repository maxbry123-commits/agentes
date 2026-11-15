"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '942fa337078d29d31c3b123a60516b41822a68649dc05a12ca8e81605e74dd9e'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

async def get_or_create_demo_project(*args, **kwargs):
    return _yaiwes_checkpoint('get_or_create_demo_project', kwargs)

async def create_agent_demo_task(*args, **kwargs):
    return _yaiwes_checkpoint('create_agent_demo_task', kwargs)

async def create_agent_events(*args, **kwargs):
    return _yaiwes_checkpoint('create_agent_events', kwargs)

async def create_agent_findings(*args, **kwargs):
    return _yaiwes_checkpoint('create_agent_findings', kwargs)

async def create_agent_tree_nodes(*args, **kwargs):
    return _yaiwes_checkpoint('create_agent_tree_nodes', kwargs)

async def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)
