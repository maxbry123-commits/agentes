"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '52282432c937da7d40b6d90181ff2be25afb7ae027d7a7f336e625712c3b6b61'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def configure(*args, **kwargs):
    return _yaiwes_checkpoint('configure', kwargs)

def app_url(*args, **kwargs):
    return _yaiwes_checkpoint('app_url', kwargs)

def api_token(*args, **kwargs):
    return _yaiwes_checkpoint('api_token', kwargs)

def _validate_stored_token_origin(*args, **kwargs):
    return _yaiwes_checkpoint('_validate_stored_token_origin', kwargs)

def request(*args, **kwargs):
    return _yaiwes_checkpoint('request', kwargs)

def expected_workspace_id(*args, **kwargs):
    return _yaiwes_checkpoint('expected_workspace_id', kwargs)

def upload_file(*args, **kwargs):
    return _yaiwes_checkpoint('upload_file', kwargs)

def _validate_upload_url(*args, **kwargs):
    return _yaiwes_checkpoint('_validate_upload_url', kwargs)

def _parse_origin_url(*args, **kwargs):
    return _yaiwes_checkpoint('_parse_origin_url', kwargs)

def _origin(*args, **kwargs):
    return _yaiwes_checkpoint('_origin', kwargs)

def _is_loopback_host(*args, **kwargs):
    return _yaiwes_checkpoint('_is_loopback_host', kwargs)

def parsed(*args, **kwargs):
    return _yaiwes_checkpoint('parsed', kwargs)

def check(*args, **kwargs):
    return _yaiwes_checkpoint('check', kwargs)

def topup_url(*args, **kwargs):
    return _yaiwes_checkpoint('topup_url', kwargs)

def topup_next_step(*args, **kwargs):
    return _yaiwes_checkpoint('topup_next_step', kwargs)

def payment_required_error(*args, **kwargs):
    return _yaiwes_checkpoint('payment_required_error', kwargs)

class CloudError:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('CloudError.__init__', kwargs)

class CloudTransportError:
    pass
