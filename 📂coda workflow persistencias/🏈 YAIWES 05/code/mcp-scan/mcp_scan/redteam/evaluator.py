"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'ff05ad6e8c8e5e7b3910e43c92063ed77096ba48af632c7207da887ed716ba8d'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _parse_eval_json(*args, **kwargs):
    return _yaiwes_checkpoint('_parse_eval_json', kwargs)

class EvaluatorAgent:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('EvaluatorAgent.__init__', kwargs)
    def _build_messages(self, *args, **kwargs):
        return _yaiwes_checkpoint('EvaluatorAgent._build_messages', kwargs)
    async def evaluate(self, *args, **kwargs):
        return _yaiwes_checkpoint('EvaluatorAgent.evaluate', kwargs)
