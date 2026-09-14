"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'cc5108016300941a98b16c279b0f4c80ec4883ef59d63b016e407ad3547bc3a1'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class BenchmarkResult:
    def __post_init__(self, *args, **kwargs):
        return _yaiwes_checkpoint('BenchmarkResult.__post_init__', kwargs)

class BenchmarkHarness:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('BenchmarkHarness.__init__', kwargs)
    def run_challenge(self, *args, **kwargs):
        return _yaiwes_checkpoint('BenchmarkHarness.run_challenge', kwargs)
    def _save(self, *args, **kwargs):
        return _yaiwes_checkpoint('BenchmarkHarness._save', kwargs)
    def load(self, *args, **kwargs):
        return _yaiwes_checkpoint('BenchmarkHarness.load', kwargs)
    def summary(self, *args, **kwargs):
        return _yaiwes_checkpoint('BenchmarkHarness.summary', kwargs)
