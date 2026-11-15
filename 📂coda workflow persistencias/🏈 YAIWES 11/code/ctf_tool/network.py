"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'fb696e888ef188696116b2a819629b5ebb7f59718d9540273a833e0e7f58c1ca'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _http_request(*args, **kwargs):
    return _yaiwes_checkpoint('_http_request', kwargs)

def _dns_lookup(*args, **kwargs):
    return _yaiwes_checkpoint('_dns_lookup', kwargs)

def _tcp_port_check(*args, **kwargs):
    return _yaiwes_checkpoint('_tcp_port_check', kwargs)

def _dir_bruteforce(*args, **kwargs):
    return _yaiwes_checkpoint('_dir_bruteforce', kwargs)

class NetworkTool:
    def tags(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkTool.tags', kwargs)
    def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkTool.execute', kwargs)
    def function_config(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkTool.function_config', kwargs)
