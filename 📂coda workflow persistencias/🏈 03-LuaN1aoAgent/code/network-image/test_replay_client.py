"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'fc013433b8780cc5032bb75110d31a49928eba4e978dfee8dd008f3ca6b8438a'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class FakeResponse:
    def __enter__(self, *args, **kwargs):
        return _yaiwes_checkpoint('FakeResponse.__enter__', kwargs)
    def __exit__(self, *args, **kwargs):
        return _yaiwes_checkpoint('FakeResponse.__exit__', kwargs)
    def iter_bytes(self, *args, **kwargs):
        return _yaiwes_checkpoint('FakeResponse.iter_bytes', kwargs)

class FakeClient:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('FakeClient.__init__', kwargs)
    def __enter__(self, *args, **kwargs):
        return _yaiwes_checkpoint('FakeClient.__enter__', kwargs)
    def __exit__(self, *args, **kwargs):
        return _yaiwes_checkpoint('FakeClient.__exit__', kwargs)
    def stream(self, *args, **kwargs):
        return _yaiwes_checkpoint('FakeClient.stream', kwargs)

class ReplayClientTest:
    def test_request_uses_out_of_band_context_without_internal_header(self, *args, **kwargs):
        return _yaiwes_checkpoint('ReplayClientTest.test_request_uses_out_of_band_context_without_internal_header', kwargs)
    def test_routed_replay_rejects_a_target_outside_original_cidrs(self, *args, **kwargs):
        return _yaiwes_checkpoint('ReplayClientTest.test_routed_replay_rejects_a_target_outside_original_cidrs', kwargs)
    def test_routed_replay_rejects_mixed_inside_and_outside_addresses(self, *args, **kwargs):
        return _yaiwes_checkpoint('ReplayClientTest.test_routed_replay_rejects_mixed_inside_and_outside_addresses', kwargs)
    def test_old_context_header_is_not_control_metadata(self, *args, **kwargs):
        return _yaiwes_checkpoint('ReplayClientTest.test_old_context_header_is_not_control_metadata', kwargs)
