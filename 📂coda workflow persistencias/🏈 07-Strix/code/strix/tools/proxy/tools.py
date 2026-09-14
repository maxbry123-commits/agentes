"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'b0d54b2ac8a652067de65cf90b4c9459b3917bad2f5517317ae0abd267532f2d'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

async def _ctx_client(*args, **kwargs):
    return _yaiwes_checkpoint('_ctx_client', kwargs)

async def _call(*args, **kwargs):
    return _yaiwes_checkpoint('_call', kwargs)

async def existing_request_ids(*args, **kwargs):
    return _yaiwes_checkpoint('existing_request_ids', kwargs)

def _to_tool_json(*args, **kwargs):
    return _yaiwes_checkpoint('_to_tool_json', kwargs)

def _no_client(*args, **kwargs):
    return _yaiwes_checkpoint('_no_client', kwargs)

def _err(*args, **kwargs):
    return _yaiwes_checkpoint('_err', kwargs)

async def list_requests(*args, **kwargs):
    return _yaiwes_checkpoint('list_requests', kwargs)

async def view_request(*args, **kwargs):
    return _yaiwes_checkpoint('view_request', kwargs)

def _format_search_hits(*args, **kwargs):
    return _yaiwes_checkpoint('_format_search_hits', kwargs)

def _format_text_page(*args, **kwargs):
    return _yaiwes_checkpoint('_format_text_page', kwargs)

async def repeat_request(*args, **kwargs):
    return _yaiwes_checkpoint('repeat_request', kwargs)

def _format_replay_tool_result(*args, **kwargs):
    return _yaiwes_checkpoint('_format_replay_tool_result', kwargs)

async def list_sitemap(*args, **kwargs):
    return _yaiwes_checkpoint('list_sitemap', kwargs)

async def view_sitemap_entry(*args, **kwargs):
    return _yaiwes_checkpoint('view_sitemap_entry', kwargs)

async def scope_rules(*args, **kwargs):
    return _yaiwes_checkpoint('scope_rules', kwargs)
