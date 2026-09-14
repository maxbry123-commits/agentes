"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '6e04469b9614cf5d40e948530852cd6e778ba9b04be4923c4d13aab3171b5855'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def url_encode(*args, **kwargs):
    return _yaiwes_checkpoint('url_encode', kwargs)

class CloudMetadataSkill:
    def can_handle(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill.can_handle', kwargs)
    async def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill.execute', kwargs)
    async def _test_cloud_ssrf(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill._test_cloud_ssrf', kwargs)
    async def _probe_ssrf(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill._probe_ssrf', kwargs)
    async def _send_ssrf(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill._send_ssrf', kwargs)
    def _check_metadata_response(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill._check_metadata_response', kwargs)
    def _extract_aws_creds(self, *args, **kwargs):
        return _yaiwes_checkpoint('CloudMetadataSkill._extract_aws_creds', kwargs)
