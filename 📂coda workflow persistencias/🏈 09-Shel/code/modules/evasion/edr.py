"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'e6b15c3e9f0298802b1820ae1346935d8c7fd460d960791b3628b21b5a196a91'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class EDREvasion:
    def amsi_bypass(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion.amsi_bypass', kwargs)
    def _amsi_memory_patch(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._amsi_memory_patch', kwargs)
    def _amsi_registry(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._amsi_registry', kwargs)
    def _amsi_reflection(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._amsi_reflection', kwargs)
    def etw_bypass(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion.etw_bypass', kwargs)
    def sandbox_detect(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion.sandbox_detect', kwargs)
    def process_injection(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion.process_injection', kwargs)
    def _shellcode_stub(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._shellcode_stub', kwargs)
    def _create_remote_thread(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._create_remote_thread', kwargs)
    def _apc_injection(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._apc_injection', kwargs)
    def _process_hollowing(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion._process_hollowing', kwargs)
    def get_techniques(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion.get_techniques', kwargs)
    def all_bypasses(self, *args, **kwargs):
        return _yaiwes_checkpoint('EDREvasion.all_bypasses', kwargs)
