"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '26081063e31dd9f4531e2c0c2913445ac1b715cbd8e67a28c410e41de2da2258'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _normalize_url(*args, **kwargs):
    return _yaiwes_checkpoint('_normalize_url', kwargs)

def _is_interesting_status(*args, **kwargs):
    return _yaiwes_checkpoint('_is_interesting_status', kwargs)

def _categorize_finding(*args, **kwargs):
    return _yaiwes_checkpoint('_categorize_finding', kwargs)

def _generate_wordlist(*args, **kwargs):
    return _yaiwes_checkpoint('_generate_wordlist', kwargs)

async def _check_path(*args, **kwargs):
    return _yaiwes_checkpoint('_check_path', kwargs)

async def _get_baseline_response(*args, **kwargs):
    return _yaiwes_checkpoint('_get_baseline_response', kwargs)

async def bruteforce_directories(*args, **kwargs):
    return _yaiwes_checkpoint('bruteforce_directories', kwargs)

async def smart_path_gen(*args, **kwargs):
    return _yaiwes_checkpoint('smart_path_gen', kwargs)

async def recursive_dir_scan(*args, **kwargs):
    return _yaiwes_checkpoint('recursive_dir_scan', kwargs)

async def comprehensive_dir_enum(*args, **kwargs):
    return _yaiwes_checkpoint('comprehensive_dir_enum', kwargs)

class DirectoryResult:
    def to_dict(self, *args, **kwargs):
        return _yaiwes_checkpoint('DirectoryResult.to_dict', kwargs)

class ScanProgress:
    def percent(self, *args, **kwargs):
        return _yaiwes_checkpoint('ScanProgress.percent', kwargs)
    def elapsed(self, *args, **kwargs):
        return _yaiwes_checkpoint('ScanProgress.elapsed', kwargs)
    def rate(self, *args, **kwargs):
        return _yaiwes_checkpoint('ScanProgress.rate', kwargs)
