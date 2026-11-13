"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '94941e43e7b0abe7fa68ca72664fe98c93d3d99a1d4ac16265682f6877ef2268'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _get_local_ips(*args, **kwargs):
    return _yaiwes_checkpoint('_get_local_ips', kwargs)

def _accept_loop(*args, **kwargs):
    return _yaiwes_checkpoint('_accept_loop', kwargs)

def _start_listener(*args, **kwargs):
    return _yaiwes_checkpoint('_start_listener', kwargs)

def _stop_listener(*args, **kwargs):
    return _yaiwes_checkpoint('_stop_listener', kwargs)

def _disconnect_client(*args, **kwargs):
    return _yaiwes_checkpoint('_disconnect_client', kwargs)

def _status(*args, **kwargs):
    return _yaiwes_checkpoint('_status', kwargs)

def _send_command_blocking(*args, **kwargs):
    return _yaiwes_checkpoint('_send_command_blocking', kwargs)

def reverse_shell_start_listener(*args, **kwargs):
    return _yaiwes_checkpoint('reverse_shell_start_listener', kwargs)

def reverse_shell_stop_listener(*args, **kwargs):
    return _yaiwes_checkpoint('reverse_shell_stop_listener', kwargs)

def reverse_shell_status(*args, **kwargs):
    return _yaiwes_checkpoint('reverse_shell_status', kwargs)

async def reverse_shell_send_command(*args, **kwargs):
    return _yaiwes_checkpoint('reverse_shell_send_command', kwargs)

def reverse_shell_disconnect(*args, **kwargs):
    return _yaiwes_checkpoint('reverse_shell_disconnect', kwargs)
