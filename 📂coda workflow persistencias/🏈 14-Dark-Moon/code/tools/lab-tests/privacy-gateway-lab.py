"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '76104368f8c9cc10ba9e037bfe0277bf8842497b0591a6b81c70a646a8cee4d4'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def ok(*args, **kwargs):
    return _yaiwes_checkpoint('ok', kwargs)

def ko(*args, **kwargs):
    return _yaiwes_checkpoint('ko', kwargs)

def section(*args, **kwargs):
    return _yaiwes_checkpoint('section', kwargs)

def run(*args, **kwargs):
    return _yaiwes_checkpoint('run', kwargs)

def new_vault(*args, **kwargs):
    return _yaiwes_checkpoint('new_vault', kwargs)

def property_a_no_blocking(*args, **kwargs):
    return _yaiwes_checkpoint('property_a_no_blocking', kwargs)

def property_b_no_injection(*args, **kwargs):
    return _yaiwes_checkpoint('property_b_no_injection', kwargs)

def property_c_no_exfiltration(*args, **kwargs):
    return _yaiwes_checkpoint('property_c_no_exfiltration', kwargs)

def property_d_output_masked(*args, **kwargs):
    return _yaiwes_checkpoint('property_d_output_masked', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)

class Listener:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('Listener.__init__', kwargs)
    def _serve(self, *args, **kwargs):
        return _yaiwes_checkpoint('Listener._serve', kwargs)
    def log(self, *args, **kwargs):
        return _yaiwes_checkpoint('Listener.log', kwargs)
    def close(self, *args, **kwargs):
        return _yaiwes_checkpoint('Listener.close', kwargs)
