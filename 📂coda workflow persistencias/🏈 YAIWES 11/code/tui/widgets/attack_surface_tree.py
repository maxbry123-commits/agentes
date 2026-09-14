"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'ade5cff3ed279587450f14f19b68f12a4f75459088a6af87fce219b0cec70a37'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class AttackSurfaceTree:
    def on_mount(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackSurfaceTree.on_mount', kwargs)
    def update_from_attack_surface(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackSurfaceTree.update_from_attack_surface', kwargs)
