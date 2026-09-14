"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0c2df2313cca06750795be56013c5f5cdd7a8d8d6e2d1ec4ceaf981dd02f4fa4'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class JailBreakingTemplate:
    def enhance_attack(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingTemplate.enhance_attack', kwargs)
    def on_topic(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingTemplate.on_topic', kwargs)
    def non_refusal(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingTemplate.non_refusal', kwargs)
    def linear_judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingTemplate.linear_judge', kwargs)
    def tree_judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('JailBreakingTemplate.tree_judge', kwargs)
