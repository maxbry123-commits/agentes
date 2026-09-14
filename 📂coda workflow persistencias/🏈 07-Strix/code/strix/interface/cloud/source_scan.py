"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0d9daef9d88d9bde06fd96552b57d3ee33e443323d6fe8fa5434ee71368db68a'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def prepare_scan_source(*args, **kwargs):
    return _yaiwes_checkpoint('prepare_scan_source', kwargs)

def _validate_source_digest_approval(*args, **kwargs):
    return _yaiwes_checkpoint('_validate_source_digest_approval', kwargs)

def _source_approval_error(*args, **kwargs):
    return _yaiwes_checkpoint('_source_approval_error', kwargs)

def _upload_scan_source(*args, **kwargs):
    return _yaiwes_checkpoint('_upload_scan_source', kwargs)

def _validate_completed_upload(*args, **kwargs):
    return _yaiwes_checkpoint('_validate_completed_upload', kwargs)

def _delete_upload(*args, **kwargs):
    return _yaiwes_checkpoint('_delete_upload', kwargs)

def _source_cleanup_note(*args, **kwargs):
    return _yaiwes_checkpoint('_source_cleanup_note', kwargs)

def _source_cleanup_error(*args, **kwargs):
    return _yaiwes_checkpoint('_source_cleanup_error', kwargs)

def _interrupted_source_upload_error(*args, **kwargs):
    return _yaiwes_checkpoint('_interrupted_source_upload_error', kwargs)

def _retained_source_upload_error(*args, **kwargs):
    return _yaiwes_checkpoint('_retained_source_upload_error', kwargs)

def _idempotency_retry_note(*args, **kwargs):
    return _yaiwes_checkpoint('_idempotency_retry_note', kwargs)

def _attach_idempotency_recovery(*args, **kwargs):
    return _yaiwes_checkpoint('_attach_idempotency_recovery', kwargs)

def _format_bytes(*args, **kwargs):
    return _yaiwes_checkpoint('_format_bytes', kwargs)

class LocalSourceScan:
    def prepare_and_attach(self, *args, **kwargs):
        return _yaiwes_checkpoint('LocalSourceScan.prepare_and_attach', kwargs)
    def mark_launch_started(self, *args, **kwargs):
        return _yaiwes_checkpoint('LocalSourceScan.mark_launch_started', kwargs)
    def handle_request_failure(self, *args, **kwargs):
        return _yaiwes_checkpoint('LocalSourceScan.handle_request_failure', kwargs)
    def handle_response_failure(self, *args, **kwargs):
        return _yaiwes_checkpoint('LocalSourceScan.handle_response_failure', kwargs)
    def wrap_result(self, *args, **kwargs):
        return _yaiwes_checkpoint('LocalSourceScan.wrap_result', kwargs)
    def close(self, *args, **kwargs):
        return _yaiwes_checkpoint('LocalSourceScan.close', kwargs)
