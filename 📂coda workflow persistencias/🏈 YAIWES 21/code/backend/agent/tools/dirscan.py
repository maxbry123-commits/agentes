"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '4d3287fbe35b626495e6cefa49f13d9d6417942f9a13a89a04029ca9e779dcf2'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class DirectoryScanner:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('DirectoryScanner.__init__', kwargs)
    def get_parameters(self, *args, **kwargs):
        return _yaiwes_checkpoint('DirectoryScanner.get_parameters', kwargs)
    async def initialize(self, *args, **kwargs):
        return _yaiwes_checkpoint('DirectoryScanner.initialize', kwargs)
    async def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('DirectoryScanner.execute', kwargs)
    async def cleanup(self, *args, **kwargs):
        return _yaiwes_checkpoint('DirectoryScanner.cleanup', kwargs)
    def to_openai_tool(self, *args, **kwargs):
        return _yaiwes_checkpoint('DirectoryScanner.to_openai_tool', kwargs)
