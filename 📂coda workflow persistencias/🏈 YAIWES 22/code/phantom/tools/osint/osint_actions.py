"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '238849e94da8315d21dd195325aefffb5b0f6eec1693572389a005ba75ba80c1'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _rate_limit(*args, **kwargs):
    return _yaiwes_checkpoint('_rate_limit', kwargs)

def _get_cache_key(*args, **kwargs):
    return _yaiwes_checkpoint('_get_cache_key', kwargs)

def _get_cached(*args, **kwargs):
    return _yaiwes_checkpoint('_get_cached', kwargs)

def _set_cached(*args, **kwargs):
    return _yaiwes_checkpoint('_set_cached', kwargs)

def _extract_domain(*args, **kwargs):
    return _yaiwes_checkpoint('_extract_domain', kwargs)

def _validate_domain(*args, **kwargs):
    return _yaiwes_checkpoint('_validate_domain', kwargs)

async def crtsh_search(*args, **kwargs):
    return _yaiwes_checkpoint('crtsh_search', kwargs)

async def shodan_search(*args, **kwargs):
    return _yaiwes_checkpoint('shodan_search', kwargs)

async def whois_lookup(*args, **kwargs):
    return _yaiwes_checkpoint('whois_lookup', kwargs)

async def dns_enum(*args, **kwargs):
    return _yaiwes_checkpoint('dns_enum', kwargs)

async def github_dork(*args, **kwargs):
    return _yaiwes_checkpoint('github_dork', kwargs)
