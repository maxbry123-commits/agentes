"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'e443d95cc694f6f6c74a596d82beeafb51010aa15a3fdb108b5debcfdb867c41'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def extract_result(*args, **kwargs):
    return _yaiwes_checkpoint('extract_result', kwargs)

class VulnerabilityExtractor:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('VulnerabilityExtractor.__init__', kwargs)
    def extract_vulnerabilities(self, *args, **kwargs):
        return _yaiwes_checkpoint('VulnerabilityExtractor.extract_vulnerabilities', kwargs)
    def _parse_vuln_block(self, *args, **kwargs):
        return _yaiwes_checkpoint('VulnerabilityExtractor._parse_vuln_block', kwargs)
    def _extract_tag_content(self, *args, **kwargs):
        return _yaiwes_checkpoint('VulnerabilityExtractor._extract_tag_content', kwargs)
