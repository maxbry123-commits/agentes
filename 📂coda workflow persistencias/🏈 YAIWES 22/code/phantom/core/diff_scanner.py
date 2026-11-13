"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '3e1415b43962d19f3b47cfa4238a75270b46d1a992f83244e339bd40870d4c64'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _load_vulns(*args, **kwargs):
    return _yaiwes_checkpoint('_load_vulns', kwargs)

def _vuln_key(*args, **kwargs):
    return _yaiwes_checkpoint('_vuln_key', kwargs)

class DiffReport:
    def _sev_badge(self, *args, **kwargs):
        return _yaiwes_checkpoint('DiffReport._sev_badge', kwargs)
    def _vuln_summary(self, *args, **kwargs):
        return _yaiwes_checkpoint('DiffReport._vuln_summary', kwargs)
    def to_markdown(self, *args, **kwargs):
        return _yaiwes_checkpoint('DiffReport.to_markdown', kwargs)
    def __str__(self, *args, **kwargs):
        return _yaiwes_checkpoint('DiffReport.__str__', kwargs)

class DiffScanner:
    def compare(self, *args, **kwargs):
        return _yaiwes_checkpoint('DiffScanner.compare', kwargs)
