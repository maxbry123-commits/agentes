"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'c7cf02c79e0fdfe15a42a2157c530eabf1d9b36eeb030e93eee080056237a54b'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

async def _do_start_kali(*args, **kwargs):
    return _yaiwes_checkpoint('_do_start_kali', kwargs)

async def _do_stop_kali(*args, **kwargs):
    return _yaiwes_checkpoint('_do_stop_kali', kwargs)

async def _do_start_metasploit(*args, **kwargs):
    return _yaiwes_checkpoint('_do_start_metasploit', kwargs)

async def _do_stop_metasploit(*args, **kwargs):
    return _yaiwes_checkpoint('_do_stop_metasploit', kwargs)

async def _do_start_mobsf(*args, **kwargs):
    return _yaiwes_checkpoint('_do_start_mobsf', kwargs)

async def _do_stop_mobsf(*args, **kwargs):
    return _yaiwes_checkpoint('_do_stop_mobsf', kwargs)

async def _do_pull_images(*args, **kwargs):
    return _yaiwes_checkpoint('_do_pull_images', kwargs)
