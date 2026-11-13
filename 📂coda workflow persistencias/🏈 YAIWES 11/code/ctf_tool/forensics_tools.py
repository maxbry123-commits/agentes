"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'cf0b633521faa473d57aa49dee264166c5ee13382b96d9a293cd92c046e212d2'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _pcap_analyze(*args, **kwargs):
    return _yaiwes_checkpoint('_pcap_analyze', kwargs)

def _pcap_extract_objects(*args, **kwargs):
    return _yaiwes_checkpoint('_pcap_extract_objects', kwargs)

def _carve_files(*args, **kwargs):
    return _yaiwes_checkpoint('_carve_files', kwargs)

def _hex_dump(*args, **kwargs):
    return _yaiwes_checkpoint('_hex_dump', kwargs)

def _hex_search(*args, **kwargs):
    return _yaiwes_checkpoint('_hex_search', kwargs)

class ForensicsTool:
    def tags(self, *args, **kwargs):
        return _yaiwes_checkpoint('ForensicsTool.tags', kwargs)
    def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('ForensicsTool.execute', kwargs)
    def function_config(self, *args, **kwargs):
        return _yaiwes_checkpoint('ForensicsTool.function_config', kwargs)
