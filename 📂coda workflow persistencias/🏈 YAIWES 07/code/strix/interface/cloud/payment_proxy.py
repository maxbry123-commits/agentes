"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '19b280ae0bbb2cc8410c93da3b507d10e469a563e0a38c455e1c9112058fd764'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _bounded_response_body(*args, **kwargs):
    return _yaiwes_checkpoint('_bounded_response_body', kwargs)

def _connection_header_names(*args, **kwargs):
    return _yaiwes_checkpoint('_connection_header_names', kwargs)

def _forward_request_headers(*args, **kwargs):
    return _yaiwes_checkpoint('_forward_request_headers', kwargs)

def _send_json_error(*args, **kwargs):
    return _yaiwes_checkpoint('_send_json_error', kwargs)

def _make_handler(*args, **kwargs):
    return _yaiwes_checkpoint('_make_handler', kwargs)

def wallet_payment_bridge(*args, **kwargs):
    return _yaiwes_checkpoint('wallet_payment_bridge', kwargs)

class _BridgeState:
    def claim_request(self, *args, **kwargs):
        return _yaiwes_checkpoint('_BridgeState.claim_request', kwargs)

class _ResponseTooLargeError:
    pass

class WalletUpstreamResponse:
    pass
