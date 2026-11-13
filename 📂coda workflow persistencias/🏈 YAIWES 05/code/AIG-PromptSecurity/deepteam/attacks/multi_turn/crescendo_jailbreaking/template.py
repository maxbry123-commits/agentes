"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0c04ad001298064f0645e714b8d91babc33c3b2378758661c605f312d88dd0b1'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class JailBreakingCrescendoTemplate:
    def crescendo_system_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingCrescendoTemplate.crescendo_system_prompt', kwargs)
    def attack_json_confinement(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingCrescendoTemplate.attack_json_confinement', kwargs)
    def refusal_system_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingCrescendoTemplate.refusal_system_prompt', kwargs)
    def eval_system_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingCrescendoTemplate.eval_system_prompt', kwargs)
