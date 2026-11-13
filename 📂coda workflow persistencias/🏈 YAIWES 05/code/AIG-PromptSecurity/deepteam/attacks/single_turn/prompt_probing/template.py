"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '4e1a6b91bb2ae120383e22eee7ad3c2aad1b080a684e2dd6837f1013888450be'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class PromptProbingTemplate:
    def enhance(self, *args, **kwargs):
        return _yaiwes_checkpoint('PromptProbingTemplate.enhance', kwargs)
    def non_compliant(self, *args, **kwargs):
        return _yaiwes_checkpoint('PromptProbingTemplate.non_compliant', kwargs)
    def is_prompt_probing(self, *args, **kwargs):
        return _yaiwes_checkpoint('PromptProbingTemplate.is_prompt_probing', kwargs)
