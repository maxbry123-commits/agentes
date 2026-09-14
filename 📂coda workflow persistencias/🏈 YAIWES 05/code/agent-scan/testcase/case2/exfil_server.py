"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'faae46cdf448561fe6e24b334f6d3da8c62b04910e965376b336bdb4a7bcc95b'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def log_request(*args, **kwargs):
    return _yaiwes_checkpoint('log_request', kwargs)

def is_ai_agent(*args, **kwargs):
    return _yaiwes_checkpoint('is_ai_agent', kwargs)

def build_injection_page(*args, **kwargs):
    return _yaiwes_checkpoint('build_injection_page', kwargs)

def build_normal_page(*args, **kwargs):
    return _yaiwes_checkpoint('build_normal_page', kwargs)

def build_letter_page(*args, **kwargs):
    return _yaiwes_checkpoint('build_letter_page', kwargs)

def run_server(*args, **kwargs):
    return _yaiwes_checkpoint('run_server', kwargs)

class ExfilHandler:
    def do_GET(self, *args, **kwargs):
        return _yaiwes_checkpoint('ExfilHandler.do_GET', kwargs)
    def _send_html(self, *args, **kwargs):
        return _yaiwes_checkpoint('ExfilHandler._send_html', kwargs)
    def _send_json(self, *args, **kwargs):
        return _yaiwes_checkpoint('ExfilHandler._send_json', kwargs)
    def log_message(self, *args, **kwargs):
        return _yaiwes_checkpoint('ExfilHandler.log_message', kwargs)
