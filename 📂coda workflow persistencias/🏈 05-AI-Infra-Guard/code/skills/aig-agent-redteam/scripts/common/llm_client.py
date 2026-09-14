"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'db79a8153ab897bc03e8aab40dd4fa27334830b86a1bea988b1720f0cbd71732'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class LLMResponse:
    def ok(self, *args, **kwargs):
        return _yaiwes_checkpoint('LLMResponse.ok', kwargs)

class LLMClient:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('LLMClient.__init__', kwargs)
    def from_env(self, *args, **kwargs):
        return _yaiwes_checkpoint('LLMClient.from_env', kwargs)
    def chat(self, *args, **kwargs):
        return _yaiwes_checkpoint('LLMClient.chat', kwargs)
    def chat_with_history(self, *args, **kwargs):
        return _yaiwes_checkpoint('LLMClient.chat_with_history', kwargs)
    def _call(self, *args, **kwargs):
        return _yaiwes_checkpoint('LLMClient._call', kwargs)
    def list_models(self, *args, **kwargs):
        return _yaiwes_checkpoint('LLMClient.list_models', kwargs)
