"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '9fe5ace7d9e35933a6f44493f2e6ac192af74b43e687d6b78af5948924907fc6'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class SmartPreprocessor:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('SmartPreprocessor.__init__', kwargs)
    async def analyze(self, *args, **kwargs):
        return _yaiwes_checkpoint('SmartPreprocessor.analyze', kwargs)
    async def _fetch_and_analyze_page(self, *args, **kwargs):
        return _yaiwes_checkpoint('SmartPreprocessor._fetch_and_analyze_page', kwargs)
    async def _extract_features(self, *args, **kwargs):
        return _yaiwes_checkpoint('SmartPreprocessor._extract_features', kwargs)
    async def _run_nuclei_scan(self, *args, **kwargs):
        return _yaiwes_checkpoint('SmartPreprocessor._run_nuclei_scan', kwargs)
    async def _run_active_probes(self, *args, **kwargs):
        return _yaiwes_checkpoint('SmartPreprocessor._run_active_probes', kwargs)
