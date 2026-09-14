"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '8afd33dea249accd0ce7b3164589f7a718c91e5d50b907717047bb500f69ad5e'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def count_data_files(*args, **kwargs):
    return _yaiwes_checkpoint('count_data_files', kwargs)

def _as_data_dir(*args, **kwargs):
    return _yaiwes_checkpoint('_as_data_dir', kwargs)

def discover(*args, **kwargs):
    return _yaiwes_checkpoint('discover', kwargs)

def download_to_temp(*args, **kwargs):
    return _yaiwes_checkpoint('download_to_temp', kwargs)

def sync_data(*args, **kwargs):
    return _yaiwes_checkpoint('sync_data', kwargs)

def resolve_or_download(*args, **kwargs):
    return _yaiwes_checkpoint('resolve_or_download', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)

class AIGData:
    def fingerprints_dir(self, *args, **kwargs):
        return _yaiwes_checkpoint('AIGData.fingerprints_dir', kwargs)
    def vuln_dir(self, *args, **kwargs):
        return _yaiwes_checkpoint('AIGData.vuln_dir', kwargs)
    def vuln_en_dir(self, *args, **kwargs):
        return _yaiwes_checkpoint('AIGData.vuln_en_dir', kwargs)
    def eval_dir(self, *args, **kwargs):
        return _yaiwes_checkpoint('AIGData.eval_dir', kwargs)
    def mcp_dir(self, *args, **kwargs):
        return _yaiwes_checkpoint('AIGData.mcp_dir', kwargs)
    def to_dict(self, *args, **kwargs):
        return _yaiwes_checkpoint('AIGData.to_dict', kwargs)
