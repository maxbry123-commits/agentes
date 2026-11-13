"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '763bba9af4306c92ceaec3db500aa569d561c85aebbf198942b167587a2d0016'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class CustomPrompt:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('CustomPrompt.__init__', kwargs)
    def _load_prompts(self, *args, **kwargs):
        return _yaiwes_checkpoint('CustomPrompt._load_prompts', kwargs)
    def _load_from_file(self, *args, **kwargs):
        return _yaiwes_checkpoint('CustomPrompt._load_from_file', kwargs)
    def _parse_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('CustomPrompt._parse_prompt', kwargs)
    def get_prompts(self, *args, **kwargs):
        return _yaiwes_checkpoint('CustomPrompt.get_prompts', kwargs)
    def get_custom_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('CustomPrompt.get_custom_prompt', kwargs)
