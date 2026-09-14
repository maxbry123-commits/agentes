"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '49595f3d67841f25e0bf21dcf1648af6ac578d0d6def52b0e495d20db2d23e4f'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class NgrokError:
    pass

class NgrokManager:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('NgrokManager.__init__', kwargs)
    async def open(self, *args, **kwargs):
        return _yaiwes_checkpoint('NgrokManager.open', kwargs)
    async def close(self, *args, **kwargs):
        return _yaiwes_checkpoint('NgrokManager.close', kwargs)
    async def close_all(self, *args, **kwargs):
        return _yaiwes_checkpoint('NgrokManager.close_all', kwargs)
    async def _read_public_url(self, *args, **kwargs):
        return _yaiwes_checkpoint('NgrokManager._read_public_url', kwargs)
