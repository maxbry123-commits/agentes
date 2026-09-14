"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '568470d013cd12e4f388206520da39ab9a4e4c3c6b95846cbc281abc1ba3c959'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def get_github_contents(*args, **kwargs):
    return _yaiwes_checkpoint('get_github_contents', kwargs)

def create_github_pr(*args, **kwargs):
    return _yaiwes_checkpoint('create_github_pr', kwargs)

def call_agent(*args, **kwargs):
    return _yaiwes_checkpoint('call_agent', kwargs)

def run_red_team(*args, **kwargs):
    return _yaiwes_checkpoint('run_red_team', kwargs)
