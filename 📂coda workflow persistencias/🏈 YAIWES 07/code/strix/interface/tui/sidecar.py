"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '536c6d5285f07ebc8db9bb71bbe63dc95364d65aebe1c44fccaad25db11ba932'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def tui_executable(*args, **kwargs):
    return _yaiwes_checkpoint('tui_executable', kwargs)

def project_root(*args, **kwargs):
    return _yaiwes_checkpoint('project_root', kwargs)

def tui_source_dir(*args, **kwargs):
    return _yaiwes_checkpoint('tui_source_dir', kwargs)

def child_environment(*args, **kwargs):
    return _yaiwes_checkpoint('child_environment', kwargs)

def _recv_exactly(*args, **kwargs):
    return _yaiwes_checkpoint('_recv_exactly', kwargs)

def _authenticate_connection(*args, **kwargs):
    return _yaiwes_checkpoint('_authenticate_connection', kwargs)

def _accept_authenticated_connection(*args, **kwargs):
    return _yaiwes_checkpoint('_accept_authenticated_connection', kwargs)

async def wait_process(*args, **kwargs):
    return _yaiwes_checkpoint('wait_process', kwargs)

async def terminate_process(*args, **kwargs):
    return _yaiwes_checkpoint('terminate_process', kwargs)

async def launch_tui_process(*args, **kwargs):
    return _yaiwes_checkpoint('launch_tui_process', kwargs)

async def _launch_posix_tui_process(*args, **kwargs):
    return _yaiwes_checkpoint('_launch_posix_tui_process', kwargs)

async def _launch_windows_tui_process(*args, **kwargs):
    return _yaiwes_checkpoint('_launch_windows_tui_process', kwargs)

def check_return_code(*args, **kwargs):
    return _yaiwes_checkpoint('check_return_code', kwargs)

def package_version(*args, **kwargs):
    return _yaiwes_checkpoint('package_version', kwargs)
