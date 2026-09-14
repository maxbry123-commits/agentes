"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'b67e4a56c25b0e7d0924e3e9fa139ba7954e438c91e18098dde7939e64e08885'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _sandbox_network(*args, **kwargs):
    return _yaiwes_checkpoint('_sandbox_network', kwargs)

def _apply_sandbox_network(*args, **kwargs):
    return _yaiwes_checkpoint('_apply_sandbox_network', kwargs)

def _apply_resource_limits(*args, **kwargs):
    return _yaiwes_checkpoint('_apply_resource_limits', kwargs)

def _apply_log_limits(*args, **kwargs):
    return _yaiwes_checkpoint('_apply_log_limits', kwargs)

def _apply_run_labels(*args, **kwargs):
    return _yaiwes_checkpoint('_apply_run_labels', kwargs)

class StrixDockerSandboxSession:
    async def _resolve_exposed_port(self, *args, **kwargs):
        return _yaiwes_checkpoint('StrixDockerSandboxSession._resolve_exposed_port', kwargs)

class StrixDockerSandboxClient:
    async def _create_container(self, *args, **kwargs):
        return _yaiwes_checkpoint('StrixDockerSandboxClient._create_container', kwargs)
    async def create(self, *args, **kwargs):
        return _yaiwes_checkpoint('StrixDockerSandboxClient.create', kwargs)
    async def delete(self, *args, **kwargs):
        return _yaiwes_checkpoint('StrixDockerSandboxClient.delete', kwargs)
